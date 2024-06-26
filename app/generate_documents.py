from docx import Document
import time
from app.fetch_data import get_lyrics_from_genius, get_chords_from_ultimate_guitar
from app.cache import cache_data, load_cache

def generate_documents(song_list, access_token, lyrics_output, chords_output):
    lyrics_cache = load_cache('data/cache/lyrics_cache.json')
    chords_cache = load_cache('data/cache/chords_cache.json')

    lyrics_document = Document()
    chords_document = Document()

    for song in sorted(song_list, key=lambda x: x['Title']):
        artist = song['Artist']
        title = song['Title']

        cache_key = f"{artist} - {title}"
        if cache_key in lyrics_cache:
            lyrics = lyrics_cache[cache_key]
        else:
            lyrics = get_lyrics_from_genius(title, artist, access_token)
            lyrics_cache[cache_key] = lyrics

        # if cache_key in chords_cache:
        #     chords = chords_cache[cache_key]
        # else:
        #     chords = get_chords_from_ultimate_guitar(title, artist)
        #     chords_cache[cache_key] = chords

        lyrics_document.add_heading(f"{title} by {artist}", level=1)
        lyrics_document.add_paragraph(lyrics)
        lyrics_document.add_page_break()

        # chords_document.add_heading(f"{title} by {artist}", level=1)
        # chords_document.add_paragraph(chords)
        # chords_document.add_page_break()

        time.sleep(5)

    lyrics_document.save(lyrics_output)
    # chords_document.save(chords_output)

    cache_data('data/cache/lyrics_cache.json', lyrics_cache)
    # cache_data('data/cache/chords_cache.json', chords_cache)