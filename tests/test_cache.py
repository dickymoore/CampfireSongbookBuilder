"""Tests for the cache helper functions.

These tests ensure that JSONL cache files are read and written correctly
and that existing entries are updated rather than duplicated.
"""

import json
import os
import tempfile
import unittest

from CampfireSongbookBuilder.app.cache import (
    jsonl_load_entry,
    jsonl_save_entry,
    jsonl_load_all,
)


class TestCacheHelpers(unittest.TestCase):
    """Unit tests for JSONL cache helpers."""

    def test_save_and_load_entry(self):
        """Entries saved to the cache should be retrievable by artist and title."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as tmp:
            cache_path = tmp.name
        try:
            # Save a new entry
            jsonl_save_entry(cache_path, 'Artist', 'Title', 'Some lyrics', 'lyrics')
            # Load the entry back
            value = jsonl_load_entry(cache_path, 'Artist', 'Title', 'lyrics')
            self.assertEqual(value, 'Some lyrics')
            # Update the existing entry
            jsonl_save_entry(cache_path, 'Artist', 'Title', 'Updated lyrics', 'lyrics')
            value2 = jsonl_load_entry(cache_path, 'Artist', 'Title', 'lyrics')
            self.assertEqual(value2, 'Updated lyrics')
            # Only one entry should exist in the file
            with open(cache_path, 'r', encoding='utf-8') as f:
                lines = list(f)
            self.assertEqual(len(lines), 1)
        finally:
            os.remove(cache_path)

    def test_load_all_entries(self):
        """Loading all entries should return a mapping of 'artist - title' to value."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as tmp:
            cache_path = tmp.name
        try:
            jsonl_save_entry(cache_path, 'Artist1', 'Title1', 'Lyrics1', 'lyrics')
            jsonl_save_entry(cache_path, 'Artist2', 'Title2', 'Lyrics2', 'lyrics')
            mapping = jsonl_load_all(cache_path, 'lyrics')
            self.assertEqual(mapping, {
                'Artist1 - Title1': 'Lyrics1',
                'Artist2 - Title2': 'Lyrics2',
            })
        finally:
            os.remove(cache_path)


if __name__ == '__main__':
    unittest.main()