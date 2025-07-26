"""Entry point for the Campfire Songbook Builder CLI."""

import logging
import argparse
import sys
from app.load_config import load_config
from app.load_songs import load_songs
from app.document_generation import cache_lyrics, cache_chords
from app.fetch_data import get_genius_client
from app.song_info import get_song_lyrics_info

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_PATH = 'data/config/config.json'
SONGS_CSV_PATH = 'data/src/CampfireSongs.csv'
LYRICS_CACHE_PATH = 'data/cache/lyrics_cache.jsonl'
CHORDS_CACHE_PATH = 'data/cache/chords_cache.jsonl'
LYRICS_DOC_PATH = 'data/output/Lyrics_Document.docx'
CHORDS_DOC_PATH = 'data/output/Chords_Document.docx'

def test_genius_api(genius_client) -> bool:
    """Test the Genius API key by searching for a well‑known song."""
    try:
        song = genius_client.search_song("Imagine", "John Lennon")
        if song:
            print("Genius API key is valid! Example search succeeded: Found song:", song.title)
            return True
        else:
            print("Genius API key appears valid, but test song not found.")
            return False
    except Exception as e:
        print("Genius API key test failed:", e)
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate chord and lyrics documents from a list of songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
    parser.add_argument('--lyrics-only', action='store_true', help='Generate document for lyrics only')
    parser.add_argument('--chords-only', action='store_true', help='Generate document for chords only')
    parser.add_argument('--generate-from-cache', action='store_true', help='Generate documents from cache only')
    parser.add_argument('--test-api', action='store_true', help='Test the Genius API key')
    parser.add_argument('--cache-only', action='store_true', help='Fetch and cache all lyrics and chords, but do not generate documents')
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(CONFIG_PATH)
        genius_access_token = config['genius']['client_access_token']
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Initialise genius client.  In offline environments this may still
    # initialise successfully, but API calls will fail.
    try:
        genius_client = get_genius_client(genius_access_token)
    except Exception as e:
        logging.error(f"Failed to initialise Genius client: {e}")
        genius_client = None

    if args.test_api:
        test_genius_api(genius_client)
        return

    # Load songs
    try:
        songs = load_songs(SONGS_CSV_PATH)
    except Exception as e:
        logging.error(f"Failed to load songs: {e}")
        sys.exit(1)

    if args.cache_only:
        logging.info("Caching all lyrics and chords for the song list (no document generation)...")
        cache_lyrics(songs, genius_client)
        cache_chords(songs)
        logging.info("Caching complete.")
        return

    if args.get_song_info:
        song_info = get_song_lyrics_info(songs, genius_client)
        for title, num_characters in song_info:
            print(f"{title}: {num_characters} characters")
        return

    if args.generate_from_cache:
        logging.info("Generating documents from cache only.")
        lyrics_output = LYRICS_DOC_PATH if not args.chords_only else None
        chords_output = CHORDS_DOC_PATH if not args.lyrics_only else None
        from app.cache import jsonl_load_all
        lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
        chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
        from app.document_creation import create_document_from_cache
        create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output, chords_output)
        return

    if args.lyrics_only:
        cache_lyrics(songs, genius_client)
        from app.cache import jsonl_load_all
        lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
        from app.document_creation import create_document_from_cache
        create_document_from_cache(songs, lyrics_cache, {}, lyrics_output=LYRICS_DOC_PATH)
        return

    if args.chords_only:
        cache_chords(songs)
        from app.cache import jsonl_load_all
        chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
        from app.document_creation import create_document_from_cache
        create_document_from_cache(songs, {}, chords_cache, chords_output=CHORDS_DOC_PATH)
        return

    # Default: cache both and generate both docs
    cache_lyrics(songs, genius_client)
    cache_chords(songs)
    from app.cache import jsonl_load_all
    lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
    chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
    from app.document_creation import create_document_from_cache
    create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=LYRICS_DOC_PATH, chords_output=CHORDS_DOC_PATH)

if __name__ == "__main__":
    main()