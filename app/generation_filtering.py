import copy

from app.content_models import compute_content_hash, derive_song_key
from app.quality_assessment import assess_candidate_quality


def build_current_content_hashes(lyrics_cache=None, chords_cache=None):
    current_content_hashes = {}

    for content_type, cache in (("lyrics", lyrics_cache), ("chords", chords_cache)):
        if not isinstance(cache, dict):
            continue

        for song_key, content in cache.items():
            if not isinstance(content, str) or content == "":
                continue

            current_content_hashes.setdefault(song_key, {})[content_type] = compute_content_hash(
                content
            )

    return current_content_hashes


def _current_quality_status(artist, title, content_type, content, quality_status_record=None):
    song_key = derive_song_key(artist, title)
    current_content_hash = None
    if isinstance(content, str) and content != "":
        current_content_hash = compute_content_hash(content)

    if (
        isinstance(quality_status_record, dict)
        and quality_status_record.get("song_key") == song_key
        and quality_status_record.get("content_type") == content_type
        and quality_status_record.get("content_hash") == current_content_hash
    ):
        return copy.deepcopy(quality_status_record), "cached_quality_status", current_content_hash

    assessment = assess_candidate_quality(
        {
            "artist": artist,
            "title": title,
            "content_type": content_type,
            "content": content,
        }
    )
    return (
        {
            "artist": artist,
            "title": title,
            "song_key": song_key,
            "content_type": content_type,
            "content_hash": current_content_hash,
            "quality": assessment["quality"],
            "signals": copy.deepcopy(assessment["signals"]),
            "summary": copy.deepcopy(assessment["summary"]),
        },
        "current_assessment",
        current_content_hash,
    )


def _current_review_decision(
    song_key,
    content_type,
    current_content_hash,
    review_decision_record=None,
):
    if not isinstance(review_decision_record, dict):
        return None

    if current_content_hash is None:
        return None

    if (
        review_decision_record.get("song_key") != song_key
        or review_decision_record.get("content_type") != content_type
        or review_decision_record.get("content_hash") != current_content_hash
    ):
        return None

    return copy.deepcopy(review_decision_record)


def evaluate_cached_content(
    artist,
    title,
    content_type,
    content,
    quality_status_record=None,
    review_decision_record=None,
):
    quality_status, quality_source, current_content_hash = _current_quality_status(
        artist,
        title,
        content_type,
        content,
        quality_status_record=quality_status_record,
    )
    song_key = quality_status["song_key"]
    review_decision = _current_review_decision(
        song_key,
        content_type,
        current_content_hash,
        review_decision_record=review_decision_record,
    )

    decision = review_decision.get("decision") if review_decision is not None else None
    quality = quality_status["quality"]

    if decision == "reject":
        included = False
        decision_source = "review_reject"
        reason = "Current review decision rejects this content."
    elif quality == "clean":
        included = True
        decision_source = "quality_clean" if decision is None else "review_{}".format(decision)
        reason = "Content passed quality checks."
    elif quality == "questionable" and decision in {"accept", "override"}:
        included = True
        decision_source = "review_{}".format(decision)
        reason = "Questionable content explicitly allowed by a current review decision."
    elif quality == "missing":
        included = False
        decision_source = "quality_missing"
        reason = "Missing content is excluded by default."
    else:
        included = False
        decision_source = "default_exclude"
        reason = "Questionable content is excluded by default."

    return {
        "song_key": song_key,
        "content_type": content_type,
        "content_hash": current_content_hash,
        "quality": quality,
        "included": included,
        "decision_source": decision_source,
        "reason": reason,
        "signals": copy.deepcopy(quality_status["signals"]),
        "quality_status": quality_status,
        "quality_status_source": quality_source,
        "review_decision": review_decision,
    }
