import logging

import pandas as pd


logger = logging.getLogger(__name__)


def _is_missing_or_blank(value):
    if pd.isna(value):
        return True
    return isinstance(value, str) and value.strip() == ""


def _is_skipped(value):
    if pd.isna(value):
        return False
    return isinstance(value, str) and value.lower() == "skip"


def _build_invalid_row_record(row_number, row):
    artist = row.get("Artist")
    title = row.get("Title")

    reasons = []
    if _is_missing_or_blank(artist):
        reasons.append("missing artist")
    if _is_missing_or_blank(title):
        reasons.append("missing title")

    return {
        "row_number": row_number,
        "artist": None if _is_missing_or_blank(artist) else artist,
        "title": None if _is_missing_or_blank(title) else title,
        "raw_artist": artist,
        "raw_title": title,
        "skip": row.get("Skip"),
        "reason": " and ".join(reasons),
    }


def load_songs(csv_file):
    """
    Load songs from a CSV file, optionally filtering out rows where 'Skip' is set to 'skip'.

    Parameters:
    csv_file (str): Path to the CSV file containing songs.

    Returns:
    tuple: A pair of lists containing valid songs and invalid row records.
    """
    logger.info("Loading songs from %s...", csv_file)
    try:
        songs_df = pd.read_csv(csv_file)

        songs = []
        invalid_rows = []

        for row_number, row in songs_df.iterrows():
            csv_row_number = int(row_number) + 2
            invalid_record = _build_invalid_row_record(csv_row_number, row)
            if invalid_record["reason"]:
                invalid_rows.append(invalid_record)
                logger.warning("Invalid song row: %s", invalid_record)
                continue

            if 'Skip' in songs_df.columns and _is_skipped(row.get("Skip")):
                continue

            songs.append(row.to_dict())

        if 'Skip' not in songs_df.columns:
            logger.warning("'Skip' column not found in CSV. Proceeding without skipping any songs.")

        return songs, invalid_rows
    except Exception as e:
        logger.error("Failed to load songs: %s", e)
        raise
