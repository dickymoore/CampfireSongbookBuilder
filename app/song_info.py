import logging
from app.fetch_data import get_lyrics_from_genius
from app.cache import cache_data, load_cache
from app.text_cleaning import clean_lyrics
from app.document_formatting import sort_songs

# Configure logging
logger = logging.getLogger(__name__)

def get_song_lyrics_info(song_list, genius_client):
    """Get song titles and the character length of the lyrics for those songs."""
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    song_info = []

    sorted_songs = sort_songs(song_list)

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        
        if cache_key in lyrics_cache and bool(lyrics_cache[cache_key]) and lyrics_cache[cache_key] != "Lyrics not found.":
            lyrics = lyrics_cache[cache_key]
            logger.debug("Lyrics loaded from cache.")
        else:
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            cleaned_lyrics = clean_lyrics(lyrics)
            num_characters = len(cleaned_lyrics)
            
            if bool(lyrics) and lyrics != "Lyrics not found." and num_characters <= 5000:
                lyrics_cache[cache_key] = lyrics
                cache_data('data/cache/lyrics_cache.json', lyrics_cache)  # Update the cache file immediately
                logger.debug("Lyrics fetched and cached.")
            else:
                lyrics = "Lyrics not found."
                logger.debug("Lyrics not found or too long.")

        cleaned_lyrics = clean_lyrics(lyrics)
        num_characters = len(cleaned_lyrics)
        song_info.append((title, num_characters))

    return song_info
