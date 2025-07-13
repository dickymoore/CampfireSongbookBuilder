import pandas as pd
import logging

def load_songs(csv_file):
    """
    Load songs from a CSV file, optionally filtering out rows where 'Skip' is set to 'skip'.
    
    Parameters:
    csv_file (str): Path to the CSV file containing songs.

    Returns:
    list: A list of dictionaries, each representing a song.
    """
    logging.info(f"Loading songs from {csv_file}...")
    try:
        songs_df = pd.read_csv(csv_file)
        
        # Check if 'Skip' column exists and filter out rows where 'Skip' is set to 'skip'
        if 'Skip' in songs_df.columns:
            songs_df = songs_df[songs_df['Skip'].str.lower() != 'skip']
        else:
            logging.warning("'Skip' column not found in CSV. Proceeding without skipping any songs.")
        
        songs = songs_df.to_dict('records')
        return songs
    except Exception as e:
        logging.error(f"Failed to load songs: {e}")
        raise
