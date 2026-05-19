import json
import logging
from datetime import datetime
from pathlib import Path

from app.content_models import build_favourite_record


logger = logging.getLogger(__name__)

FAVOURITES_VERSION = 1
DEFAULT_FAVOURITES_PATH = Path("data/selections/favourites.json")


def _empty_favourites_state(updated_at=None):
    return {
        "version": FAVOURITES_VERSION,
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
                "Invalid JSON in favourites file: {}".format(exc),
            )
        ]
    except OSError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Failed to read favourites file: {}".format(exc),
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


def _validate_favourite_record(file_path, outer_song_key, record, errors):
    record_field_base = "entries['{}']".format(outer_song_key)

    if not isinstance(record, dict):
        errors.append(
            _validation_error(
                file_path,
                record_field_base,
                "favourite entries must be dictionaries; got {!r}".format(record),
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

    if validated_record["song_key"] != outer_song_key:
        errors.append(
            _validation_error(
                file_path,
                "{}.song_key".format(record_field_base),
                "entry key must match derived song identity {}; got {!r}".format(
                    validated_record["song_key"],
                    outer_song_key,
                ),
            )
        )
        return None

    return validated_record


def load_favourites(file_path=DEFAULT_FAVOURITES_PATH):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_favourites_state(), []
        return _empty_favourites_state(), errors

    if not isinstance(document, dict):
        return _empty_favourites_state(), [
            _validation_error(
                file_path,
                "$",
                "favourites file must contain a top-level object; got {!r}".format(document),
            )
        ]

    state_errors = []
    version = document.get("version", FAVOURITES_VERSION)
    if version != FAVOURITES_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(FAVOURITES_VERSION, version),
            )
        )
        version = FAVOURITES_VERSION

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
        return _empty_favourites_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries is required and must be an object keyed by song_key; got None",
            )
        ]

    if not isinstance(entries, dict):
        return _empty_favourites_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries must be an object keyed by song_key; got {!r}".format(entries),
            )
        ]

    validated_entries = {}
    for outer_song_key, record in entries.items():
        validated_record = _validate_favourite_record(
            file_path,
            outer_song_key,
            record,
            state_errors,
        )
        if validated_record is not None:
            validated_entries[outer_song_key] = validated_record

    state = {
        "version": version,
        "updated_at": updated_at,
        "entries": validated_entries,
    }
    return state, errors + state_errors


def build_favourites_state(favourite_records, updated_at=None):
    entries = {}
    for favourite in favourite_records:
        if not isinstance(favourite, dict):
            raise ValueError("favourite records must be dictionaries; got {!r}".format(favourite))

        record = build_favourite_record(
            favourite.get("artist"),
            favourite.get("title"),
            song_key=favourite.get("song_key"),
        )
        entries[record["song_key"]] = record

    return {
        "version": FAVOURITES_VERSION,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_favourites(file_path, favourite_records, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    state = build_favourites_state(favourite_records, updated_at=updated_at)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved favourites to %s", file_path)
