import copy
import json
import logging
import math
import re
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)

DEFAULT_REPORTS_PATH = Path("data/review/reports")
SENSITIVE_KEY_PATTERN = re.compile(
    r"(access[_-]?token|api[_-]?token|client[_-]?secret|client[_-]?access[_-]?token|"
    r"private[_-]?key|password|secret|token)",
    re.IGNORECASE,
)


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _sanitize_key(key):
    if not isinstance(key, str):
        return key
    if SENSITIVE_KEY_PATTERN.search(key):
        return None
    return key


def _sanitize_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, dict):
        sanitized = {}
        for key, nested_value in value.items():
            sanitized_key = _sanitize_key(key)
            if sanitized_key is None:
                continue
            sanitized[sanitized_key] = _sanitize_value(nested_value)
        return sanitized

    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]

    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]

    return copy.deepcopy(value)


def _normalize_missing_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _safe_filename_component(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "report"


def _group_source_attempts(source_attempts):
    grouped = {}

    for attempt in source_attempts or []:
        if not isinstance(attempt, dict):
            continue

        song_key = attempt.get("song_key")
        content_type = attempt.get("content_type")
        if not song_key or not content_type:
            continue

        grouped.setdefault(song_key, {}).setdefault(content_type, []).append(
            {
                "artist": attempt.get("artist"),
                "title": attempt.get("title"),
                "song_key": song_key,
                "content_type": content_type,
                "source": attempt.get("source"),
                "status": attempt.get("status"),
                "error": attempt.get("error"),
                "retrieved_at": attempt.get("retrieved_at"),
            }
        )

    return grouped


def _build_song_entry(result, source_attempts_by_song):
    song_key = result.get("song_key")
    content_type = result.get("content_type")
    song_attempts = []

    if song_key in source_attempts_by_song:
        song_attempts = copy.deepcopy(source_attempts_by_song[song_key].get(content_type, []))

    return {
        "artist": result.get("artist"),
        "title": result.get("title"),
        "song_key": song_key,
        "content_type": content_type,
        "content_hash": result.get("content_hash"),
        "quality": result.get("quality"),
        "included": result.get("included"),
        "decision_source": result.get("decision_source"),
        "reason": result.get("reason"),
        "signals": copy.deepcopy(result.get("signals", [])),
        "quality_status": copy.deepcopy(result.get("quality_status")),
        "review_decision": copy.deepcopy(result.get("review_decision")),
        "source_attempts": song_attempts,
    }


def _build_summary_entry(result):
    entry = {
        "song_key": result.get("song_key"),
        "content_type": result.get("content_type"),
        "quality": result.get("quality"),
        "included": result.get("included"),
        "reason": result.get("reason"),
    }

    signals = result.get("signals") or []
    if signals:
        entry["top_signal"] = copy.deepcopy(signals[0])

    return entry


def _build_invalid_input_entry(record):
    entry = {
        "row_number": record.get("row_number"),
        "raw_artist": _normalize_missing_value(record.get("raw_artist")),
        "raw_title": _normalize_missing_value(record.get("raw_title")),
        "reason": record.get("reason"),
    }

    if "skip" in record:
        entry["skip"] = _normalize_missing_value(record.get("skip"))

    return entry


def _build_selection_issue_entry(record):
    entry = {
        "selection_name": record.get("selection_name"),
        "issue_type": record.get("issue_type"),
        "artist": record.get("artist"),
        "title": record.get("title"),
        "song_key": record.get("song_key"),
        "content_type": record.get("content_type"),
        "reason": record.get("reason"),
    }

    if "file_path" in record:
        entry["file_path"] = record.get("file_path")

    if "field" in record:
        entry["field"] = record.get("field")

    return entry


def _artifact_key(record):
    return (
        record.get("artifact_path"),
        record.get("artifact_type"),
    )


def _build_manual_review_gate(document_verification_rows, review_gate_rows):
    verification_by_artifact = {
        _artifact_key(record): record
        for record in document_verification_rows
        if record.get("artifact_path") and record.get("artifact_type")
    }

    ready_artifacts = []
    blocked_artifacts = []
    for decision in review_gate_rows:
        verification_record = verification_by_artifact.get(_artifact_key(decision), {})
        gate_entry = {
            "artifact_path": decision.get("artifact_path"),
            "artifact_type": decision.get("artifact_type"),
            "review_ready": decision.get("review_ready"),
            "blocked_from_manual_review": decision.get("review_ready") is False,
            "blocking_stage": (
                "document_verification" if decision.get("review_ready") is False else None
            ),
            "failure_reasons": copy.deepcopy(decision.get("failure_reasons", [])),
            "computed_at": decision.get("computed_at"),
            "verification_status": verification_record.get("verification_status"),
            "verification_reasons": copy.deepcopy(
                verification_record.get("verification_reasons", [])
            ),
            "verified_at": verification_record.get("verified_at"),
        }
        if gate_entry["blocked_from_manual_review"]:
            blocked_artifacts.append(gate_entry)
        else:
            ready_artifacts.append(gate_entry)

    return {
        "ready_count": len(ready_artifacts),
        "blocked_count": len(blocked_artifacts),
        "ready_artifacts": ready_artifacts,
        "blocked_artifacts": blocked_artifacts,
    }


def build_traceable_quality_report(
    generation_results,
    source="generate_from_cache",
    report_type="quality_run",
    source_attempts=None,
    generated_at=None,
    invalid_song_rows=None,
    selection_issues=None,
    pdf_outputs=None,
    pdf_errors=None,
    document_verification=None,
    review_gate_decisions=None,
):
    generated_at_value = generated_at or _now_iso()
    source_attempts_by_song = _group_source_attempts(source_attempts)
    songs = [
        _build_song_entry(result, source_attempts_by_song)
        for result in generation_results or []
    ]
    invalid_input_rows = [
        _build_invalid_input_entry(record)
        for record in invalid_song_rows or []
        if isinstance(record, dict)
    ]
    selection_issue_rows = [
        _build_selection_issue_entry(record)
        for record in selection_issues or []
        if isinstance(record, dict)
    ]
    pdf_output_rows = [str(path) for path in pdf_outputs or [] if path]
    pdf_error_rows = [
        {
            "source": record.get("source"),
            "target": record.get("target"),
            "reason": record.get("reason"),
        }
        for record in pdf_errors or []
        if isinstance(record, dict)
    ]
    document_verification_rows = [
        copy.deepcopy(record)
        for record in document_verification or []
        if isinstance(record, dict)
    ]
    review_gate_rows = [
        copy.deepcopy(record)
        for record in review_gate_decisions or []
        if isinstance(record, dict)
    ]
    manual_review_gate = _build_manual_review_gate(
        document_verification_rows,
        review_gate_rows,
    )
    clean_songs = [
        _build_summary_entry(song)
        for song in songs
        if song.get("quality") == "clean"
    ]
    excluded_clean_songs = [
        _build_summary_entry(song)
        for song in songs
        if song.get("quality") == "clean" and not song.get("included")
    ]
    questionable_songs = [
        _build_summary_entry(song)
        for song in songs
        if song.get("quality") == "questionable"
    ]
    missing_songs = [
        _build_summary_entry(song)
        for song in songs
        if song.get("quality") == "missing"
    ]

    summary = {
        "included_count": sum(1 for song in songs if song.get("included")),
        "excluded_count": sum(
            1
            for song in songs
            if not song.get("included") and song.get("quality") != "missing"
        ),
        "missing_count": sum(1 for song in songs if song.get("quality") == "missing"),
        "questionable_count": sum(1 for song in songs if song.get("quality") == "questionable"),
        "overridden_count": sum(
            1
            for song in songs
            if isinstance(song.get("review_decision"), dict)
            and song["review_decision"].get("decision") == "override"
        ),
        "clean_count": len(clean_songs),
        "excluded_clean_count": len(excluded_clean_songs),
        "invalid_input_count": len(invalid_input_rows),
        "selection_issue_count": len(selection_issue_rows),
        "pdf_output_count": len(pdf_output_rows),
        "pdf_error_count": len(pdf_error_rows),
        "review_ready_count": sum(
            1 for decision in review_gate_rows if decision.get("review_ready") is True
        ),
        "not_review_ready_count": sum(
            1 for decision in review_gate_rows if decision.get("review_ready") is False
        ),
        "manual_review_ready_count": manual_review_gate["ready_count"],
        "manual_review_blocked_count": manual_review_gate["blocked_count"],
        "counts": {
            "clean": len(clean_songs),
            "excluded_clean": len(excluded_clean_songs),
            "questionable": len(questionable_songs),
            "missing": len(missing_songs),
            "invalid_input": len(invalid_input_rows),
            "selection_issue": len(selection_issue_rows),
            "pdf_output": len(pdf_output_rows),
            "pdf_error": len(pdf_error_rows),
            "review_ready": sum(
                1 for decision in review_gate_rows if decision.get("review_ready") is True
            ),
            "not_review_ready": sum(
                1 for decision in review_gate_rows if decision.get("review_ready") is False
            ),
            "manual_review_ready": manual_review_gate["ready_count"],
            "manual_review_blocked": manual_review_gate["blocked_count"],
        },
        "clean_songs": clean_songs,
        "excluded_clean_songs": excluded_clean_songs,
        "questionable_songs": questionable_songs,
        "missing_songs": missing_songs,
        "invalid_input_rows": invalid_input_rows,
        "selection_issues": selection_issue_rows,
        "pdf_outputs": pdf_output_rows,
        "pdf_errors": pdf_error_rows,
        "document_verification": document_verification_rows,
        "review_gate_decisions": review_gate_rows,
        "manual_review_gate": manual_review_gate,
    }

    report = {
        "generated_at": generated_at_value,
        "report_type": report_type,
        "source": source,
        "summary": summary,
        "songs": songs,
        "selection_issues": selection_issue_rows,
        "pdf_outputs": pdf_output_rows,
        "pdf_errors": pdf_error_rows,
        "document_verification": document_verification_rows,
        "review_gate_decisions": review_gate_rows,
        "manual_review_gate": manual_review_gate,
    }

    return _sanitize_value(report)


def write_traceable_quality_report(report, output_dir=DEFAULT_REPORTS_PATH):
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    generated_at = report.get("generated_at") or _now_iso()
    report_type = _safe_filename_component(str(report.get("report_type", "report")))
    source = _safe_filename_component(str(report.get("source", "source")))
    timestamp = re.sub(r"[^0-9T+-]", "", generated_at.replace(":", "").replace("-", ""))
    if timestamp == "":
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%z")

    target_path = target_dir / "{}-{}-{}.json".format(report_type, source, timestamp)

    sanitized_report = _sanitize_value(report)
    with target_path.open("w", encoding="utf-8") as handle:
        json.dump(sanitized_report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Traceability report written to %s", target_path)
    return target_path


def summarize_traceable_quality_report(report, report_path):
    summary = report.get("summary", {})
    counts = summary.get("counts", {})
    return (
        "Quality report written to {} "
        "(clean {}, questionable {}, missing {}, invalid input {}; "
        "selection issues {}; included {}, excluded {}, overridden {})."
    ).format(
        report_path,
        counts.get("clean", summary.get("clean_count", 0)),
        counts.get("questionable", summary.get("questionable_count", 0)),
        counts.get("missing", summary.get("missing_count", 0)),
        counts.get("invalid_input", summary.get("invalid_input_count", 0)),
        counts.get("selection_issue", summary.get("selection_issue_count", 0)),
        summary.get("included_count", 0),
        summary.get("excluded_count", 0),
        summary.get("overridden_count", 0),
    )
