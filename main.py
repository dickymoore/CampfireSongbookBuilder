import pandas as pd
import json
import logging
from app.generate_documents import generate_documents
from app.fetch_data import get_genius_client

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    songs = songs_df.to_dict('records')
except Exception as e:
    logging.error(f"Failed to load songs: {e}")
    raise

lyrics_output = "data/output/Lyrics_Document.docx"
chords_output = "data/output/Chords_Document.docx"

logging.info("Generating documents...")
generate_documents(songs, genius_client, lyrics_output, chords_output)
logging.info("Documents generated successfully.")
