"""Tests for the ``text_cleaning`` module.

These tests verify that lyrics and chord cleaning functions behave as expected.
The functions should remove unwanted sections and markup without altering
substantive content.
"""

import unittest

from CampfireSongbookBuilder.app.text_cleaning import clean_lyrics, clean_chords


class TestTextCleaning(unittest.TestCase):
    """Unit tests for cleaning lyrics and chords."""

    def test_clean_lyrics_removes_contributors_and_embed(self):
        """The cleaner should strip contributor and embed sections from lyrics."""
        raw = (
            "Line before contributors\n"
            "Contributors:\n"
            "Some contributor text\n"
            "Embed\n"
            "Final line"
        )
        cleaned = clean_lyrics(raw)
        # The cleaned lyrics should not contain the trigger words
        self.assertNotIn("Contributors", cleaned)
        self.assertNotIn("Embed", cleaned)
        # It should retain the final line of the lyrics
        self.assertIn("Final line", cleaned)

    def test_clean_lyrics_removes_unwanted_phrases(self):
        """Certain advertising phrases should be removed from the lyrics."""
        raw = (
            "You might also like Old Song\n"
            "See Artist LiveGet tickets as low as $40\n"
            "Random Lyrics\n"
            "Actual lyric line"
        )
        cleaned = clean_lyrics(raw)
        # Advertising lines should be stripped out entirely
        self.assertNotIn("You might also like", cleaned)
        self.assertNotIn("LiveGet", cleaned)
        self.assertNotIn("Lyrics", cleaned)
        # The actual lyric line should remain
        self.assertIn("Actual lyric line", cleaned)

    def test_clean_chords_removes_markup_tags(self):
        """Markup tags such as [ch] and [tab] should be stripped from chords."""
        raw = "[ch]C G Am[/ch] [tab]F G[/tab]"
        cleaned = clean_chords(raw)
        # Tags should be removed and spacing normalised
        expected = "C G Am F G"
        # Remove any extra whitespace for comparison
        self.assertEqual(" ".join(cleaned.split()), expected)


if __name__ == '__main__':
    unittest.main()