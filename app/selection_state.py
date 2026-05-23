import json
import logging
from datetime import datetime
from pathlib import Path

from app.content_models import build_favourite_record


logger = logging.getLogger(__name__)

NAMED_SELECTION_VERSION = 1


def _empty_named_selection_state(selection_name=None, updated_at=None):
    return {
        "version": NAMED_SELECTION_VERSION,
        "selection_name": selection_name,
        "updated_at": updated_at,
        "entries": [],
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
                "Invalid JSON in selection file: {}".format(exc),
            )
        ]
    except OSError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Failed to read selection file: {}".format(exc),
            )
        ]


def _validate_required_text(file_path, field_path, value, errors):
    if not isinstance(value, str) or value == "":
        errors.append(
            _validation_error(
                file_path,
                field_path,
                "{} must be a non-empty string; got {!r}".format(
                    field_path.rsplit(".", 1)[-1],
                    value,
                ),
            )
        )
        return None
    return value


def _validate_named_selection_record(file_path, index, record, errors):
    record_field_base = "entries[{}]".format(index)

    if not isinstance(record, dict):
        errors.append(
            _validation_error(
                file_path,
                record_field_base,
                "selection entries must be dictionaries; got {!r}".format(record),
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

    if artist is None or title is None:
        return None

    if "song_key" in record:
        song_key = _validate_required_text(
            file_path,
            "{}.song_key".format(record_field_base),
            record.get("song_key"),
            errors,
        )
        if song_key is None:
            return None
    else:
        song_key = None

    try:
        validated_record = build_favourite_record(artist, title, song_key=song_key)
    except ValueError as exc:
        errors.append(
            _validation_error(
                file_path,
                "{}.song_key".format(record_field_base),
                str(exc),
            )
        )
        return None

    return validated_record


def _validate_selection_name(file_path, selection_name, errors):
    if selection_name is None:
        return None
    if not isinstance(selection_name, str) or selection_name == "":
        errors.append(
            _validation_error(
                file_path,
                "selection_name",
                "selection_name must be a non-empty string or null; got {!r}".format(
                    selection_name
                ),
            )
        )
        return None
    return selection_name


def load_named_selection(file_path):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_named_selection_state(selection_name=file_path.stem), []
        return _empty_named_selection_state(selection_name=file_path.stem), errors

    if not isinstance(document, dict):
        return _empty_named_selection_state(selection_name=file_path.stem), [
            _validation_error(
                file_path,
                "$",
                "selection file must contain a top-level object; got {!r}".format(document),
            )
        ]

    state_errors = []
    version = document.get("version", NAMED_SELECTION_VERSION)
    if version != NAMED_SELECTION_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(NAMED_SELECTION_VERSION, version),
            )
        )
        version = NAMED_SELECTION_VERSION

    selection_name = _validate_selection_name(file_path, document.get("selection_name"), state_errors)
    if selection_name is None:
        selection_name = file_path.stem

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
        return _empty_named_selection_state(selection_name=selection_name, updated_at=updated_at), (
            errors
            + state_errors
            + [
                _validation_error(
                    file_path,
                    "entries",
                    "entries is required and must be a list of song entries; got None",
                )
            ]
        )

    if not isinstance(entries, list):
        return _empty_named_selection_state(selection_name=selection_name, updated_at=updated_at), (
            errors
            + state_errors
            + [
                _validation_error(
                    file_path,
                    "entries",
                    "entries must be a list of song entries; got {!r}".format(entries),
                )
            ]
        )

    validated_entries = []
    for index, record in enumerate(entries):
        validated_record = _validate_named_selection_record(
            file_path,
            index,
            record,
            state_errors,
        )
        if validated_record is not None:
            validated_entries.append(validated_record)

    state = {
        "version": version,
        "selection_name": selection_name,
        "updated_at": updated_at,
        "entries": validated_entries,
    }
    return state, errors + state_errors


def build_named_selection_state(selection_records, selection_name=None, updated_at=None):
    entries = []
    for selection_record in selection_records:
        if not isinstance(selection_record, dict):
            raise ValueError(
                "selection records must be dictionaries; got {!r}".format(selection_record)
            )

        record = build_favourite_record(
            selection_record.get("artist"),
            selection_record.get("title"),
            song_key=selection_record.get("song_key"),
        )
        entries.append(record)

    resolved_selection_name = selection_name if selection_name is not None else None
    if resolved_selection_name is None:
        resolved_selection_name = "selection"

    return {
        "version": NAMED_SELECTION_VERSION,
        "selection_name": resolved_selection_name,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_named_selection(file_path, selection_records, selection_name=None, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    resolved_selection_name = selection_name if selection_name is not None else file_path.stem
    state = build_named_selection_state(
        selection_records,
        selection_name=resolved_selection_name,
        updated_at=updated_at,
    )
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved selection to %s", file_path)
