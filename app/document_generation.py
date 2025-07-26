"""Functions to populate the cache by fetching lyrics and chords from multiple sources.

These functions iterate over the provided song list, attempt to retrieve
lyrics/chords from a series of sources (Genius, Lyrics.ovh, AZLyrics for
lyrics and Chordie, Ultimate Guitar, E‑Chords, Songsterr and Yousician for
chords) and write the results to the JSONL cache.  A summary of songs for
which data could not be found is printed to stdout.

The environment this project runs in may not have outbound network access.
Fetching will gracefully handle request failures and record missing items.
"""

import logging
from .fetch_data import get_lyrics_from_sources, get_chords_from_sources
from .cache import jsonl_save_entry, jsonl_load_entry, jsonl_load_all
from .text_cleaning import clean_lyrics
from .document_formatting import sort_songs

logger = logging.getLogger(__name__)

def cache_lyrics(song_list, genius_client) -> None:
    """Fetch and cache lyrics for the supplied songs.

    For each song the function first consults the cache.  If the lyrics are
    present and not marked as "Lyrics not found." they are considered valid.
    Otherwise the function attempts to fetch the lyrics from multiple sources
    (see ``get_lyrics_from_sources``).  Long lyrics (>5,000 characters) are
    skipped as they usually indicate an error page.  A summary of missing
    lyrics is printed on completion.

    Args:
        song_list: List of dictionaries with ``'Artist'`` and ``'Title'`` keys.
        genius_client: An authenticated ``lyricsgenius.Genius`` client or a
            compatible stub for testing.  The argument is still required to
            preserve backward compatibility, although some environments may not
            support external API calls.
    """
    logger.info("Caching lyrics...")
    missing_lyrics: list[str] = []
    missing_lyrics_log: list[tuple[str, str, list[str]]] = []
    for song in sort_songs(song_list):
        artist = song['Artist']
        title = song['Title']
        found = False
        cached = jsonl_load_entry('data/cache/lyrics_cache.jsonl', artist, title, 'lyrics')
        if cached and cached != "Lyrics not found.":
            found = True
        else:
            lyrics, source, tried_log = get_lyrics_from_sources(title, artist, genius_client)
            cleaned_lyrics = clean_lyrics(lyrics)
            num_characters = len(cleaned_lyrics)
            if bool(lyrics) and lyrics != "Lyrics not found." and num_characters <= 5000:
                jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist, title, lyrics, 'lyrics')
                logger.debug("Lyrics fetched and cached from %s.", source)
                found = True
            else:
                jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist, title, "Lyrics not found.", 'lyrics')
                logger.debug("Lyrics not found or too long for %s by %s.", title, artist)
        if not found:
            missing_lyrics.append(f"{artist} – {title}")
            missing_lyrics_log.append((artist, title, tried_log if not found else []))
    # Print summary
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

def cache_chords(song_list) -> None:
    """Fetch and cache chords for the supplied songs.

    The function uses ``get_chords_from_sources`` to try multiple chord
    providers.  It records missing chords and prints a summary at the end.

    Args:
        song_list: List of dictionaries with ``'Artist'`` and ``'Title'`` keys.
    """
    logger.info("Caching chords...")
    missing_chords: list[str] = []
    missing_chords_log: list[tuple[str, str, list[str]]] = []
    for song in sort_songs(song_list):
        artist = song['Artist']
        title = song['Title']
        found = False
        cached = jsonl_load_entry('data/cache/chords_cache.jsonl', artist, title, 'chords')
        if cached and cached != "Chords not found.":
            found = True
        else:
            chords, source, tried_log = get_chords_from_sources(title, artist)
            if bool(chords) and chords != "Chords not found.":
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, chords, 'chords')
                logger.debug("Chords fetched and cached from %s.", source)
                found = True
            else:
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, "Chords not found.", 'chords')
                logger.debug("Chords not found for %s by %s.", title, artist)
        if not found:
            missing_chords.append(f"{artist} – {title}")
            missing_chords_log.append((artist, title, tried_log if not found else []))
    # Print summary
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