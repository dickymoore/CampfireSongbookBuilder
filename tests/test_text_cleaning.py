import unittest

from app.text_cleaning import clean_chords, clean_lyrics


class TestTextCleaning(unittest.TestCase):
    def test_clean_lyrics_removes_translations_prefix(self):
        lyrics = (
            "TranslationsEspañolItalianoChained To The Rhythm Lyrics[Verse 1]\n"
            "Are we crazy?\n"
        )

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(cleaned, "[Verse 1]\nAre we crazy?\n")

    def test_clean_lyrics_removes_contributors_and_embed_counters(self):
        lyrics = (
            "17 ContributorsLife on Mars? Lyrics\n"
            "[Verse 1]\n"
            "It's a god-awful small affair\n"
            "23Embed\n"
        )

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(
            cleaned,
            "[Verse 1]\nIt's a god-awful small affair\n",
        )

    def test_clean_lyrics_collapses_excessive_blank_lines(self):
        lyrics = "Line 1\n\n\n\nLine 2\n"

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(cleaned, "Line 1\n\nLine 2\n")

    def test_clean_lyrics_removes_inline_promo_block_before_next_section(self):
        lyrics = (
            "[Chorus]\n"
            "A line\n"
            "You might also like[Verse 2]\n"
            "Another line\n"
        )

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(cleaned, "[Chorus]\nA line\n[Verse 2]\nAnother line\n")

    def test_clean_lyrics_collapses_exact_repeated_lines(self):
        lyrics = (
            "This is the chorus line\n"
            "This is the chorus line\n"
            "Verse 2\n"
        )

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(cleaned, "This is the chorus line x2\nVerse 2\n")

    def test_clean_lyrics_collapses_exact_repeated_blocks(self):
        lyrics = (
            "Verse 1\n"
            "Line A\n"
            "Line B\n"
            "Verse 1\n"
            "Line A\n"
            "Line B\n"
        )

        cleaned = clean_lyrics(lyrics)

        self.assertEqual(cleaned, "Verse 1\nLine A\nLine B x2\n")

    def test_clean_chords_collapses_vertical_chord_runs(self):
        chords = (
            "Intro 1\n"
            "F\n"
            "Am\n"
            "F\n"
            "Am\n"
            "Today I\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Intro 1\nF / Am / F / Am\nToday I\n")
