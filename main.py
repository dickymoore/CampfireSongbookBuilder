import pandas as pd
import json
from app.generate_documents import generate_documents

# Load configuration
with open('data/config/config.json', 'r') as config_file:
    config = json.load(config_file)

api_key = config['genius']['api_key']

# Load songs from CSV file
csv_file = 'data/src/songs.csv'
songs_df = pd.read_csv(csv_file)
songs = songs_df.to_dict('records')

lyrics_output = "Lyrics_Document.docx"
chords_output = "Chords_Document.docx"

generate_documents(songs, api_key, lyrics_output, chords_output)
