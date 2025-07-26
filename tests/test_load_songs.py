"""Tests for the ``load_songs`` helper.

These tests verify that song loading correctly filters out entries marked
for skipping and that basic error conditions are handled gracefully.
"""

import os
import tempfile
import unittest
import pandas as pd

from CampfireSongbookBuilder.app.load_songs import load_songs


class TestLoadSongs(unittest.TestCase):
    """Unit tests for the ``load_songs`` function."""

    def test_load_songs_filters_skip(self):
        """Rows with 'Skip' equal to 'skip' (case‑insensitive) should be excluded."""
        # Create a temporary CSV file with a mix of skip flags
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as tmp:
            df = pd.DataFrame({
                'Artist': ['ArtistA', 'ArtistB', 'ArtistC', 'ArtistD'],
                'Title': ['Song1', 'Song2', 'Song3', 'Song4'],
                'Skip': ['skip', 'SKIP', '', ' sKiP ']
            })
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        try:
            songs = load_songs(tmp_path)
            # Only the entry with an empty Skip value should be retained
            titles = [s['Title'] for s in songs]
            self.assertIn('Song3', titles)
            self.assertEqual(len(songs), 1)
        finally:
            os.remove(tmp_path)

    def test_load_songs_missing_file(self):
        """An informative exception should be raised if the CSV file is missing."""
        missing_path = '/nonexistent/path/to/songs.csv'
        with self.assertRaises(FileNotFoundError):
            load_songs(missing_path)


if __name__ == '__main__':
    unittest.main()