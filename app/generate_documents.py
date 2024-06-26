from docx import Document
import time
import logging
from app.fetch_data import get_lyrics_from_genius
from app.cache import cache_data, load_cache

# Configure logging
logger = logging.getLogger(__name__)

def remove_contributors_and_embeds(document):
    """Remove paragraphs containing 'Contributors' and 'Embed' from the document."""
    new_doc = Document()
    for para in document.paragraphs:
        if "Contributors" not in para.text and "Embed" not in para.text:
            new_doc.add_paragraph(para.text)
    return new_doc

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
            cache_data('data/cache/lyrics_cache.json', lyrics_cache)  # Update the cache file immediately
            logger.debug("Lyrics fetched and cached.")

        lyrics_document.add_heading(f"{title} by {artist}", level=1)
        lyrics_document.add_paragraph(lyrics)
        lyrics_document.add_page_break()

        # chords_document.add_heading(f"{title} by {artist}", level=1)
        # chords_document.add_paragraph(chords)
        # chords_document.add_page_break()

        time.sleep(5)

    # Remove Contributors and Embed sections before saving
    cleaned_lyrics_document = remove_contributors_and_embeds(lyrics_document)
    cleaned_lyrics_document.save(lyrics_output)
    logger.info(f"Lyrics document saved as {lyrics_output}.")

    # chords_document.save(chords_output)
    # logger.info(f"Chords document saved as {chords_output}.")

if __name__ == "__main__":
    # Example usage
    song_list = [
        {'Artist': 'Artist1', 'Title': 'Song1'},
        {'Artist': 'Artist2', 'Title': 'Song2'}
    ]
    genius_client = get_genius_client('your_access_token')
    generate_documents(song_list, genius_client, 'output/Lyrics_Document.docx', 'output/Chords_Document.docx')
