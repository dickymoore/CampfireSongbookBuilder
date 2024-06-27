import pandas as pd
import json
import logging
import argparse
from app.document_generation import cache_lyrics, cache_chords
from app.fetch_data import get_genius_client
from app.song_info import get_song_lyrics_info
from app.document_creation import create_document_from_cache
from app.cache import load_cache

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Process some songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
    parser.add_argument('--lyrics-only', action='store_true', help='Generate document for lyrics only')
    parser.add_argument('--chords-only', action='store_true', help='Generate document for chords only')
    parser.add_argument('--generate-from-cache', action='store_true', help='Generate documents from cache only')
    args = parser.parse_args()

    # Load configuration
    logging.info("Loading configuration...")
    with open('data/config/config.json', 'r') as config_file:
        config = json.load(config_file)

    access_token = config['genius']['client_access_token']

    # Initialize Genius client
    logging.info("Initializing Genius client...")
    genius_client = get_genius_client(access_token)

    # Load songs from CSV file
    csv_file = 'data/src/CampfireSongs.csv'
    logging.info(f"Loading songs from {csv_file}...")
    try:
        songs_df = pd.read_csv(csv_file)
        
        # Check if 'Skip' column exists and filter out rows where 'Skip' is set to 'skip'
        if 'Skip' in songs_df.columns:
            songs_df = songs_df[songs_df['Skip'].str.lower() != 'skip']
        else:
            logging.warning("'Skip' column not found in CSV. Proceeding without skipping any songs.")
        
        songs = songs_df.to_dict('records')
    except Exception as e:
        logging.error(f"Failed to load songs: {e}")
        raise

    if args.get_song_info:
        song_info = get_song_lyrics_info(songs, genius_client)
        for title, num_characters in song_info:
            print(f"{title}: {num_characters} characters")
    else:
        lyrics_cache = load_cache('data/cache/lyrics_cache.json')
        chords_cache = load_cache('data/cache/chords_cache.json')

        if args.generate_from_cache:
            logging.info("Generating documents from cache only.")
            lyrics_output = "data/output/Lyrics_Document.docx" if args.lyrics_only else None
            chords_output = "data/output/Chords_Document.docx" if args.chords_only else None
            create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=lyrics_output, chords_output=chords_output)
        else:
            if args.lyrics_only:
                cache_lyrics(songs, genius_client)
                lyrics_output = "data/output/Lyrics_Document.docx"
                create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=lyrics_output)
            elif args.chords_only:
                cache_chords(songs)
                chords_output = "data/output/Chords_Document.docx"
                create_document_from_cache(songs, lyrics_cache, chords_cache, chords_output=chords_output)
            else:
                cache_lyrics(songs, genius_client)
                cache_chords(songs)
                lyrics_output = "data/output/Lyrics_Document.docx"
                chords_output = "data/output/Chords_Document.docx"
                create_document_from_cache(songs, lyrics_cache, chords_cache, lyrics_output=lyrics_output, chords_output=chords_output)

if __name__ == "__main__":
    main()
