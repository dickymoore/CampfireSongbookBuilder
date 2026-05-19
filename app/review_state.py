import copy
import json
import logging
from datetime import datetime
from pathlib import Path

from app.content_models import (
    build_quality_signal,
    build_quality_status,
    build_review_decision,
    derive_song_key,
    validate_content_hash,
    validate_content_type,
    validate_quality,
    validate_severity,
)


logger = logging.getLogger(__name__)

QUALITY_STATUS_VERSION = 1
REVIEW_DECISION_VERSION = 1
DEFAULT_QUALITY_STATUS_PATH = Path("data/review/quality_status.json")
DEFAULT_REVIEW_DECISIONS_PATH = Path("data/review/review_decisions.json")


def _empty_quality_status_state(updated_at=None):
    return {
        "version": QUALITY_STATUS_VERSION,
        "updated_at": updated_at,
        "entries": {},
    }


def _empty_review_decisions_state(updated_at=None):
    return {
        "version": REVIEW_DECISION_VERSION,
        "updated_at": updated_at,
        "entries": {},
    }


def _validation_error(file_path, field, reason):
    return {
        "file_path": str(file_path),
        "field": field,
        "reason": reason,
    }


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
                "Invalid JSON in quality status file: {}".format(exc),
            )
        ]
    except OSError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Failed to read quality status file: {}".format(exc),
            )
        ]


def _validate_required_text(file_path, field_path, value, errors):
    if not isinstance(value, str) or value == "":
        errors.append(
            _validation_error(
                file_path,
                field_path,
                "{} must be a non-empty string; got {!r}".format(field_path.rsplit(".", 1)[-1], value),
            )
        )
        return None
    return value


def _validate_optional_text(file_path, field_path, value, errors):
    if value is None:
        return None
    return _validate_required_text(file_path, field_path, value, errors)


def _validate_signal_entry(file_path, base_field_path, signal, index, errors):
    signal_field_path = "{}[{}]".format(base_field_path, index)
    if not isinstance(signal, dict):
        errors.append(
            _validation_error(
                file_path,
                signal_field_path,
                "signals entries must be dictionaries; got {!r}".format(signal),
            )
        )
        return None

    code = _validate_required_text(
        file_path,
        "{}.code".format(signal_field_path),
        signal.get("code"),
        errors,
    )
    severity_value = signal.get("severity")
    message = _validate_required_text(
        file_path,
        "{}.message".format(signal_field_path),
        signal.get("message"),
        errors,
    )
    content_type_value = signal.get("content_type")

    if severity_value is not None:
        try:
            validate_severity(severity_value)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.severity".format(signal_field_path),
                    str(exc),
                )
            )
            severity_value = None

    if content_type_value is not None:
        try:
            validate_content_type(content_type_value)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.content_type".format(signal_field_path),
                    str(exc),
                )
            )
            content_type_value = None

    if code is None or severity_value is None or message is None or content_type_value is None:
        return None

    return build_quality_signal(code, severity_value, message, content_type_value)


def _validate_quality_status_record(file_path, outer_song_key, content_type_key, record, errors):
    record_field_base = "entries['{}'].{}".format(outer_song_key, content_type_key)

    if not isinstance(record, dict):
        errors.append(
            _validation_error(
                file_path,
                record_field_base,
                "quality status entries must be dictionaries; got {!r}".format(record),
            )
        )
        return None

    artist = _validate_required_text(
        file_path,
        "{}.artist".format(record_field_base),
        record.get("artist"),
        errors,
    )
    title = _validate_required_text(
        file_path,
        "{}.title".format(record_field_base),
        record.get("title"),
        errors,
    )
    song_key = _validate_required_text(
        file_path,
        "{}.song_key".format(record_field_base),
        record.get("song_key"),
        errors,
    )

    record_content_type = record.get("content_type")
    if record_content_type is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_type".format(record_field_base),
                "content_type must be a non-empty string; got None",
            )
        )
        validated_content_type = None
    else:
        try:
            validated_content_type = validate_content_type(record_content_type)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.content_type".format(record_field_base),
                    str(exc),
                )
            )
            validated_content_type = None

    if validated_content_type is not None and validated_content_type != content_type_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_type".format(record_field_base),
                "content_type must match enclosing entry key {!r}; got {!r}".format(
                    content_type_key,
                    validated_content_type,
                ),
            )
        )
        validated_content_type = None

    content_hash = record.get("content_hash")
    if content_hash is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_hash".format(record_field_base),
                "content_hash must be a non-empty string; got None",
            )
        )
        validated_content_hash = None
    else:
        try:
            validated_content_hash = validate_content_hash(content_hash)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.content_hash".format(record_field_base),
                    str(exc),
                )
            )
            validated_content_hash = None

    quality = record.get("quality")
    if quality is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.quality".format(record_field_base),
                "quality must be a non-empty string; got None",
            )
        )
        validated_quality = None
    else:
        try:
            validated_quality = validate_quality(quality)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.quality".format(record_field_base),
                    str(exc),
                )
            )
            validated_quality = None

    signals = record.get("signals")
    validated_signals = []
    if signals is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.signals".format(record_field_base),
                "signals must be a list; got None",
            )
        )
    elif not isinstance(signals, list):
        errors.append(
            _validation_error(
                file_path,
                "{}.signals".format(record_field_base),
                "signals must be a list; got {!r}".format(signals),
            )
        )
    else:
        for signal_index, signal in enumerate(signals):
            validated_signal = _validate_signal_entry(
                file_path,
                "{}.signals".format(record_field_base),
                signal,
                signal_index,
                errors,
            )
            if validated_signal is not None:
                validated_signals.append(validated_signal)

    assessed_at = _validate_optional_text(
        file_path,
        "{}.assessed_at".format(record_field_base),
        record.get("assessed_at"),
        errors,
    )

    if (
        artist is None
        or title is None
        or song_key is None
        or validated_content_type is None
        or validated_content_hash is None
        or validated_quality is None
    ):
        return None

    derived_song_key = derive_song_key(artist, title)
    if song_key != derived_song_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.song_key".format(record_field_base),
                "song_key must match derived song identity {}; got {!r}".format(
                    derived_song_key,
                    song_key,
                ),
            )
        )
        return None

    if outer_song_key != derived_song_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.song_key".format(record_field_base),
                "entry key must match derived song identity {}; got {!r}".format(
                    derived_song_key,
                    outer_song_key,
                ),
            )
        )
        return None

    return build_quality_status(
        artist,
        title,
        validated_content_type,
        validated_content_hash,
        validated_quality,
        signals=validated_signals,
        assessed_at=assessed_at,
    )


def _validate_review_decision_record(
    file_path,
    outer_song_key,
    content_type_key,
    record,
    errors,
    current_content_hash=None,
):
    record_field_base = "entries['{}'].{}".format(outer_song_key, content_type_key)

    if not isinstance(record, dict):
        errors.append(
            _validation_error(
                file_path,
                record_field_base,
                "review decision entries must be dictionaries; got {!r}".format(record),
            )
        )
        return None

    song_key = _validate_required_text(
        file_path,
        "{}.song_key".format(record_field_base),
        record.get("song_key"),
        errors,
    )

    record_content_type = record.get("content_type")
    if record_content_type is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_type".format(record_field_base),
                "content_type must be a non-empty string; got None",
            )
        )
        validated_content_type = None
    else:
        try:
            validated_content_type = validate_content_type(record_content_type)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.content_type".format(record_field_base),
                    str(exc),
                )
            )
            validated_content_type = None

    content_hash = record.get("content_hash")
    if content_hash is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_hash".format(record_field_base),
                "content_hash must be a non-empty string; got None",
            )
        )
        validated_content_hash = None
    else:
        try:
            validated_content_hash = validate_content_hash(content_hash)
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.content_hash".format(record_field_base),
                    str(exc),
                )
            )
            validated_content_hash = None

    decision = record.get("decision")
    if decision is None:
        errors.append(
            _validation_error(
                file_path,
                "{}.decision".format(record_field_base),
                "decision must be a non-empty string; got None",
            )
        )
        validated_decision = None
    else:
        try:
            validated_decision = build_review_decision(
                song_key,
                validated_content_type if validated_content_type is not None else record_content_type,
                validated_content_hash if validated_content_hash is not None else content_hash,
                decision,
                reason=record.get("reason"),
                decided_at=record.get("decided_at"),
            )
        except ValueError as exc:
            errors.append(
                _validation_error(
                    file_path,
                    "{}.decision".format(record_field_base),
                    str(exc),
                )
            )
            validated_decision = None

    if song_key is None or validated_content_type is None or validated_content_hash is None or validated_decision is None:
        return None

    if song_key != outer_song_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.song_key".format(record_field_base),
                "entry key must match song_key {}; got {!r}".format(song_key, outer_song_key),
            )
        )
        return None

    if validated_content_type != content_type_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_type".format(record_field_base),
                "content_type must match enclosing entry key {!r}; got {!r}".format(
                    content_type_key,
                    validated_content_type,
                ),
            )
        )
        return None

    if current_content_hash is not None and validated_content_hash != current_content_hash:
        errors.append(
            _validation_error(
                file_path,
                "{}.content_hash".format(record_field_base),
                "review decision is stale for current content hash {}; got {!r}".format(
                    current_content_hash,
                    validated_content_hash,
                ),
            )
        )
        return None

    return validated_decision


def load_quality_status(file_path=DEFAULT_QUALITY_STATUS_PATH):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_quality_status_state(), []
        return _empty_quality_status_state(), errors

    if not isinstance(document, dict):
        return _empty_quality_status_state(), [
            _validation_error(
                file_path,
                "$",
                "quality status file must contain a top-level object; got {!r}".format(document),
            )
        ]

    state_errors = []
    version = document.get("version", QUALITY_STATUS_VERSION)
    if version != QUALITY_STATUS_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(QUALITY_STATUS_VERSION, version),
            )
        )
        version = QUALITY_STATUS_VERSION

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
        return _empty_quality_status_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries is required and must be an object keyed by song_key; got None",
            )
        ]

    if not isinstance(entries, dict):
        return _empty_quality_status_state(updated_at=updated_at), errors + state_errors + [
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
            try:
                validate_content_type(content_type_key)
            except ValueError as exc:
                state_errors.append(
                    _validation_error(
                        file_path,
                        "entries['{}'].{}".format(outer_song_key, content_type_key),
                        str(exc),
                    )
                )
                continue

            validated_record = _validate_quality_status_record(
                file_path,
                outer_song_key,
                content_type_key,
                record,
                state_errors,
            )
            if validated_record is not None:
                validated_song_entries[content_type_key] = validated_record

        if validated_song_entries:
            validated_entries[outer_song_key] = validated_song_entries

    state = {
        "version": version,
        "updated_at": updated_at,
        "entries": validated_entries,
    }
    return state, errors + state_errors


def load_review_decisions(file_path=DEFAULT_REVIEW_DECISIONS_PATH, current_content_hashes=None):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_review_decisions_state(), []
        return _empty_review_decisions_state(), errors

    if not isinstance(document, dict):
        return _empty_review_decisions_state(), [
            _validation_error(
                file_path,
                "$",
                "review decisions file must contain a top-level object; got {!r}".format(document),
            )
        ]

    state_errors = []
    version = document.get("version", REVIEW_DECISION_VERSION)
    if version != REVIEW_DECISION_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(REVIEW_DECISION_VERSION, version),
            )
        )
        version = REVIEW_DECISION_VERSION

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
        return _empty_review_decisions_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries is required and must be an object keyed by song_key; got None",
            )
        ]

    if not isinstance(entries, dict):
        return _empty_review_decisions_state(updated_at=updated_at), errors + state_errors + [
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
            try:
                validate_content_type(content_type_key)
            except ValueError as exc:
                state_errors.append(
                    _validation_error(
                        file_path,
                        "entries['{}'].{}".format(outer_song_key, content_type_key),
                        str(exc),
                    )
                )
                continue

            current_content_hash = None
            if isinstance(current_content_hashes, dict):
                current_song_hashes = current_content_hashes.get(outer_song_key, {})
                if isinstance(current_song_hashes, dict):
                    current_content_hash = current_song_hashes.get(content_type_key)

            validated_record = _validate_review_decision_record(
                file_path,
                outer_song_key,
                content_type_key,
                record,
                state_errors,
                current_content_hash=current_content_hash,
            )
            if validated_record is not None:
                validated_song_entries[content_type_key] = validated_record

        if validated_song_entries:
            validated_entries[outer_song_key] = validated_song_entries

    state = {
        "version": version,
        "updated_at": updated_at,
        "entries": validated_entries,
    }
    return state, errors + state_errors


def build_quality_status_state(quality_status_records, updated_at=None):
    entries = {}
    for quality_status in quality_status_records:
        if not isinstance(quality_status, dict):
            raise ValueError("quality status records must be dictionaries; got {!r}".format(quality_status))

        record = build_quality_status(
            quality_status.get("artist"),
            quality_status.get("title"),
            quality_status.get("content_type"),
            quality_status.get("content_hash"),
            quality_status.get("quality"),
            signals=quality_status.get("signals"),
            assessed_at=quality_status.get("assessed_at"),
        )
        entries.setdefault(record["song_key"], {})[record["content_type"]] = record

    return {
        "version": QUALITY_STATUS_VERSION,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_quality_status(file_path, quality_status_records, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    state = build_quality_status_state(quality_status_records, updated_at=updated_at)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved quality status to %s", file_path)
    return state


def build_review_decision_state(review_decision_records, updated_at=None):
    entries = {}
    for review_decision in review_decision_records:
        if not isinstance(review_decision, dict):
            raise ValueError("review decision records must be dictionaries; got {!r}".format(review_decision))

        record = build_review_decision(
            review_decision.get("song_key"),
            review_decision.get("content_type"),
            review_decision.get("content_hash"),
            review_decision.get("decision"),
            reason=review_decision.get("reason"),
            decided_at=review_decision.get("decided_at"),
        )
        entries.setdefault(record["song_key"], {})[record["content_type"]] = record

    return {
        "version": REVIEW_DECISION_VERSION,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_review_decisions(file_path, review_decision_records, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    state = build_review_decision_state(review_decision_records, updated_at=updated_at)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved review decisions to %s", file_path)
    return state
