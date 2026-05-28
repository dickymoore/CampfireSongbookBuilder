from datetime import datetime

from app.content_models import (
    build_quality_status,
    derive_song_key,
    validate_content_hash,
    validate_content_type,
)


QUALITY_BANDS = ("clean", "reviewable", "questionable", "poor")
SCORE_VERSION_V1 = "v1"
_QUALITY_BAND_PRIORITY = {
    "poor": 0,
    "questionable": 1,
    "reviewable": 2,
    "clean": 3,
}

_CLEAN_MINIMUM = 85
_REVIEWABLE_MINIMUM = 60
_QUESTIONABLE_MINIMUM = 40

_DEFAULT_SEVERITY_PENALTIES = {
    "info": 0,
    "warning": 8,
    "error": 20,
}

_SIGNAL_PENALTIES = {
    "lyrics": {
        "missing_lyrics": 100,
        "unusable_lyrics": 45,
        "duplicate_block": 40,
        "html_residue": 14,
        "email_header_artifacts": 12,
        "excessive_bracket_noise": 10,
        "print_hostile_content": 18,
        "low_confidence_match": 20,
    },
    "chords": {
        "missing_chords": 100,
        "unusable_chords": 45,
        "duplicate_block": 38,
        "html_residue": 10,
        "email_header_artifacts": 8,
        "excessive_bracket_noise": 4,
        "print_hostile_content": 14,
        "low_confidence_match": 10,
    },
}


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


def _validate_quality_status_record(quality_status_record):
    if not isinstance(quality_status_record, dict):
        raise ValueError(
            "quality_status_record must be a dictionary; got {!r}".format(quality_status_record)
        )
    return build_quality_status(
        quality_status_record.get("artist"),
        quality_status_record.get("title"),
        quality_status_record.get("content_type"),
        quality_status_record.get("content_hash"),
        quality_status_record.get("quality"),
        signals=quality_status_record.get("signals"),
        assessed_at=quality_status_record.get("assessed_at"),
    )


def _base_score_for_quality(quality):
    if quality == "clean":
        return 100
    if quality == "questionable":
        return 70
    if quality == "missing":
        return 0
    raise ValueError("unsupported quality {!r}".format(quality))


def _penalty_for_signal(content_type, signal):
    code = signal.get("code")
    severity = signal.get("severity")
    code_penalties = _SIGNAL_PENALTIES.get(content_type, {})
    if code in code_penalties:
        return code_penalties[code]
    return _DEFAULT_SEVERITY_PENALTIES.get(severity, 0)


def _compose_score_reasons(content_type, quality, signals):
    """Build stable, machine-readable score reason tokens.

    Contract (v1):
      - `score_reasons` is a list of non-empty strings.
      - The first entry is `quality:<quality>` when quality is not `clean`.
      - Remaining entries are `signal:<signal_code>` tokens for signals that
        materially contribute to the score (i.e., signals with a non-zero penalty),
        ordered deterministically by descending penalty then signal code.
    """

    score_reasons = []
    if quality != "clean":
        score_reasons.append("quality:{}".format(quality))

    material_penalties_by_code = {}
    for signal in signals or []:
        code = signal.get("code")
        if not code:
            continue
        penalty = _penalty_for_signal(content_type, signal)
        if penalty <= 0:
            continue
        previous = material_penalties_by_code.get(code)
        if previous is None or penalty > previous:
            material_penalties_by_code[code] = penalty

    ordered_codes = sorted(
        material_penalties_by_code.items(),
        key=lambda item: (-item[1], item[0]),
    )
    for code, _ in ordered_codes:
        score_reasons.append("signal:{}".format(code))

    return score_reasons


def compose_content_score(quality_status_record, scored_at=None):
    validated_record = _validate_quality_status_record(quality_status_record)
    content_type = validated_record["content_type"]
    quality = validated_record["quality"]
    signals = validated_record.get("signals", [])

    if quality == "missing":
        quality_score = 0
    else:
        quality_score = _base_score_for_quality(quality)
        for signal in signals:
            quality_score -= _penalty_for_signal(content_type, signal)
        if quality_score < 0:
            quality_score = 0
        if quality_score > 100:
            quality_score = 100

    score_reasons = _compose_score_reasons(content_type, quality, signals)

    return build_content_score(
        validated_record["artist"],
        validated_record["title"],
        content_type,
        validated_record["content_hash"],
        quality_score,
        score_reasons=score_reasons,
        scored_at=scored_at,
    )


def compose_content_scores(quality_status_records, scored_at=None):
    return [
        compose_content_score(record, scored_at=scored_at)
        for record in quality_status_records or []
    ]


def prioritize_content_scores(content_scores, include_clean=False):
    prioritized = []
    for record in content_scores or []:
        score = build_content_score(
            record.get("artist"),
            record.get("title"),
            record.get("content_type"),
            record.get("content_hash"),
            record.get("quality_score"),
            quality_band=record.get("quality_band"),
            score_version=record.get("score_version", SCORE_VERSION_V1),
            score_reasons=record.get("score_reasons"),
            scored_at=record.get("scored_at"),
        )
        if not include_clean and score["quality_band"] == "clean":
            continue
        prioritized.append(score)

    prioritized.sort(
        key=lambda record: (
            _QUALITY_BAND_PRIORITY[record["quality_band"]],
            record["quality_score"],
            record["song_key"],
            record["content_type"],
        )
    )

    ranked = []
    for index, record in enumerate(prioritized, start=1):
        ranked_record = dict(record)
        ranked_record["priority_rank"] = index
        ranked.append(ranked_record)
    return ranked


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
