import json
import logging
import re
from datetime import datetime
from pathlib import Path

from app.content_models import (
    compute_content_hash,
    derive_song_key,
    validate_content_type,
)


logger = logging.getLogger(__name__)

REMEDIATED_CONTENT_VERSION = 1
REMEDIATION_OUTCOMES = (
    "allowed",
    "attempted",
    "refused",
    "success",
    "failed",
    "resolved",
    "unresolved",
)
DEFAULT_REMEDIATED_CONTENT_PATH = Path("data/review/remediated_content.json")
DEFAULT_BACKUPS_DIR = Path("data/review/backups")
DEFAULT_REMEDIATION_AUDIT_PATH = Path("data/review/audit/remediation_attempts.jsonl")


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _require_text(field_name, value):
    if not isinstance(value, str) or value == "":
        raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
    return value


def _validation_error(file_path, field, reason):
    return {
        "file_path": str(file_path),
        "field": field,
        "reason": reason,
    }


def _load_json_document(file_path):
    if not file_path.exists():
        return None, []

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle), []
    except json.JSONDecodeError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Invalid JSON in remediated content file: {}".format(exc),
            )
        ]
    except OSError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Failed to read remediated content file: {}".format(exc),
            )
        ]


def _empty_remediated_content_state(updated_at=None):
    return {
        "version": REMEDIATED_CONTENT_VERSION,
        "updated_at": updated_at,
        "entries": {},
    }


def _safe_path_component(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "item"


def validate_remediation_outcome(outcome):
    if outcome not in REMEDIATION_OUTCOMES:
        raise ValueError(
            "outcome must be one of {}; got {!r}".format(
                ", ".join(repr(item) for item in REMEDIATION_OUTCOMES),
                outcome,
            )
        )
    return outcome


def build_remediated_content_record(
    artist,
    title,
    content_type,
    content,
    backup_reference,
    updated_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_value = _require_text("content", content)
    backup_reference_value = _require_text("backup_reference", backup_reference)
    updated_at_value = _require_text("updated_at", updated_at if updated_at is not None else _now_iso())

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "content": content_value,
        "content_hash": compute_content_hash(content_value),
        "backup_reference": backup_reference_value,
        "updated_at": updated_at_value,
    }


def build_remediation_audit_record(
    artist,
    title,
    content_type,
    pre_change_reference,
    remediation_reason,
    outcome,
    post_change_reference=None,
    timestamp=None,
    details=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    pre_change_reference_value = _require_text("pre_change_reference", pre_change_reference)
    remediation_reason_value = _require_text("remediation_reason", remediation_reason)
    outcome_value = validate_remediation_outcome(outcome)

    if post_change_reference is None:
        post_change_reference_value = None
    else:
        post_change_reference_value = _require_text("post_change_reference", post_change_reference)

    timestamp_value = _require_text("timestamp", timestamp if timestamp is not None else _now_iso())
    if details is None:
        details_value = None
    else:
        if not isinstance(details, dict):
            raise ValueError("details must be a dictionary; got {!r}".format(details))
        details_value = details

    record = {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "pre_change_reference": pre_change_reference_value,
        "post_change_reference": post_change_reference_value,
        "remediation_reason": remediation_reason_value,
        "outcome": outcome_value,
        "timestamp": timestamp_value,
    }
    if details_value is not None:
        record["details"] = details_value
    return record


def create_backup_record(
    artist,
    title,
    content_type,
    content,
    backups_dir=DEFAULT_BACKUPS_DIR,
    captured_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_value = _require_text("content", content)
    captured_at_value = _require_text("captured_at", captured_at if captured_at is not None else _now_iso())

    song_key = derive_song_key(artist_value, title_value)
    target_dir = Path(backups_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp_slug = re.sub(r"[^0-9T+-]", "", captured_at_value.replace(":", "").replace("-", ""))
    target_path = target_dir / "{}-{}-{}.json".format(
        _safe_path_component(song_key),
        content_type_value,
        timestamp_slug,
    )

    record = {
        "artist": artist_value,
        "title": title_value,
        "song_key": song_key,
        "content_type": content_type_value,
        "content": content_value,
        "content_hash": compute_content_hash(content_value),
        "captured_at": captured_at_value,
        "backup_path": str(target_path),
    }

    with target_path.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved remediation backup to %s", target_path)
    return record


def load_remediated_content(file_path=DEFAULT_REMEDIATED_CONTENT_PATH):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_remediated_content_state(), []
        return _empty_remediated_content_state(), errors

    if not isinstance(document, dict):
        return _empty_remediated_content_state(), [
            _validation_error(
                file_path,
                "$",
                "remediated content file must contain a top-level object; got {!r}".format(document),
            )
        ]

    state_errors = []
    version = document.get("version", REMEDIATED_CONTENT_VERSION)
    if version != REMEDIATED_CONTENT_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(REMEDIATED_CONTENT_VERSION, version),
            )
        )
        version = REMEDIATED_CONTENT_VERSION

    updated_at = document.get("updated_at")
    if updated_at is not None and not isinstance(updated_at, str):
        state_errors.append(
            _validation_error(
                file_path,
                "updated_at",
                "updated_at must be a string or null; got {!r}".format(updated_at),
            )
        )
        updated_at = None

    entries = document.get("entries")
    if entries is None:
        return _empty_remediated_content_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries is required and must be an object keyed by song_key; got None",
            )
        ]

    if not isinstance(entries, dict):
        return _empty_remediated_content_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries must be an object keyed by song_key; got {!r}".format(entries),
            )
        ]

    validated_entries = {}
    for outer_song_key, content_type_map in entries.items():
        if not isinstance(content_type_map, dict):
            state_errors.append(
                _validation_error(
                    file_path,
                    "entries['{}']".format(outer_song_key),
                    "song entries must be dictionaries keyed by content_type; got {!r}".format(
                        content_type_map
                    ),
                )
            )
            continue

        validated_song_entries = {}
        for content_type_key, record in content_type_map.items():
            record_field_base = "entries['{}'].{}".format(outer_song_key, content_type_key)
            if not isinstance(record, dict):
                state_errors.append(
                    _validation_error(
                        file_path,
                        record_field_base,
                        "remediated content entries must be dictionaries; got {!r}".format(record),
                    )
                )
                continue

            try:
                validated_record = build_remediated_content_record(
                    record.get("artist"),
                    record.get("title"),
                    record.get("content_type"),
                    record.get("content"),
                    record.get("backup_reference"),
                    updated_at=record.get("updated_at"),
                )
            except ValueError as exc:
                state_errors.append(
                    _validation_error(
                        file_path,
                        record_field_base,
                        str(exc),
                    )
                )
                continue

            if validated_record["song_key"] != outer_song_key:
                state_errors.append(
                    _validation_error(
                        file_path,
                        "{}.song_key".format(record_field_base),
                        "entry key must match song_key {}; got {!r}".format(
                            validated_record["song_key"],
                            outer_song_key,
                        ),
                    )
                )
                continue

            if validated_record["content_type"] != content_type_key:
                state_errors.append(
                    _validation_error(
                        file_path,
                        "{}.content_type".format(record_field_base),
                        "content_type must match enclosing entry key {!r}; got {!r}".format(
                            content_type_key,
                            validated_record["content_type"],
                        ),
                    )
                )
                continue

            validated_song_entries[content_type_key] = validated_record

        if validated_song_entries:
            validated_entries[outer_song_key] = validated_song_entries

    return {
        "version": version,
        "updated_at": updated_at,
        "entries": validated_entries,
    }, errors + state_errors


def build_remediated_content_state(remediated_content_records, updated_at=None):
    entries = {}
    for remediated_content in remediated_content_records:
        if not isinstance(remediated_content, dict):
            raise ValueError(
                "remediated content records must be dictionaries; got {!r}".format(remediated_content)
            )

        record = build_remediated_content_record(
            remediated_content.get("artist"),
            remediated_content.get("title"),
            remediated_content.get("content_type"),
            remediated_content.get("content"),
            remediated_content.get("backup_reference"),
            updated_at=remediated_content.get("updated_at"),
        )
        entries.setdefault(record["song_key"], {})[record["content_type"]] = record

    return {
        "version": REMEDIATED_CONTENT_VERSION,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_remediated_content(file_path, remediated_content_records, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    state = build_remediated_content_state(
        remediated_content_records,
        updated_at=updated_at,
    )
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved remediated content to %s", file_path)
    return state


def append_remediation_audit_record(file_path, remediation_audit_record):
    target_path = Path(file_path)

    try:
        if not isinstance(remediation_audit_record, dict):
            raise ValueError(
                "remediation audit records must be dictionaries; got {!r}".format(
                    remediation_audit_record
                )
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(remediation_audit_record, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.error("Error writing remediation audit file %s: %s", target_path, exc)
        return False


def record_remediation_audit(
    artist,
    title,
    content_type,
    pre_change_reference,
    remediation_reason,
    outcome,
    post_change_reference=None,
    timestamp=None,
    file_path=DEFAULT_REMEDIATION_AUDIT_PATH,
    details=None,
):
    audit_record = build_remediation_audit_record(
        artist,
        title,
        content_type,
        pre_change_reference,
        remediation_reason,
        outcome,
        post_change_reference=post_change_reference,
        timestamp=timestamp,
        details=details,
    )
    return append_remediation_audit_record(file_path, audit_record)


def load_remediation_audit_records(file_path=DEFAULT_REMEDIATION_AUDIT_PATH):
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
                            "Invalid JSON in remediation audit file: {}".format(exc),
                        )
                    )
                    continue

                if not isinstance(record, dict):
                    errors.append(
                        _validation_error(
                            target_path,
                            "[line {}]".format(line_number),
                            "Remediation audit entries must be dictionaries; got {!r}".format(record),
                        )
                    )
                    continue

                records.append(record)
    except OSError as exc:
        errors.append(
            _validation_error(
                target_path,
                "$",
                "Failed to read remediation audit file: {}".format(exc),
            )
        )
        logger.error("Error reading remediation audit file %s: %s", target_path, exc)

    return records, errors
