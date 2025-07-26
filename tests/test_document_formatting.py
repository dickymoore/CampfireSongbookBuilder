"""Tests for document formatting helpers.

The sort_songs function should order songs case‑insensitively and ignore
non‑alphanumeric characters in titles.
"""

import unittest

from CampfireSongbookBuilder.app.document_formatting import sort_songs


class TestDocumentFormatting(unittest.TestCase):
    """Unit tests for sorting song titles."""

    def test_sort_songs_ignores_case_and_punctuation(self):
        songs = [
            {'Artist': 'X', 'Title': 'B Song'},
            {'Artist': 'Y', 'Title': 'a song'},
            {'Artist': 'Z', 'Title': 'A Song'},
            {'Artist': 'W', 'Title': 'a-song'},
        ]
        sorted_songs = sort_songs(songs)
        ordered_titles = [s['Title'] for s in sorted_songs]
        # All variations of "a song" should come before "B Song"
        self.assertEqual(ordered_titles[:3], ['a song', 'A Song', 'a-song'])
        self.assertEqual(ordered_titles[-1], 'B Song')


if __name__ == '__main__':
    unittest.main()