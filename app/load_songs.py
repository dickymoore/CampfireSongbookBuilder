"""Load song list from a CSV file with optional skip filtering."""

import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

def load_songs(csv_file: str):
    """Load songs from a CSV file, filtering out rows where 'Skip' equals 'skip'.

    The CSV must contain at least the columns 'Artist' and 'Title'.  An
    optional 'Skip' column indicates rows to exclude; values are compared
    case‑insensitively after stripping whitespace.

    Args:
        csv_file: Path to the CSV file containing the song list.

    Returns:
        A list of dictionaries, each representing a song.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        Exception: If pandas fails to read the file.
    """
    logger.info(f"Loading songs from {csv_file}...")
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Songs CSV file '{csv_file}' does not exist")
    try:
        songs_df = pd.read_csv(csv_file)
        if 'Skip' in songs_df.columns:
            # Filter out rows where Skip equals 'skip' (case insensitive)
            mask = ~songs_df['Skip'].astype(str).str.strip().str.lower().eq('skip')
            songs_df = songs_df[mask]
        else:
            logger.warning("'Skip' column not found in CSV. Proceeding without skipping any songs.")
        songs = songs_df.to_dict('records')
        return songs
    except Exception as e:
        logger.error(f"Failed to load songs: {e}")
        raise