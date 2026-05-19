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


def build_traceable_quality_report(
    generation_results,
    source="generate_from_cache",
    report_type="quality_run",
    source_attempts=None,
    generated_at=None,
    invalid_song_rows=None,
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
        "counts": {
            "clean": len(clean_songs),
            "excluded_clean": len(excluded_clean_songs),
            "questionable": len(questionable_songs),
            "missing": len(missing_songs),
            "invalid_input": len(invalid_input_rows),
        },
        "clean_songs": clean_songs,
        "excluded_clean_songs": excluded_clean_songs,
        "questionable_songs": questionable_songs,
        "missing_songs": missing_songs,
        "invalid_input_rows": invalid_input_rows,
    }

    report = {
        "generated_at": generated_at_value,
        "report_type": report_type,
        "source": source,
        "summary": summary,
        "songs": songs,
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
        "included {}, excluded {}, overridden {})."
    ).format(
        report_path,
        counts.get("clean", summary.get("clean_count", 0)),
        counts.get("questionable", summary.get("questionable_count", 0)),
        counts.get("missing", summary.get("missing_count", 0)),
        counts.get("invalid_input", summary.get("invalid_input_count", 0)),
        summary.get("included_count", 0),
        summary.get("excluded_count", 0),
        summary.get("overridden_count", 0),
    )
