import pandas as pd
import json
import logging
import argparse
from app.generate_documents import generate_documents, get_song_lyrics_info
from app.fetch_data import get_genius_client

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Process some songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
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
        lyrics_output = "data/output/Lyrics_Document.docx"
        chords_output = "data/output/Chords_Document.docx"
        
        logging.info("Generating documents...")
        generate_documents(songs, genius_client, lyrics_output, chords_output)
        logging.info("Documents generated successfully.")

if __name__ == "__main__":
    main()
