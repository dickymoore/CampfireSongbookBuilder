from docx import Document
import logging
from app.document_formatting import set_document_margins, set_paragraph_font, create_two_column_section, add_header_footer, sort_songs
from app.text_cleaning import clean_lyrics, clean_chords

# Configure logging
logger = logging.getLogger(__name__)

def create_document_from_cache(song_list, lyrics_cache, chords_cache, lyrics_output=None, chords_output=None):
    if lyrics_output:
        lyrics_document = Document()
        set_document_margins(lyrics_document, 0.5)
        create_two_column_section(lyrics_document)
        add_header_footer(lyrics_document)

    if chords_output:
        chords_document = Document()
        set_document_margins(chords_document, 0.5)
        create_two_column_section(chords_document)  # Add this line to ensure two-column layout for chords
        add_header_footer(chords_document)

    sorted_songs = sort_songs(song_list)

    for song in sorted_songs:
        artist = song['Artist']
        title = song['Title']
        cache_key = f"{artist} - {title}"

        if lyrics_output and cache_key in lyrics_cache and bool(lyrics_cache[cache_key]):
            lyrics = clean_lyrics(lyrics_cache[cache_key])
            num_characters = len(lyrics)
            
            if num_characters <= 5000:
                heading = lyrics_document.add_heading(f"{title} by {artist}", level=1)
                set_paragraph_font(heading, 14)
                paragraph = lyrics_document.add_paragraph(lyrics)
                set_paragraph_font(paragraph, 12)
            else:
                logger.debug(f"Lyrics for {title} are too long and have been excluded.")

        if chords_output and cache_key in chords_cache and bool(chords_cache[cache_key]):
            chords = clean_chords(chords_cache[cache_key])
            heading = chords_document.add_heading(f"{title} by {artist}", level=1)
            set_paragraph_font(heading, 14)
            paragraph = chords_document.add_paragraph(chords)
            set_paragraph_font(paragraph, 12)

    if lyrics_output:
        lyrics_document.save(lyrics_output)
        logger.info(f"Lyrics document saved as {lyrics_output}.")

    if chords_output:
        chords_document.save(chords_output)
        logger.info(f"Chords document saved as {chords_output}.")
