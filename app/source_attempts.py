import json
import logging
from pathlib import Path

from app.content_models import build_source_attempt_record


logger = logging.getLogger(__name__)

DEFAULT_SOURCE_ATTEMPTS_PATH = Path("data/review/source_attempts.jsonl")


def _validation_error(file_path, field, reason):
    return {
        "file_path": str(file_path),
        "field": field,
        "reason": reason,
    }


def append_source_attempt_record(file_path, source_attempt):
    target_path = Path(file_path)

    try:
        if not isinstance(source_attempt, dict):
            raise ValueError("source attempt records must be dictionaries; got {!r}".format(source_attempt))

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(source_attempt, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.error("Error writing source attempt file %s: %s", target_path, exc)
        return False


def record_source_attempt(
    artist,
    title,
    content_type,
    source,
    status,
    error=None,
    retrieved_at=None,
    file_path=DEFAULT_SOURCE_ATTEMPTS_PATH,
):
    source_attempt = build_source_attempt_record(
        artist,
        title,
        content_type,
        source,
        status,
        error=error,
        retrieved_at=retrieved_at,
    )
    return append_source_attempt_record(file_path, source_attempt)


def load_source_attempts(file_path=DEFAULT_SOURCE_ATTEMPTS_PATH):
    target_path = Path(file_path)
    records = []
    errors = []

    if not target_path.exists():
        return records, errors

    try:
        with target_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        _validation_error(
                            target_path,
                            "[line {}]".format(line_number),
                            "Invalid JSON in source attempt file: {}".format(exc),
                        )
                    )
                    continue

                if not isinstance(record, dict):
                    errors.append(
                        _validation_error(
                            target_path,
                            "[line {}]".format(line_number),
                            "Source attempt entries must be dictionaries; got {!r}".format(record),
                        )
                    )
                    continue

                records.append(record)
    except OSError as exc:
        errors.append(
            _validation_error(
                target_path,
                "$",
                "Failed to read source attempt file: {}".format(exc),
            )
        )
        logger.error("Error reading source attempt file %s: %s", target_path, exc)

    return records, errors
