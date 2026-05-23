import subprocess
import tempfile
from pathlib import Path

from app.content_models import derive_song_key, validate_content_type
from app.content_scoring import validate_quality_score
from app.remediation_state import (
    DEFAULT_BACKUPS_DIR,
    DEFAULT_REMEDIATED_CONTENT_PATH,
    DEFAULT_REMEDIATION_AUDIT_PATH,
    build_remediated_content_record,
    create_backup_record,
    load_remediated_content,
    record_remediation_audit,
    save_remediated_content,
)


DEFAULT_REMEDIATION_THRESHOLD = 40
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


def run_bounded_remediation(
    artist,
    title,
    content_type,
    content,
    content_score,
    threshold=DEFAULT_REMEDIATION_THRESHOLD,
    workspace_root=".",
    remediated_content_path=DEFAULT_REMEDIATED_CONTENT_PATH,
    backups_dir=DEFAULT_BACKUPS_DIR,
    audit_path=DEFAULT_REMEDIATION_AUDIT_PATH,
    runner=subprocess.run,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_value = _require_text("content", content)
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
        record_remediation_audit(
            artist_value,
            title_value,
            content_type_value,
            backup_reference,
            evaluation["reason_code"],
            "refused",
            file_path=audit_path,
        )
        return {
            "status": "refused",
            "allowed": False,
            "manual_review_required": True,
            "reason_code": evaluation["reason_code"],
            "reason": evaluation["reason"],
            "signal_codes": evaluation["signal_codes"],
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
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: {}".format(exc),
                "failed",
                file_path=audit_path,
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "codex_exec_failed",
                "reason": str(exc),
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
                "backup_reference": backup_reference,
                "command": command,
                "prompt": prompt,
            }

        if not output_path.exists():
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: missing_output",
                "failed",
                file_path=audit_path,
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "missing_output",
                "reason": "codex exec did not write a remediation result",
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
                "backup_reference": backup_reference,
                "command": command,
                "prompt": prompt,
            }

        remediated_content = output_path.read_text(encoding="utf-8").strip()
        if remediated_content == "":
            record_remediation_audit(
                artist_value,
                title_value,
                content_type_value,
                backup_reference,
                "codex_exec_failed: empty_output",
                "failed",
                file_path=audit_path,
            )
            return {
                "status": "failed",
                "allowed": True,
                "manual_review_required": True,
                "reason_code": "empty_output",
                "reason": "codex exec produced an empty remediation result",
                "signal_codes": evaluation["signal_codes"],
                "approved_operations": evaluation["approved_operations"],
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

    return {
        "status": "success",
        "allowed": True,
        "manual_review_required": False,
        "reason_code": evaluation["reason_code"],
        "reason": evaluation["reason"],
        "signal_codes": evaluation["signal_codes"],
        "approved_operations": evaluation["approved_operations"],
        "backup_reference": backup_reference,
        "post_change_reference": post_change_reference,
        "remediated_content": remediated_content,
        "saved_state": saved_state,
        "command": command,
        "prompt": prompt,
    }
