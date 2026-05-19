import hashlib
import re


CONTENT_TYPES = ("lyrics", "chords")
QUALITY_VALUES = ("clean", "questionable", "missing")
REVIEW_DECISIONS = ("accept", "reject", "override")
SIGNAL_SEVERITIES = ("info", "warning", "error")
SOURCE_OUTCOMES = ("candidate", "not_found", "error")
CONTENT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_text(field_name, value):
    if not isinstance(value, str) or value == "":
        raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
    return value


def _optional_text(field_name, value):
    if value is None:
        return None
    return _require_text(field_name, value)


def _validate_enum(field_name, value, allowed_values):
    if value not in allowed_values:
        raise ValueError(
            "{} must be one of {}; got {!r}".format(
                field_name, ", ".join(repr(item) for item in allowed_values), value
            )
        )
    return value


def validate_content_type(content_type):
    return _validate_enum("content_type", content_type, CONTENT_TYPES)


def validate_quality(quality):
    return _validate_enum("quality", quality, QUALITY_VALUES)


def validate_review_decision(decision):
    return _validate_enum("decision", decision, REVIEW_DECISIONS)


def validate_severity(severity):
    return _validate_enum("severity", severity, SIGNAL_SEVERITIES)


def validate_source_outcome(status):
    return _validate_enum("status", status, SOURCE_OUTCOMES)


def derive_song_key(artist, title):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    return "{} - {}".format(artist_value, title_value)


def build_favourite_record(artist, title, song_key=None):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    derived_song_key = derive_song_key(artist_value, title_value)

    if song_key is None:
        song_key_value = derived_song_key
    else:
        song_key_value = _require_text("song_key", song_key)
        if song_key_value != derived_song_key:
            raise ValueError(
                "song_key must match derived song identity {}; got {!r}".format(
                    derived_song_key,
                    song_key_value,
                )
            )

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": song_key_value,
    }


def compute_content_hash(content):
    content_value = _require_text("content", content)
    digest = hashlib.sha256(content_value.encode("utf-8")).hexdigest()
    return "sha256:{}".format(digest)


def validate_content_hash(content_hash):
    content_hash_value = _require_text("content_hash", content_hash)
    if not CONTENT_HASH_PATTERN.match(content_hash_value):
        raise ValueError(
            "content_hash must match sha256:<hex>; got {!r}".format(content_hash_value)
        )
    return content_hash_value


def build_candidate_record(
    artist,
    title,
    content_type,
    source,
    content,
    source_artist=None,
    source_title=None,
    status="candidate",
    error=None,
    retrieved_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    source_value = _require_text("source", source)
    content_value = _require_text("content", content)
    status_value = validate_source_outcome(status)

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "source": source_value,
        "content": content_value,
        "content_hash": compute_content_hash(content_value),
        "source_artist": _optional_text("source_artist", source_artist),
        "source_title": _optional_text("source_title", source_title),
        "status": status_value,
        "error": _optional_text("error", error),
        "retrieved_at": _optional_text("retrieved_at", retrieved_at),
    }


def build_source_attempt_record(
    artist,
    title,
    content_type,
    source,
    status,
    error=None,
    retrieved_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    source_value = _require_text("source", source)
    status_value = validate_source_outcome(status)

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "source": source_value,
        "status": status_value,
        "error": _optional_text("error", error),
        "retrieved_at": _optional_text("retrieved_at", retrieved_at),
    }


def build_quality_signal(code, severity, message, content_type):
    code_value = _require_text("code", code)
    severity_value = validate_severity(severity)
    message_value = _require_text("message", message)
    content_type_value = validate_content_type(content_type)

    return {
        "code": code_value,
        "severity": severity_value,
        "message": message_value,
        "content_type": content_type_value,
    }


def _validate_quality_signal_record(signal):
    if not isinstance(signal, dict):
        raise ValueError("signals entries must be dictionaries; got {!r}".format(signal))

    return build_quality_signal(
        signal.get("code"),
        signal.get("severity"),
        signal.get("message"),
        signal.get("content_type"),
    )


def build_quality_status(
    artist,
    title,
    content_type,
    content_hash,
    quality,
    signals=None,
    assessed_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_hash_value = validate_content_hash(content_hash)
    quality_value = validate_quality(quality)
    signal_list = []

    if signals is not None:
        for signal in signals:
            signal_list.append(_validate_quality_signal_record(signal))

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "content_hash": content_hash_value,
        "quality": quality_value,
        "signals": signal_list,
        "assessed_at": _optional_text("assessed_at", assessed_at),
    }


def build_review_decision(
    song_key,
    content_type,
    content_hash,
    decision,
    reason=None,
    decided_at=None,
):
    song_key_value = _require_text("song_key", song_key)
    content_type_value = validate_content_type(content_type)
    content_hash_value = validate_content_hash(content_hash)
    decision_value = validate_review_decision(decision)

    return {
        "song_key": song_key_value,
        "content_type": content_type_value,
        "content_hash": content_hash_value,
        "decision": decision_value,
        "reason": _optional_text("reason", reason),
        "decided_at": _optional_text("decided_at", decided_at),
    }
