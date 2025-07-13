# import pandas as pd
# import json
import logging
import argparse
from app.load_config import load_config
# from app.document_generation import cache_lyrics, cache_chords
# from app.fetch_data import get_genius_client
# from app.song_info import get_song_lyrics_info
# from app.document_creation import create_document_from_cache
# from app.cache import load_cache

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # Configure logging

def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="generate chord and lyrics documents from a list of songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
    parser.add_argument('--lyrics-only', action='store_true', help='Generate document for lyrics only')
    parser.add_argument('--chords-only', action='store_true', help='Generate document for chords only')
    parser.add_argument('--generate-from-cache', action='store_true', help='Generate documents from cache only')
    args = parser.parse_args()

    match args:
        case argparse.Namespace(get_song_info=True):
            logging.debug("get_song_info")
            load_config('data/config/config.json')
        case argparse.Namespace(generate_from_cache=True):
            logging.info("generate_from_cache")
        case argparse.Namespace(lyrics_only=True):
            logging.info("lyrics_only")
        case argparse.Namespace(chords_only=True):
            logging.info("chords_only")
        case _:
            logging.info("Running in default mode")
    


    # genius_access_token = config['genius']['client_genius_access_token']  # Load the access token for use with genius
    # logging.info("Initializing Genius client...")
    # genius_client = get_genius_client(genius_access_token)

#     if args.get_song_info:
#         song_info = get_song_lyrics_info(songs, genius_client)
#         for title, num_characters in song_info:
#             print(f"{title}: {num_characters} characters")
#     else:
#         lyrics_cache = load_cache('data/cache/lyrics_cache.json')
#         chords_cache = load_cache('data/cache/chords_cache.json')

#         if args.generate_from_cache:
#             logging.info("Generating documents from cache only.")
#             lyrics_output = "data/output/Lyrics_Document.docx" if not args.chords_only else None
#             chords_output = "data/output/Chords_Document.docx" if not args.lyrics_only else None
#             create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output, chords_output)
#         else:
#             if args.lyrics_only:
#                 cache_lyrics(songs, genius_client)
#                 lyrics_output = "data/output/Lyrics_Document.docx"
#                 create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=lyrics_output)
#             elif args.chords_only:
#                 cache_chords(songs)
#                 chords_output = "data/output/Chords_Document.docx"
#                 create_document_from_cache(songs, lyrics_cache, chords_cache, chords_output=chords_output)
#             else:
#                 cache_lyrics(songs, genius_client)
#                 cache_chords(songs)
#                 lyrics_output = "data/output/Lyrics_Document.docx"
#                 chords_output = "data/output/Chords_Document.docx"
#                 create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=lyrics_output, chords_output=chords_output)

if __name__ == "__main__":
    main()
