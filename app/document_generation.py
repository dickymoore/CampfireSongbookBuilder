import logging
from datetime import datetime

from app.content_models import build_quality_status, compute_content_hash, derive_song_key
from app.content_scoring import compose_content_score
from app.fetch_data import get_lyrics_from_sources, get_chords_from_sources
from app.cache import jsonl_save_entry, jsonl_load_entry, jsonl_load_all
from app.document_formatting import sort_songs
from app.quality_assessment import assess_candidate_quality
from app.review_state import (
    DEFAULT_CONTENT_SCORES_PATH,
    DEFAULT_QUALITY_STATUS_PATH,
    load_content_scores,
    load_quality_status,
    save_content_scores,
    save_quality_status,
)

# Configure logging
logger = logging.getLogger(__name__)

QUALITY_STATUS_PATH = DEFAULT_QUALITY_STATUS_PATH
CONTENT_SCORES_PATH = DEFAULT_CONTENT_SCORES_PATH


def _flatten_quality_status_records(state):
    records = []
    for song_entries in state.get("entries", {}).values():
        records.extend(song_entries.values())
    return records


def _flatten_content_score_records(state):
    records = []
    for song_entries in state.get("entries", {}).values():
        records.extend(song_entries.values())
    return records


def _load_quality_status_record(artist, title, content_type):
    state, errors = load_quality_status(QUALITY_STATUS_PATH)
    if errors:
        logger.warning("Quality status load reported %d recoverable issue(s).", len(errors))
    song_key = derive_song_key(artist, title)
    return state.get("entries", {}).get(song_key, {}).get(content_type)


def _save_quality_status_record(artist, title, content_type, content, quality_result):
    if not isinstance(content, str) or content == "":
        return

    state, errors = load_quality_status(QUALITY_STATUS_PATH)
    if errors:
        logger.warning("Quality status load reported %d recoverable issue(s).", len(errors))

    records = _flatten_quality_status_records(state)
    content_hash = compute_content_hash(content)
    record = build_quality_status(
        artist,
        title,
        content_type,
        content_hash,
        "clean" if quality_result["quality"] == "clean" else "questionable",
        signals=quality_result["signals"],
        assessed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
    )

    filtered_records = [
        existing
        for existing in records
        if not (
            existing.get("song_key") == record["song_key"]
            and existing.get("content_type") == record["content_type"]
        )
    ]
    filtered_records.append(record)
    save_quality_status(QUALITY_STATUS_PATH, filtered_records)

    try:
        content_score_record = compose_content_score(record, scored_at=record.get("assessed_at"))
    except ValueError as exc:
        logger.warning(
            "Failed to compute content score for %s (%s): %s",
            record.get("song_key"),
            record.get("content_type"),
            exc,
        )
        return

    score_state, score_errors = load_content_scores(
        CONTENT_SCORES_PATH,
        current_content_hashes={
            content_score_record["song_key"]: {
                content_score_record["content_type"]: content_score_record["content_hash"]
            }
        },
    )
    if score_errors:
        logger.warning("Content scores load reported %d recoverable issue(s).", len(score_errors))

    score_records = _flatten_content_score_records(score_state)
    filtered_score_records = [
        existing
        for existing in score_records
        if not (
            existing.get("song_key") == content_score_record["song_key"]
            and existing.get("content_type") == content_score_record["content_type"]
        )
    ]
    filtered_score_records.append(content_score_record)
    save_content_scores(
        CONTENT_SCORES_PATH,
        filtered_score_records,
        updated_at=record.get("assessed_at"),
    )


def _assess_cached_content(artist, title, content_type, content):
    return assess_candidate_quality(
        {
            "artist": artist,
            "title": title,
            "content_type": content_type,
            "content": content,
        }
    )


def cache_lyrics(song_list, genius_client):
    logger.info("Caching lyrics...")
    missing_lyrics = []
    missing_lyrics_log = []

    for song in sort_songs(song_list):
        artist = song['Artist']
        title = song['Title']
        found = False
        cached = jsonl_load_entry('data/cache/lyrics_cache.jsonl', artist, title, 'lyrics')
        cached_quality_status = _load_quality_status_record(artist, title, "lyrics")
        if cached and cached != "Lyrics not found.":
            cached_content_hash = compute_content_hash(cached)
            if (
                cached_quality_status
                and cached_quality_status["quality"] == "clean"
                and cached_quality_status.get("content_hash") == cached_content_hash
            ):
                found = True
            else:
                cached_quality = _assess_cached_content(artist, title, "lyrics", cached)
                if cached_quality["quality"] == "clean":
                    _save_quality_status_record(artist, title, "lyrics", cached, cached_quality)
                    found = True
                else:
                    lyrics, source, tried_log, quality_result = get_lyrics_from_sources(title, artist, genius_client)
                    jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist, title, lyrics, 'lyrics')
                    _save_quality_status_record(artist, title, "lyrics", lyrics, quality_result)
                    logger.debug("Lyrics fetched with Questionable quality." if quality_result["quality"] != "clean" else f"Lyrics fetched and cached from {source}.")
                    found = quality_result["quality"] == "clean" or lyrics != "Lyrics not found."
        else:
            lyrics, source, tried_log, quality_result = get_lyrics_from_sources(title, artist, genius_client)
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist, title, lyrics, 'lyrics')
            _save_quality_status_record(artist, title, "lyrics", lyrics, quality_result)
            if quality_result["quality"] == "clean":
                logger.debug(f"Lyrics fetched and cached from {source}.")
            else:
                logger.debug("Lyrics fetched with Questionable quality.")
            found = quality_result["quality"] == "clean" or lyrics != "Lyrics not found."
        if not found:
            missing_lyrics.append(f"{artist} – {title}")
            missing_lyrics_log.append((artist, title, tried_log if not found else []))

    if missing_lyrics:
        print("\nSummary: Missing Lyrics")
        for song in missing_lyrics:
            print(f"- {song}")
        print("\nDetails of sources/queries tried for missing lyrics:")
        for artist, title, tried_log in missing_lyrics_log:
            print(f"{artist} – {title}:")
            for attempt in tried_log:
                print(f"  Tried: {attempt}")
    else:
        print("\nAll lyrics found!")

def cache_chords(song_list):
    logger.info("Caching chords...")
    missing_chords = []
    missing_chords_log = []

    for song in sort_songs(song_list):
        artist = song['Artist']
        title = song['Title']
        found = False
        cached = jsonl_load_entry('data/cache/chords_cache.jsonl', artist, title, 'chords')
        cached_quality_status = _load_quality_status_record(artist, title, "chords")
        if cached and cached != "Chords not found.":
            cached_content_hash = compute_content_hash(cached)
            if (
                cached_quality_status
                and cached_quality_status["quality"] == "clean"
                and cached_quality_status.get("content_hash") == cached_content_hash
            ):
                found = True
            else:
                cached_quality = _assess_cached_content(artist, title, "chords", cached)
                if cached_quality["quality"] == "clean":
                    _save_quality_status_record(artist, title, "chords", cached, cached_quality)
                    found = True
                else:
                    chords, source, tried_log, quality_result = get_chords_from_sources(title, artist)
                    jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, chords, 'chords')
                    _save_quality_status_record(artist, title, "chords", chords, quality_result)
                    logger.debug("Chords fetched with Questionable quality." if quality_result["quality"] != "clean" else f"Chords fetched and cached from {source}.")
                    found = quality_result["quality"] == "clean" or chords != "Chords not found."
        else:
            chords, source, tried_log, quality_result = get_chords_from_sources(title, artist)
            jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, chords, 'chords')
            _save_quality_status_record(artist, title, "chords", chords, quality_result)
            if quality_result["quality"] == "clean":
                logger.debug(f"Chords fetched and cached from {source}.")
            else:
                logger.debug(f"Chords fetched with Questionable quality for {title} by {artist}.")
            found = quality_result["quality"] == "clean" or chords != "Chords not found."
        if not found:
            missing_chords.append(f"{artist} – {title}")
            missing_chords_log.append((artist, title, tried_log if not found else []))

    if missing_chords:
        print("\nSummary: Missing Chords")
        for song in missing_chords:
            print(f"- {song}")
        print("\nDetails of sources/queries tried for missing chords:")
        for artist, title, tried_log in missing_chords_log:
            print(f"{artist} – {title}:")
            for attempt in tried_log:
                print(f"  Tried: {attempt}")
    else:
        print("\nAll chords found!")
