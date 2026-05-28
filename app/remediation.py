import subprocess
import tempfile
from pathlib import Path

from app.content_models import derive_song_key, validate_content_type
from app.content_scoring import compose_content_score, validate_quality_score
from app.document_verification import (
    DEFAULT_DOCUMENT_QUALITY_PATH,
    evaluate_document_artifact,
    load_document_verification,
    save_document_verification,
)
from app.generation_filtering import evaluate_cached_content
from app.quality_assessment import assess_candidate_quality
from app.remediation_state import (
    DEFAULT_BACKUPS_DIR,
    DEFAULT_REMEDIATED_CONTENT_PATH,
    DEFAULT_REMEDIATION_AUDIT_PATH,
    build_remediated_content_record,
    create_backup_record,
    load_remediated_content,
    load_remediation_audit_records,
    record_remediation_audit,
    save_remediated_content,
)
from app.review_gate import compute_review_gate_decisions
from app.review_state import (
    DEFAULT_CONTENT_SCORES_PATH,
    DEFAULT_QUALITY_STATUS_PATH,
    DEFAULT_REVIEW_DECISIONS_PATH,
    load_content_scores,
    load_quality_status,
    load_review_decisions,
    save_content_scores,
    save_quality_status,
)


DEFAULT_REMEDIATION_THRESHOLD = 40
DEFAULT_REMEDIATION_RESOLUTION_THRESHOLD = 60
DEFAULT_REMEDIATION_RETRY_LIMIT = 2
ALLOWED_REMEDIATION_OPERATIONS = (
    "whitespace normalization",
    "section restructuring without semantic rewrite",
    "removal of obvious scraper residue",
    "normalization or removal of repeated junk blocks",
)
FORBIDDEN_REMEDIATION_OPERATIONS = (
    "semantic rewriting",
    "musical reinterpretation",
    "inventing or filling missing lyrics",
    "inventing or filling missing chords",
    "changing song meaning",
)
_ALLOWED_SIGNAL_OPERATIONS = {
    "duplicate_block": "normalization or removal of repeated junk blocks",
    "html_residue": "removal of obvious scraper residue",
    "email_header_artifacts": "removal of obvious scraper residue",
    "excessive_bracket_noise": "section restructuring without semantic rewrite",
    "print_hostile_content": "whitespace normalization",
}
_OUT_OF_SCOPE_SIGNALS = {
    "missing_lyrics",
    "missing_chords",
    "unusable_lyrics",
    "unusable_chords",
    "low_confidence_match",
}


def _require_text(field_name, value):
    if not isinstance(value, str) or value == "":
        raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
    return value


def _normalized_workspace_root(workspace_root):
    return Path(workspace_root).resolve()


def _extract_signal_codes(score_reasons):
    signal_codes = []
    for reason in score_reasons or []:
        if isinstance(reason, str) and reason.startswith("signal:"):
            signal_codes.append(reason.split(":", 1)[1])
    return signal_codes


def evaluate_remediation_candidate(content_score, threshold=DEFAULT_REMEDIATION_THRESHOLD):
    if not isinstance(content_score, dict):
        raise ValueError("content_score must be a dictionary; got {!r}".format(content_score))

    quality_score = validate_quality_score(content_score.get("quality_score"))
    score_reasons = content_score.get("score_reasons") or []
    signal_codes = _extract_signal_codes(score_reasons)

    if quality_score >= threshold:
        return {
            "allowed": False,
            "status": "refused",
            "reason_code": "above_threshold",
            "reason": "candidate score is not below the remediation threshold",
            "signal_codes": signal_codes,
            "approved_operations": [],
        }

    if not signal_codes:
        return {
            "allowed": False,
            "status": "refused",
            "reason_code": "no_supported_issue_signals",
            "reason": "candidate lacks machine-readable issue signals for bounded cleanup",
            "signal_codes": signal_codes,
            "approved_operations": [],
        }

    blocked_signal_codes = [code for code in signal_codes if code in _OUT_OF_SCOPE_SIGNALS]
    if blocked_signal_codes:
        return {
            "allowed": False,
            "status": "refused",
            "reason_code": "out_of_scope_signal",
            "reason": "candidate requires semantic rewrite or manual review",
            "signal_codes": signal_codes,
            "blocked_signal_codes": blocked_signal_codes,
            "approved_operations": [],
        }

    unsupported_signal_codes = [
        code for code in signal_codes if code not in _ALLOWED_SIGNAL_OPERATIONS
    ]
    if unsupported_signal_codes:
        return {
            "allowed": False,
            "status": "refused",
            "reason_code": "unsupported_signal",
            "reason": "candidate contains issue signals outside the v1 bounded cleanup allowlist",
            "signal_codes": signal_codes,
            "blocked_signal_codes": unsupported_signal_codes,
            "approved_operations": [],
        }

    approved_operations = []
    for code in signal_codes:
        operation = _ALLOWED_SIGNAL_OPERATIONS[code]
        if operation not in approved_operations:
            approved_operations.append(operation)

    return {
        "allowed": True,
        "status": "allowed",
        "reason_code": "allowed_scope",
        "reason": "candidate falls within the bounded remediation allowlist",
        "signal_codes": signal_codes,
        "approved_operations": approved_operations,
    }


def build_bounded_remediation_prompt(artist, title, content_type, content, evaluation):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_value = _require_text("content", content)
    if not isinstance(evaluation, dict) or not evaluation.get("allowed"):
        raise ValueError("evaluation must be an allowed remediation decision")

    allowed_operations = "\n".join(
        "- {}".format(operation) for operation in evaluation["approved_operations"]
    )
    forbidden_operations = "\n".join(
        "- {}".format(operation) for operation in FORBIDDEN_REMEDIATION_OPERATIONS
    )
    signal_codes = ", ".join(evaluation["signal_codes"])

    return """You are cleaning a song {content_type} artifact.

Song:
- Artist: {artist}
- Title: {title}
- Content type: {content_type}
- Triggering issue signals: {signals}

Allowed operations for this candidate:
{allowed_operations}

Hard constraints:
{forbidden_operations}
- Return only the cleaned {content_type} text with no commentary, no markdown fences, and no explanations.
- Preserve the same song, ordering, and meaning.
- If the content cannot be safely improved within the allowed scope, return the original text unchanged.

Original content:
<<<CONTENT
{content}
CONTENT""".format(
        artist=artist_value,
        title=title_value,
        content_type=content_type_value,
        signals=signal_codes,
        allowed_operations=allowed_operations,
        forbidden_operations=forbidden_operations,
        content=content_value,
    )


def build_codex_exec_command(output_path, workspace_root):
    return [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "-C",
        str(_normalized_workspace_root(workspace_root)),
        "-o",
        str(output_path),
        "-",
    ]


def _post_change_reference(remediated_content_path, song_key, content_type):
    return "{}#{}:{}".format(remediated_content_path, song_key, content_type)


def _escalation_details(category, reason, extra_details=None):
    details = {
        "escalation_category": category,
        "escalation_reason": reason,
    }
    if isinstance(extra_details, dict):
        details.update(extra_details)
    return details


def _merge_remediated_record(existing_state, remediated_record):
    records = []
    seen_key = (remediated_record["song_key"], remediated_record["content_type"])

    for song_entries in existing_state.get("entries", {}).values():
        for existing_record in song_entries.values():
            existing_key = (existing_record.get("song_key"), existing_record.get("content_type"))
            if existing_key == seen_key:
                continue
            records.append(existing_record)

    records.append(remediated_record)
    return records


def _flatten_state_records(state):
    records = []
    for entry_group in state.get("entries", {}).values():
        if not isinstance(entry_group, dict):
            continue
        for record in entry_group.values():
            if isinstance(record, dict):
                records.append(record)
    return records


def _merge_record(existing_state, record, key_fields):
    records = []
    record_key = tuple(record.get(field) for field in key_fields)

    for existing_record in _flatten_state_records(existing_state):
        existing_key = tuple(existing_record.get(field) for field in key_fields)
        if existing_key == record_key:
            continue
        records.append(existing_record)

    records.append(record)
    return records


def _merge_document_verification_record(existing_state, record):
    records = []
    artifact_path = record.get("artifact_path")

    for existing_record in _flatten_state_records(existing_state):
        if existing_record.get("artifact_path") == artifact_path:
            continue
        records.append(existing_record)

    records.append(record)
    return records


def _document_verification_summary(records):
    summary = []
    for record in records:
        summary.append(
            {
                "artifact_path": record.get("artifact_path"),
                "artifact_type": record.get("artifact_type"),
                "verification_status": record.get("verification_status"),
                "verification_reasons": list(record.get("verification_reasons", [])),
            }
        )
    return summary


def count_remediation_attempts(
    artist,
    title,
    content_type,
    audit_path=DEFAULT_REMEDIATION_AUDIT_PATH,
):
    song_key = derive_song_key(artist, title)
    content_type_value = validate_content_type(content_type)
    records, _ = load_remediation_audit_records(audit_path)

    return sum(
        1
        for record in records
        if record.get("song_key") == song_key
        and record.get("content_type") == content_type_value
        and record.get("outcome") == "attempted"
    )


def reevaluate_remediated_content(
    artist,
    title,
    content_type,
    remediated_content,
    backup_reference,
    previous_content_score=None,
    resolution_threshold=DEFAULT_REMEDIATION_RESOLUTION_THRESHOLD,
    remediated_content_path=DEFAULT_REMEDIATED_CONTENT_PATH,
    quality_status_path=DEFAULT_QUALITY_STATUS_PATH,
    content_scores_path=DEFAULT_CONTENT_SCORES_PATH,
    review_decisions_path=DEFAULT_REVIEW_DECISIONS_PATH,
    document_quality_path=DEFAULT_DOCUMENT_QUALITY_PATH,
    artifact_paths=None,
    audit_path=DEFAULT_REMEDIATION_AUDIT_PATH,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    remediated_content_value = _require_text("content", remediated_content)

    song_key = derive_song_key(artist_value, title_value)
    quality_assessment = assess_candidate_quality(
        {
            "artist": artist_value,
            "title": title_value,
            "content_type": content_type_value,
            "content": remediated_content_value,
        }
    )
    quality_status_record = {
        "artist": artist_value,
        "title": title_value,
        "song_key": song_key,
        "content_type": content_type_value,
        "content_hash": previous_content_score.get("content_hash")
        if isinstance(previous_content_score, dict)
        else None,
        "quality": quality_assessment["quality"],
        "signals": quality_assessment["signals"],
    }
    quality_status_record["content_hash"] = evaluate_cached_content(
        artist_value,
        title_value,
        content_type_value,
        remediated_content_value,
    )["content_hash"]
    quality_status_state, _ = load_quality_status(quality_status_path)
    saved_quality_state = save_quality_status(
        quality_status_path,
        _merge_record(
            quality_status_state,
            quality_status_record,
            ("song_key", "content_type"),
        ),
    )

    rescored_quality_status = saved_quality_state["entries"][
        song_key
    ][content_type_value]
    content_score_record = compose_content_score(rescored_quality_status)
    content_scores_state, _ = load_content_scores(content_scores_path)
    saved_content_scores_state = save_content_scores(
        content_scores_path,
        _merge_record(
            content_scores_state,
            content_score_record,
            ("song_key", "content_type"),
        ),
    )

    review_decisions_state, _ = load_review_decisions(review_decisions_path)
    current_review_decision = (
        review_decisions_state.get("entries", {})
        .get(song_key, {})
        .get(content_type_value)
    )
    current_review_result = evaluate_cached_content(
        artist_value,
        title_value,
        content_type_value,
        remediated_content_value,
        quality_status_record=rescored_quality_status,
        review_decision_record=current_review_decision,
    )

    refreshed_verification_records = []
    missing_artifact_paths = []
    if artifact_paths:
        document_verification_state, _ = load_document_verification(document_quality_path)
        merged_records = _flatten_state_records(document_verification_state)

        for artifact_path in artifact_paths:
            path = Path(artifact_path)
            if not path.exists():
                missing_artifact_paths.append(str(path))
                continue
            refreshed_record = evaluate_document_artifact(path)
            refreshed_verification_records.append(refreshed_record)
            merged_records = _merge_document_verification_record(
                {"entries": {str(index): {"record": record} for index, record in enumerate(merged_records)}},
                refreshed_record,
            )

        if refreshed_verification_records:
            save_document_verification(document_quality_path, merged_records)

    review_gate_decisions = compute_review_gate_decisions(refreshed_verification_records)

    previous_quality_score = None
    previous_content_hash = None
    if isinstance(previous_content_score, dict):
        previous_quality_score = previous_content_score.get("quality_score")
        previous_content_hash = previous_content_score.get("content_hash")

    current_quality_score = content_score_record["quality_score"]
    score_improved = (
        isinstance(previous_quality_score, int) and current_quality_score > previous_quality_score
    )
    if artifact_paths:
        verification_passed = (not missing_artifact_paths) and all(
            record.get("verification_status") == "passed"
            for record in refreshed_verification_records
        )
    else:
        verification_passed = True

    evaluation_outcome = (
        "resolved"
        if current_quality_score >= resolution_threshold and verification_passed
        else "unresolved"
    )
    unresolved_reasons = []
    if current_quality_score < resolution_threshold:
        unresolved_reasons.append("still_below_threshold")
    if not verification_passed:
        unresolved_reasons.append("verification_failed")
    escalation_category = None
    escalation_reason = None
    if evaluation_outcome == "unresolved":
        if "still_below_threshold" in unresolved_reasons:
            escalation_category = "still_below_threshold"
            escalation_reason = "post-remediation quality score remains below the resolution threshold"
        elif "verification_failed" in unresolved_reasons:
            escalation_category = "verification_failed"
            escalation_reason = "artifact verification still fails after remediation"

    post_change_reference = _post_change_reference(
        remediated_content_path,
        song_key,
        content_type_value,
    )
    details = {
        "resolution_threshold": resolution_threshold,
        "before_content_hash": previous_content_hash,
        "after_content_hash": content_score_record["content_hash"],
        "before_quality_score": previous_quality_score,
        "after_quality_score": current_quality_score,
        "score_improved": score_improved,
        "review_result": {
            "quality": current_review_result.get("quality"),
            "included": current_review_result.get("included"),
            "decision_source": current_review_result.get("decision_source"),
            "reason": current_review_result.get("reason"),
        },
        "document_verification": _document_verification_summary(refreshed_verification_records),
        "review_gate_decisions": review_gate_decisions,
        "unresolved_reasons": unresolved_reasons,
    }
    if missing_artifact_paths:
        details["missing_artifact_paths"] = missing_artifact_paths
    if escalation_category is not None:
        details["escalation_category"] = escalation_category
        details["escalation_reason"] = escalation_reason
    record_remediation_audit(
        artist_value,
        title_value,
        content_type_value,
        backup_reference,
        "post_remediation_re_evaluation",
        evaluation_outcome,
        post_change_reference=post_change_reference,
        file_path=audit_path,
        details=details,
    )

    return {
        "status": evaluation_outcome,
        "quality_status": rescored_quality_status,
        "content_score": content_score_record,
        "score_improved": score_improved,
        "unresolved_reasons": unresolved_reasons,
        "escalation_category": escalation_category,
        "escalation_reason": escalation_reason,
        "review_result": current_review_result,
        "document_verification": refreshed_verification_records,
        "review_gate_decisions": review_gate_decisions,
        "saved_quality_state": saved_quality_state,
        "saved_content_scores_state": saved_content_scores_state,
    }


def run_bounded_remediation(
    artist,
    title,
    content_type,
    content,
    content_score,
    threshold=DEFAULT_REMEDIATION_THRESHOLD,
    resolution_threshold=DEFAULT_REMEDIATION_RESOLUTION_THRESHOLD,
    retry_limit=DEFAULT_REMEDIATION_RETRY_LIMIT,
    workspace_root=".",
    remediated_content_path=DEFAULT_REMEDIATED_CONTENT_PATH,
    backups_dir=DEFAULT_BACKUPS_DIR,
    audit_path=DEFAULT_REMEDIATION_AUDIT_PATH,
    quality_status_path=DEFAULT_QUALITY_STATUS_PATH,
    content_scores_path=DEFAULT_CONTENT_SCORES_PATH,
    review_decisions_path=DEFAULT_REVIEW_DECISIONS_PATH,
    document_quality_path=DEFAULT_DOCUMENT_QUALITY_PATH,
    artifact_paths=None,
    runner=subprocess.run,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_value = _require_text("content", content)
    song_key = derive_song_key(artist_value, title_value)
    existing_attempt_count = count_remediation_attempts(
        artist_value,
        title_value,
        content_type_value,
        audit_path=audit_path,
    )
    if existing_attempt_count >= retry_limit:
        escalation_reason = "automatic remediation retry limit reached"
        pre_change_reference = _post_change_reference(
            remediated_content_path,
            song_key,
            content_type_value,
        )
        record_remediation_audit(
            artist_value,
            title_value,
            content_type_value,
            pre_change_reference,
            "retry_limit_reached",
            "refused",
            file_path=audit_path,
            details=_escalation_details(
                "retry_limit_reached",
                escalation_reason,
                {
                    "retry_limit": retry_limit,
                    "attempt_count": existing_attempt_count,
                },
            ),
        )
        return {
            "status": "refused",
            "allowed": False,
            "manual_review_required": True,
            "reason_code": "retry_limit_reached",
            "reason": escalation_reason,
            "signal_codes": [],
            "escalation_category": "retry_limit_reached",
            "escalation_reason": escalation_reason,
            "attempt_count": existing_attempt_count,
            "retry_limit": retry_limit,
            "backup_reference": None,
        }
    evaluation = evaluate_remediation_candidate(content_score, threshold=threshold)
    backup_record = create_backup_record(
        artist_value,
        title_value,
        content_type_value,
        content_value,
        backups_dir=backups_dir,
    )
    backup_reference = backup_record["backup_path"]

    if not evaluation["allowed"]:
        escalation_reason = evaluation["reason"]
        record_remediation_audit(
            artist_value,
            title_value,
            content_type_value,
            backup_reference,
            evaluation["reason_code"],
            "refused",
            file_path=audit_path,
            details=_escalation_details(
                "not_allowed_to_fix",
                escalation_reason,
                {
                    "signal_codes": evaluation["signal_codes"],
                },
            ),
        )
        return {
            "status": "refused",
            "allowed": False,
            "manual_review_required": True,
            "reason_code": evaluation["reason_code"],
            "reason": evaluation["reason"],
            "signal_codes": evaluation["signal_codes"],
            "escalation_category": "not_allowed_to_fix",
            "escalation_reason": escalation_reason,
            "backup_reference": backup_reference,
        }

    record_remediation_audit(
        artist_value,
        title_value,
        content_type_value,
        backup_reference,
        evaluation["reason_code"],
        "allowed",
        file_path=audit_path,
    )
    record_remediation_audit(
        artist_value,
        title_value,
        content_type_value,
        backup_reference,
        evaluation["reason_code"],
        "attempted",
        file_path=audit_path,
    )

    prompt = build_bounded_remediation_prompt(
        artist_value,
        title_value,
        content_type_value,
        content_value,
        evaluation,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "codex-remediation-output.txt"
        command = build_codex_exec_command(output_path, workspace_root)

        try:
            runner(command, input=prompt, check=True, capture_output=True, text=True)
        except Exception as exc:
            escalation_reason = str(exc)
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: {}".format(exc),
                "failed",
                file_path=audit_path,
                details=_escalation_details(
                    "remediation_failed",
                    escalation_reason,
                ),
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "codex_exec_failed",
                "reason": str(exc),
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
                "escalation_category": "remediation_failed",
                "escalation_reason": escalation_reason,
                "backup_reference": backup_reference,
                "command": command,
                "prompt": prompt,
            }

        if not output_path.exists():
            escalation_reason = "codex exec did not write a remediation result"
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: missing_output",
                "failed",
                file_path=audit_path,
                details=_escalation_details(
                    "remediation_failed",
                    escalation_reason,
                ),
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "missing_output",
                "reason": escalation_reason,
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
                "escalation_category": "remediation_failed",
                "escalation_reason": escalation_reason,
                "backup_reference": backup_reference,
                "command": command,
                "prompt": prompt,
            }

        remediated_content = output_path.read_text(encoding="utf-8").strip()
        if remediated_content == "":
            escalation_reason = "codex exec produced an empty remediation result"
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: empty_output",
                "failed",
                file_path=audit_path,
                details=_escalation_details(
                    "remediation_failed",
                    escalation_reason,
                ),
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "empty_output",
                "reason": escalation_reason,
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
                "escalation_category": "remediation_failed",
                "escalation_reason": escalation_reason,
                "backup_reference": backup_reference,
                "command": command,
                "prompt": prompt,
            }

    remediated_content_state, _ = load_remediated_content(remediated_content_path)
    remediated_record = build_remediated_content_record(
        artist_value,
        title_value,
        content_type_value,
        remediated_content,
        backup_reference,
    )
    saved_state = save_remediated_content(
        remediated_content_path,
        _merge_remediated_record(remediated_content_state, remediated_record),
    )
    song_key = derive_song_key(artist_value, title_value)
    post_change_reference = _post_change_reference(
        remediated_content_path,
        song_key,
        content_type_value,
    )
    record_remediation_audit(
        artist_value,
        title_value,
        content_type_value,
        backup_reference,
        evaluation["reason_code"],
        "success",
        post_change_reference=post_change_reference,
        file_path=audit_path,
    )
    post_remediation_evaluation = reevaluate_remediated_content(
        artist_value,
        title_value,
        content_type_value,
        remediated_content,
        backup_reference,
        previous_content_score=content_score,
        resolution_threshold=resolution_threshold,
        quality_status_path=quality_status_path,
        content_scores_path=content_scores_path,
        review_decisions_path=review_decisions_path,
        document_quality_path=document_quality_path,
        artifact_paths=artifact_paths,
        audit_path=audit_path,
    )

    return {
        "status": "success",
        "allowed": True,
        "manual_review_required": post_remediation_evaluation["status"] != "resolved",
        "reason_code": evaluation["reason_code"],
        "reason": evaluation["reason"],
        "signal_codes": evaluation["signal_codes"],
        "approved_operations": evaluation["approved_operations"],
        "backup_reference": backup_reference,
        "post_change_reference": post_change_reference,
        "remediated_content": remediated_content,
        "saved_state": saved_state,
        "post_remediation_evaluation": post_remediation_evaluation,
        "escalation_category": post_remediation_evaluation["escalation_category"],
        "escalation_reason": post_remediation_evaluation["escalation_reason"],
        "command": command,
        "prompt": prompt,
    }
