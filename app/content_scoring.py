from datetime import datetime

from app.content_models import (
    derive_song_key,
    validate_content_hash,
    validate_content_type,
)


QUALITY_BANDS = ("clean", "reviewable", "questionable", "poor")
SCORE_VERSION_V1 = "v1"

_CLEAN_MINIMUM = 85
_REVIEWABLE_MINIMUM = 60
_QUESTIONABLE_MINIMUM = 40


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _require_text(field_name, value):
    if not isinstance(value, str) or value == "":
        raise ValueError("{} must be a non-empty string; got {!r}".format(field_name, value))
    return value


def _validate_score_reason(reason, index):
    if not isinstance(reason, str) or reason == "":
        raise ValueError(
            "score_reasons[{}] must be a non-empty string; got {!r}".format(index, reason)
        )
    return reason


def validate_quality_score(quality_score):
    if isinstance(quality_score, bool) or not isinstance(quality_score, int):
        raise ValueError(
            "quality_score must be an integer in 0-100; got {!r}".format(quality_score)
        )
    if quality_score < 0 or quality_score > 100:
        raise ValueError(
            "quality_score must be an integer in 0-100; got {!r}".format(quality_score)
        )
    return quality_score


def quality_band_for_score(quality_score):
    score_value = validate_quality_score(quality_score)
    if score_value >= _CLEAN_MINIMUM:
        return "clean"
    if score_value >= _REVIEWABLE_MINIMUM:
        return "reviewable"
    if score_value >= _QUESTIONABLE_MINIMUM:
        return "questionable"
    return "poor"


def validate_quality_band(quality_band):
    if quality_band not in QUALITY_BANDS:
        raise ValueError(
            "quality_band must be one of {}; got {!r}".format(
                ", ".join(repr(item) for item in QUALITY_BANDS),
                quality_band,
            )
        )
    return quality_band


def validate_score_version(score_version):
    score_version_value = _require_text("score_version", score_version)
    if score_version_value != SCORE_VERSION_V1:
        raise ValueError(
            "score_version must be {!r}; got {!r}".format(
                SCORE_VERSION_V1,
                score_version_value,
            )
        )
    return score_version_value


def build_content_score(
    artist,
    title,
    content_type,
    content_hash,
    quality_score,
    quality_band=None,
    score_version=SCORE_VERSION_V1,
    score_reasons=None,
    scored_at=None,
):
    artist_value = _require_text("artist", artist)
    title_value = _require_text("title", title)
    content_type_value = validate_content_type(content_type)
    content_hash_value = validate_content_hash(content_hash)
    quality_score_value = validate_quality_score(quality_score)
    derived_quality_band = quality_band_for_score(quality_score_value)
    score_version_value = validate_score_version(score_version)

    if quality_band is None:
        quality_band_value = derived_quality_band
    else:
        quality_band_value = validate_quality_band(quality_band)
        if quality_band_value != derived_quality_band:
            raise ValueError(
                "quality_band must match quality_score-derived band {!r}; got {!r}".format(
                    derived_quality_band,
                    quality_band_value,
                )
            )

    score_reason_values = []
    for index, reason in enumerate(score_reasons or []):
        score_reason_values.append(_validate_score_reason(reason, index))

    return {
        "artist": artist_value,
        "title": title_value,
        "song_key": derive_song_key(artist_value, title_value),
        "content_type": content_type_value,
        "content_hash": content_hash_value,
        "quality_score": quality_score_value,
        "quality_band": quality_band_value,
        "score_version": score_version_value,
        "score_reasons": score_reason_values,
        "scored_at": _require_text("scored_at", scored_at if scored_at is not None else _now_iso()),
    }
