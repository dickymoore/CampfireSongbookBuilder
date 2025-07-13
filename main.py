import logging
import argparse
import sys
from app.load_config import load_config
from app.load_songs import load_songs
from app.document_generation import cache_lyrics, cache_chords
from app.fetch_data import get_genius_client
from app.song_info import get_song_lyrics_info
from app.document_creation import create_document_from_cache
from app.cache import load_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_PATH = 'data/config/config.json'
SONGS_CSV_PATH = 'data/src/CampfireSongs.csv'
LYRICS_CACHE_PATH = 'data/cache/lyrics_cache.json'
CHORDS_CACHE_PATH = 'data/cache/chords_cache.json'
LYRICS_DOC_PATH = 'data/output/Lyrics_Document.docx'
CHORDS_DOC_PATH = 'data/output/Chords_Document.docx'

def main():
    parser = argparse.ArgumentParser(description="Generate chord and lyrics documents from a list of songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
    parser.add_argument('--lyrics-only', action='store_true', help='Generate document for lyrics only')
    parser.add_argument('--chords-only', action='store_true', help='Generate document for chords only')
    parser.add_argument('--generate-from-cache', action='store_true', help='Generate documents from cache only')
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(CONFIG_PATH)
        if not config or 'genius' not in config or 'client_access_token' not in config['genius']:
            raise ValueError("Missing 'genius' or 'client_access_token' in config file.")
        genius_access_token = config['genius']['client_access_token']
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Load songs
    try:
        songs = load_songs(SONGS_CSV_PATH)
    except Exception as e:
        logging.error(f"Failed to load songs: {e}")
        sys.exit(1)

    genius_client = get_genius_client(genius_access_token)

    if args.get_song_info:
        song_info = get_song_lyrics_info(songs, genius_client)
        for title, num_characters in song_info:
            print(f"{title}: {num_characters} characters")
        return

    lyrics_cache = load_cache(LYRICS_CACHE_PATH)
    chords_cache = load_cache(CHORDS_CACHE_PATH)

    if args.generate_from_cache:
        logging.info("Generating documents from cache only.")
        lyrics_output = LYRICS_DOC_PATH if not args.chords_only else None
        chords_output = CHORDS_DOC_PATH if not args.lyrics_only else None
        create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output, chords_output)
        return

    if args.lyrics_only:
        cache_lyrics(songs, genius_client)
        lyrics_cache = load_cache(LYRICS_CACHE_PATH)
        create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=LYRICS_DOC_PATH)
        return

    if args.chords_only:
        cache_chords(songs)
        chords_cache = load_cache(CHORDS_CACHE_PATH)
        create_document_from_cache(songs, lyrics_cache, chords_cache, chords_output=CHORDS_DOC_PATH)
        return

    # Default: cache both and generate both docs
    cache_lyrics(songs, genius_client)
    cache_chords(songs)
    lyrics_cache = load_cache(LYRICS_CACHE_PATH)
    chords_cache = load_cache(CHORDS_CACHE_PATH)
    create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=LYRICS_DOC_PATH, chords_output=CHORDS_DOC_PATH)

if __name__ == "__main__":
    main()
