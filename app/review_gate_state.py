import json
import logging
from datetime import datetime
from pathlib import Path

from app.review_gate import build_review_gate_decision


logger = logging.getLogger(__name__)

REVIEW_GATE_STATE_VERSION = 1
DEFAULT_REVIEW_GATE_STATE_PATH = Path("data/review/review_gate_decisions.json")


def _empty_review_gate_state(updated_at=None):
    return {
        "version": REVIEW_GATE_STATE_VERSION,
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
                "Invalid JSON in review gate state file: {}".format(exc),
            )
        ]
    except OSError as exc:
        return None, [
            _validation_error(
                file_path,
                "$",
                "Failed to read review gate state file: {}".format(exc),
            )
        ]


def artifact_identity(review_gate_decision):
    if not isinstance(review_gate_decision, dict):
        return (None, None)
    artifact_path = review_gate_decision.get("artifact_path")
    artifact_type = review_gate_decision.get("artifact_type")
    if isinstance(artifact_path, Path):
        artifact_path = str(artifact_path)
    if isinstance(artifact_type, str):
        artifact_type = artifact_type.lower()
    return (artifact_path, artifact_type)


def load_review_gate_state(file_path=DEFAULT_REVIEW_GATE_STATE_PATH):
    file_path = Path(file_path)
    document, errors = _load_json_document(file_path)

    if document is None:
        if not file_path.exists():
            return _empty_review_gate_state(), []
        return _empty_review_gate_state(), errors

    if not isinstance(document, dict):
        return _empty_review_gate_state(), errors + [
            _validation_error(
                file_path,
                "$",
                "review gate state file must contain a top-level object; got {!r}".format(
                    document
                ),
            )
        ]

    state_errors = []
    version = document.get("version", REVIEW_GATE_STATE_VERSION)
    if version != REVIEW_GATE_STATE_VERSION:
        state_errors.append(
            _validation_error(
                file_path,
                "version",
                "version must be {}; got {!r}".format(REVIEW_GATE_STATE_VERSION, version),
            )
        )
        version = REVIEW_GATE_STATE_VERSION

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
        return _empty_review_gate_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries is required and must be an object keyed by artifact_path; got None",
            )
        ]

    if not isinstance(entries, dict):
        return _empty_review_gate_state(updated_at=updated_at), errors + state_errors + [
            _validation_error(
                file_path,
                "entries",
                "entries must be an object keyed by artifact_path; got {!r}".format(entries),
            )
        ]

    validated_entries = {}
    for outer_artifact_path, artifact_entries in entries.items():
        field_base = "entries['{}']".format(outer_artifact_path)
        if not isinstance(artifact_entries, dict):
            state_errors.append(
                _validation_error(
                    file_path,
                    field_base,
                    "artifact entry groups must be objects keyed by artifact_type; got {!r}".format(
                        artifact_entries
                    ),
                )
            )
            continue

        for outer_artifact_type, record in artifact_entries.items():
            record_field_base = "{}['{}']".format(field_base, outer_artifact_type)
            if not isinstance(record, dict):
                state_errors.append(
                    _validation_error(
                        file_path,
                        record_field_base,
                        "review gate decision entries must be dictionaries; got {!r}".format(record),
                    )
                )
                continue

            try:
                built = build_review_gate_decision(
                    record.get("artifact_path"),
                    record.get("artifact_type"),
                    record.get("review_ready"),
                    failure_reasons=record.get("failure_reasons"),
                    computed_at=record.get("computed_at"),
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

            identity = artifact_identity(built)
            if identity[0] != outer_artifact_path:
                state_errors.append(
                    _validation_error(
                        file_path,
                        "{}.artifact_path".format(record_field_base),
                        "entry key must match artifact_path {!r}; got {!r}".format(
                            identity[0],
                            outer_artifact_path,
                        ),
                    )
                )
                continue

            if identity[1] != str(outer_artifact_type).lower():
                state_errors.append(
                    _validation_error(
                        file_path,
                        "{}.artifact_type".format(record_field_base),
                        "entry key must match artifact_type {!r}; got {!r}".format(
                            identity[1],
                            outer_artifact_type,
                        ),
                    )
                )
                continue

            validated_entries.setdefault(identity[0], {})[identity[1]] = built

    return {
        "version": version,
        "updated_at": updated_at,
        "entries": validated_entries,
    }, errors + state_errors


def build_review_gate_state(review_gate_decisions, updated_at=None):
    entries = {}
    for decision in review_gate_decisions or []:
        if not isinstance(decision, dict):
            raise ValueError(
                "review gate decision records must be dictionaries; got {!r}".format(decision)
            )

        record = build_review_gate_decision(
            decision.get("artifact_path"),
            decision.get("artifact_type"),
            decision.get("review_ready"),
            failure_reasons=decision.get("failure_reasons"),
            computed_at=decision.get("computed_at"),
        )
        entries.setdefault(record["artifact_path"], {})[record["artifact_type"]] = record

    return {
        "version": REVIEW_GATE_STATE_VERSION,
        "updated_at": updated_at if updated_at is not None else _now_iso(),
        "entries": entries,
    }


def save_review_gate_state(file_path, review_gate_decisions, updated_at=None):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    state = build_review_gate_state(review_gate_decisions, updated_at=updated_at)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    logger.info("Saved review gate state to %s", file_path)
    return state


def refresh_review_gate_state(
    file_path=DEFAULT_REVIEW_GATE_STATE_PATH,
    review_gate_decisions=None,
    remove_artifact_paths=None,
    updated_at=None,
):
    file_path = Path(file_path)
    state, errors = load_review_gate_state(file_path)
    if errors:
        logger.warning(
            "Review gate state load reported %d recoverable issue(s).",
            len(errors),
        )

    merged_by_identity = {}
    for artifact_entries in (state.get("entries") or {}).values():
        if not isinstance(artifact_entries, dict):
            continue
        for record in artifact_entries.values():
            identity = artifact_identity(record)
            if identity[0] and identity[1]:
                merged_by_identity[identity] = record

    for record in review_gate_decisions or []:
        if not isinstance(record, dict):
            raise ValueError(
                "review gate decision records must be dictionaries; got {!r}".format(record)
            )
        built = build_review_gate_decision(
            record.get("artifact_path"),
            record.get("artifact_type"),
            record.get("review_ready"),
            failure_reasons=record.get("failure_reasons"),
            computed_at=record.get("computed_at"),
        )
        merged_by_identity[artifact_identity(built)] = built

    for artifact_path in remove_artifact_paths or []:
        if not artifact_path:
            continue
        artifact_path = str(artifact_path)
        for identity in [key for key in merged_by_identity.keys() if key[0] == artifact_path]:
            merged_by_identity.pop(identity, None)

    return save_review_gate_state(
        file_path,
        list(merged_by_identity.values()),
        updated_at=updated_at,
    )

