"""Helper for reporting information about songs from the lyrics cache."""

import logging
from .fetch_data import get_lyrics_from_genius
from .cache import jsonl_load_entry, jsonl_load_all
from .text_cleaning import clean_lyrics
from .document_formatting import sort_songs

logger = logging.getLogger(__name__)

def get_song_lyrics_info(song_list, genius_client):
    """Return a list of (title, character_count) for the given songs.

    Lyrics are loaded from the cache if available; otherwise they are fetched
    from Genius via the provided client.  Very long lyrics are excluded.

    Args:
        song_list: List of dictionaries containing at least 'Artist' and 'Title'.
        genius_client: A ``lyricsgenius.Genius`` client or compatible stub.

    Returns:
        A list of tuples: (song title, number of characters in cleaned lyrics).
    """
    lyrics_cache = jsonl_load_all('data/cache/lyrics_cache.jsonl', 'lyrics')
    song_info: list[tuple[str, int]] = []
    sorted_songs = sort_songs(song_list)
    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        if cache_key in lyrics_cache and bool(lyrics_cache[cache_key]) and lyrics_cache[cache_key] != "Lyrics not found.":
            lyrics = lyrics_cache[cache_key]
            logger.debug("Lyrics loaded from cache for %s by %s.", title, artist)
        else:
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            cleaned_lyrics = clean_lyrics(lyrics)
            num_characters = len(cleaned_lyrics)
            if bool(lyrics) and lyrics != "Lyrics not found." and num_characters <= 5000:
                logger.debug("Lyrics fetched and cached for %s by %s.", title, artist)
            else:
                lyrics = "Lyrics not found."
                logger.debug("Lyrics not found or too long for %s by %s.", title, artist)
        cleaned_lyrics = clean_lyrics(lyrics)
        num_characters = len(cleaned_lyrics)
        song_info.append((title, num_characters))
    return song_info