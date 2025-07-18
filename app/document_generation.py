import logging
from app.fetch_data import get_lyrics_from_sources, get_chords_from_sources
from app.cache import jsonl_save_entry, jsonl_load_entry, jsonl_load_all
from app.text_cleaning import clean_lyrics
from app.document_formatting import sort_songs

# Configure logging
logger = logging.getLogger(__name__)

def cache_lyrics(song_list, genius_client):
    logger.info("Caching lyrics...")
    missing_lyrics = []
    missing_lyrics_log = []

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
                logger.debug(f"Lyrics fetched and cached from {source}.")
                found = True
            else:
                jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist, title, "Lyrics not found.", 'lyrics')
                logger.debug("Lyrics not found or too long.")
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
        if cached and cached != "Chords not found.":
            found = True
        else:
            chords, source, tried_log = get_chords_from_sources(title, artist)
            if bool(chords) and chords != "Chords not found.":
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, chords, 'chords')
                logger.debug(f"Chords fetched and cached from {source}.")
                found = True
            else:
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist, title, "Chords not found.", 'chords')
                logger.debug(f"Chords not found for {title} by {artist}.")
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
