import logging
from app.fetch_data import get_lyrics_from_genius, get_chords_from_chordie
from app.cache import cache_data, load_cache
from app.text_cleaning import clean_lyrics
from app.document_formatting import sort_songs

# Configure logging
logger = logging.getLogger(__name__)

def cache_lyrics(song_list, genius_client):
    logger.info("Caching lyrics...")
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    sorted_songs = sort_songs(song_list)

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        
        if cache_key not in lyrics_cache or not bool(lyrics_cache[cache_key]) or lyrics_cache[cache_key] == "Lyrics not found.":
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            cleaned_lyrics = clean_lyrics(lyrics)
            num_characters = len(cleaned_lyrics)
            
            if bool(lyrics) and lyrics != "Lyrics not found." and num_characters <= 5000:
                lyrics_cache[cache_key] = lyrics
                logger.debug("Lyrics fetched and cached.")
            else:
                lyrics_cache[cache_key] = "Lyrics not found."
                logger.debug("Lyrics not found or too long.")

            cache_data('data/cache/lyrics_cache.json', lyrics_cache)

def cache_chords(song_list):
    logger.info("Caching chords...")
    chords_cache = load_cache('data/cache/chords_cache.json')
    sorted_songs = sort_songs(song_list)

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"

        if cache_key not in chords_cache or not bool(chords_cache[cache_key]) or chords_cache[cache_key] == "Chords not found.":
            chords = get_chords_from_chordie(title, artist)
            if bool(chords) and chords != "Chords not found.":
                chords_cache[cache_key] = chords
                logger.debug("Chords fetched and cached.")
            else:
                chords_cache[cache_key] = "Chords not found."
                logger.debug("Chords not found.")

            cache_data('data/cache/chords_cache.json', chords_cache)
