import logging
from app.fetch_data import get_lyrics_from_sources, get_chords_from_chordie
from app.cache import cache_data, load_cache
from app.text_cleaning import clean_lyrics
from app.document_formatting import sort_songs

# Configure logging
logger = logging.getLogger(__name__)

def cache_lyrics(song_list, genius_client):
    logger.info("Caching lyrics...")
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    sorted_songs = sort_songs(song_list)
    missing_lyrics = []
    missing_lyrics_log = []

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        found = False
        if cache_key not in lyrics_cache or not bool(lyrics_cache[cache_key]) or lyrics_cache[cache_key] == "Lyrics not found.":
            lyrics, source, tried_log = get_lyrics_from_sources(title, artist, genius_client)
            cleaned_lyrics = clean_lyrics(lyrics)
            num_characters = len(cleaned_lyrics)
            if bool(lyrics) and lyrics != "Lyrics not found." and num_characters <= 5000:
                lyrics_cache[cache_key] = lyrics
                logger.debug(f"Lyrics fetched and cached from {source}.")
                found = True
            else:
                lyrics_cache[cache_key] = "Lyrics not found."
                logger.debug("Lyrics not found or too long.")
        else:
            found = True
        if not found:
            missing_lyrics.append(f"{artist} – {title}")
            missing_lyrics_log.append((artist, title, tried_log))
        cache_data('data/cache/lyrics_cache.json', lyrics_cache)

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
    chords_cache = load_cache('data/cache/chords_cache.json')
    sorted_songs = sort_songs(song_list)
    missing_chords = []

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        found = False
        if cache_key not in chords_cache or not bool(chords_cache[cache_key]) or chords_cache[cache_key] == "Chords not found.":
            chords = get_chords_from_chordie(title, artist)
            if bool(chords) and chords != "Chords not found.":
                chords_cache[cache_key] = chords
                logger.debug(f"Chords fetched and cached for {title} by {artist}.")
                found = True
            else:
                chords_cache[cache_key] = "Chords not found."
                logger.debug(f"Chords not found for {title} by {artist}.")
        else:
            found = True
        if not found:
            missing_chords.append(f"{artist} – {title}")
        cache_data('data/cache/chords_cache.json', chords_cache)

    if missing_chords:
        print("\nSummary: Missing Chords")
        for song in missing_chords:
            print(f"- {song}")
    else:
        print("\nAll chords found!")
