from docx import Document
import time
import logging
from app.fetch_data import get_lyrics_from_genius
from app.cache import cache_data, load_cache

# Configure logging
logger = logging.getLogger(__name__)

def generate_documents(song_list, genius_client, lyrics_output, chords_output):
    logger.info("Loading cache data...")
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    chords_cache = load_cache('data/cache/chords_cache.json')

    lyrics_document = Document()
    chords_document = Document()

    for song in sorted(song_list, key=lambda x: x['Title']):
        artist = song['Artist']
        title = song['Title']
        logger.debug(f"Processing {title} by {artist}...")

        cache_key = f"{artist} - {title}"
        if cache_key in lyrics_cache:
            lyrics = lyrics_cache[cache_key]
            logger.debug("Lyrics loaded from cache.")
        else:
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            lyrics_cache[cache_key] = lyrics
            logger.debug("Lyrics fetched and cached.")

        # if cache_key in chords_cache:
        #     chords = chords_cache[cache_key]
        #     logger.debug("Chords loaded from cache.")
        # else:
        #     chords = get_chords_from_ultimate_guitar(title, artist)
        #     chords_cache[cache_key] = chords
        #     logger.debug("Chords fetched and cached.")

        lyrics_document.add_heading(f"{title} by {artist}", level=1)
        lyrics_document.add_paragraph(lyrics)
        lyrics_document.add_page_break()

        # chords_document.add_heading(f"{title} by {artist}", level=1)
        # chords_document.add_paragraph(chords)
        # chords_document.add_page_break()

        time.sleep(5)

    lyrics_document.save(lyrics_output)
    logger.info(f"Lyrics document saved as {lyrics_output}.")
    # chords_document.save(chords_output)
    # logger.info(f"Chords document saved as {chords_output}.")

    cache_data('data/cache/lyrics_cache.json', lyrics_cache)
    logger.info("Lyrics cache updated.")
    # cache_data('data/cache/chords_cache.json', chords_cache)
    # logger.info("Chords cache updated.")
