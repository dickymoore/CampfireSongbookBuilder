from datetime import datetime

from app.document_verification import validate_artifact_type, validate_verification_status


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _require_text(field_name, value):
    if not isinstance(value, str) or value == "":
        raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
    return value


def build_review_gate_decision(
    artifact_path,
    artifact_type,
    review_ready,
    failure_reasons=None,
    computed_at=None,
):
    artifact_path_value = _require_text("artifact_path", artifact_path)
    artifact_type_value = validate_artifact_type(artifact_type)

    if not isinstance(review_ready, bool):
        raise ValueError("review_ready must be a bool; got {!r}".format(review_ready))

    if failure_reasons is None:
        failure_reason_items = []
    elif not isinstance(failure_reasons, list):
        raise ValueError(
            "failure_reasons must be a list; got {!r}".format(failure_reasons)
        )
    else:
        failure_reason_items = failure_reasons

    failure_reason_values = []
    for index, reason in enumerate(failure_reason_items):
        failure_reason_values.append(
            _require_text("failure_reasons[{}]".format(index), reason)
        )

    computed_at_value = _require_text(
        "computed_at",
        computed_at if computed_at is not None else _now_iso(),
    )

    return {
        "artifact_path": artifact_path_value,
        "artifact_type": artifact_type_value,
        "review_ready": review_ready,
        "failure_reasons": failure_reason_values,
        "computed_at": computed_at_value,
    }


def compute_review_gate_decision(document_verification_record, computed_at=None):
    if not isinstance(document_verification_record, dict):
        raise ValueError(
            "document_verification_record must be a dictionary; got {!r}".format(
                document_verification_record
            )
        )

    artifact_path = _require_text(
        "document_verification_record.artifact_path",
        document_verification_record.get("artifact_path"),
    )
    artifact_type = validate_artifact_type(
        document_verification_record.get("artifact_type")
    )
    verification_status = validate_verification_status(
        document_verification_record.get("verification_status")
    )

    verification_reasons = document_verification_record.get("verification_reasons")
    if not isinstance(verification_reasons, list):
        raise ValueError(
            "document_verification_record.verification_reasons must be a list; got {!r}".format(
                verification_reasons
            )
        )

    if verification_status == "passed":
        review_ready = True
        failure_reasons = []
    else:
        review_ready = False
        failure_reasons = verification_reasons

    return build_review_gate_decision(
        artifact_path=artifact_path,
        artifact_type=artifact_type,
        review_ready=review_ready,
        failure_reasons=failure_reasons,
        computed_at=computed_at,
    )


def compute_review_gate_decisions(document_verification_records, computed_at=None):
    decisions = []
    for record in document_verification_records or []:
        decisions.append(
            compute_review_gate_decision(record, computed_at=computed_at)
        )
    return decisions
