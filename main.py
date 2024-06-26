import pandas as pd
import json
import logging
from app.generate_documents import generate_documents
from app.fetch_data import get_access_token

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
logging.info("Loading configuration...")
with open('data/config/config.json', 'r') as config_file:
    config = json.load(config_file)

website_url = config['genius']['website_url']
client_id = config['genius']['client_id']
client_secret = config['genius']['client_secret']

# Get access token
logging.info("Getting access token...")
try:
    access_token = get_access_token(website_url, client_id, client_secret)
except Exception as e:
    logging.error(f"Failed to get access token: {e}")
    raise

# Load songs from CSV file
csv_file = 'data/src/CampfireSongs.csv'
logging.info(f"Loading songs from {csv_file}...")
try:
    songs_df = pd.read_csv(csv_file)
    songs = songs_df.to_dict('records')
except Exception as e:
    logging.error(f"Failed to load songs: {e}")
    raise

lyrics_output = "Lyrics_Document.docx"
chords_output = "Chords_Document.docx"

logging.info("Generating documents...")
generate_documents(songs, access_token, lyrics_output, chords_output)
logging.info("Documents generated successfully.")
