from docx import Document
import re
import logging
from app.fetch_data import get_lyrics_from_genius
from app.cache import cache_data, load_cache

# Configure logging
logger = logging.getLogger(__name__)

def remove_contributors_and_embeds(lyrics):
    lyrics = re.sub(r'^.*Contributors', '', lyrics, flags=re.DOTALL)
    lyrics = re.sub(r'Embed\s*$', '', lyrics, flags=re.MULTILINE)
    return lyrics

def get_song_lyrics_info(song_list, genius_client):
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    song_info = []

    for song in sorted(song_list, key=lambda x: x['Title']):
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"
        
        if cache_key in lyrics_cache and bool(lyrics_cache[cache_key]) and lyrics_cache[cache_key] != "Lyrics not found.":
            lyrics = lyrics_cache[cache_key]
        else:
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            if bool(lyrics) and lyrics != "Lyrics not found.":
                lyrics_cache[cache_key] = lyrics
                cache_data('data/cache/lyrics_cache.json', lyrics_cache)  # Update the cache file immediately
            else:
                lyrics = "Lyrics not found."

        cleaned_lyrics = remove_contributors_and_embeds(lyrics)
        num_characters = len(cleaned_lyrics)
        song_info.append((title, num_characters))

    return song_info

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
            if bool(lyrics):
                logger.debug("Lyrics loaded from cache.")
            else: 
                logger.debug("Attampt to load lyrics from cache failed.")
        else:
            lyrics = get_lyrics_from_genius(title, artist, genius_client)
            if lyrics and lyrics != "Lyrics not found.":
                lyrics_cache[cache_key] = lyrics
                cache_data('data/cache/lyrics_cache.json', lyrics_cache)  # Update the cache file immediately
                logger.debug("Lyrics fetched and cached.")
            else:
                lyrics = "Lyrics not found."
                logger.debug("Lyrics not found.")

        cleaned_lyrics = remove_contributors_and_embeds(lyrics)
        lyrics_document.add_heading(f"{title} by {artist}", level=1)
        # table = lyrics_document.add_table(rows=1, cols=1)
        # row = table.rows[0]
        # cell_lyrics = row.cells[0]
        # cell_lyrics.text = cleaned_lyrics
        lyrics_document.add_paragraph(cleaned_lyrics)
        # lyrics_document.add_page_break()

        # chords_document.add_heading(f"{title} by {artist}", level=1)
        # chords_document.add_paragraph(chords)
        # chords_document.add_page_break()
    lyrics_document.save(lyrics_output)
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
