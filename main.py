import pandas as pd
import json
from app.generate_documents import generate_documents
from app.fetch_data import get_access_token

# Load configuration
with open('data/config/config.json', 'r') as config_file:
    config = json.load(config_file)

client_id = config['genius']['client_id']
client_secret = config['genius']['client_secret']

# Get access token
access_token = get_access_token(client_id, client_secret)

# Load songs from CSV file
csv_file = 'data/src/CampfireSongs.csv'
songs_df = pd.read_csv(csv_file)
songs = songs_df.to_dict('records')

lyrics_output = "Lyrics_Document.docx"
chords_output = "Chords_Document.docx"

generate_documents(songs, access_token, lyrics_output, chords_output)
