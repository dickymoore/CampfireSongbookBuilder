import unittest

from app.text_cleaning import clean_chords, clean_lyrics


class TestTextCleaning(unittest.TestCase):
    def test_clean_lyrics_removes_translations_prefix(self):
        lyrics = (
            "[Verse 1]\n"
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

    def test_clean_chords_removes_tab_staff_and_commentary(self):
        chords = (
            "Tab from: somewhere\n"
            "e|----------------|\n"
            "B|----------------|\n"
            "When playing Em, add an accent\n"
            "Em\n"
            "Hello there\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Em\nHello there\n")

    def test_clean_chords_removes_chord_diagram_and_beat_count_lines(self):
        chords = (
            "Chords used :\n"
            "|---0----0------0-----0---0---|\n"
            "[1] [+] [2] [+] [3] [+] [4] [+] [1] [+] [2] [+] [3] [+] [4] [+]\n"
            "Am\n"
            "A lyric line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nA lyric line\n")

    def test_clean_chords_removes_multiline_commentary_block(self):
        chords = (
            "In the recording off of Bryter Layter it sounds like Nick is using an open tuning of some sort.\n"
            "I prefer to stay in standard tuning when I play so here's how I have written out the chords.\n"
            "A\n"
            "Real line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "A\nReal line\n")

    def test_clean_chords_removes_asterisk_separator_lines(self):
        chords = (
            "**************\n"
            "Am\n"
            "Line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nLine\n")

    def test_clean_chords_removes_link_and_title_preamble_block(self):
        chords = (
            "From the album \"Let It Bee\" (1988)\n"
            "Spotify link: https://example.com\n"
            "Voice of the Beehive - I Say Nothing\n"
            "D\n"
            "Lyric line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "D\nLyric line\n")

    def test_clean_chords_removes_dash_separator_lines(self):
        chords = (
            "-----------------------------\n"
            "Am\n"
            "Line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nLine\n")

    def test_clean_chords_removes_hash_separator_and_ug_disclaimer_lines(self):
        chords = (
            "##This file is the author's own work and represents their interpretation of the #\n"
            "#------------------------------------------------------------------------------##\n"
            "Am\n"
            "Line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nLine\n")

    def test_clean_chords_removes_bracketed_tab_from_link(self):
        chords = (
            "[ Tab from: http://www.guitartabs.cc/example ]\n"
            "Am\n"
            "Line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nLine\n")

    def test_clean_chords_removes_capo_and_please_note_lines(self):
        chords = (
            "Capo on 2. Closest thing I could think of.\n"
            "#----------------------------------PLEASE NOTE---------------------------------#\n"
            "Am\n"
            "Line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "Am\nLine\n")

    def test_clean_chords_removes_inline_parenthetical_commentary(self):
        chords = (
            "C, Am, C, Am (This is just an estimation of what's going on with the synth part.)\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "C, Am, C, Am\n")

    def test_clean_chords_expands_slash_compacted_chord_only_lines(self):
        chords = (
            "C G D / C G D / Em Bm C\n"
            "Lyric line\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "C G D\nC G D\nEm Bm C\nLyric line\n")

    def test_clean_chords_strips_inline_bracketed_chords(self):
        chords = (
            "[Cmaj7]we are in love [H7sus4]we are in love [242222]\n"
        )

        cleaned = clean_chords(chords)

        self.assertEqual(cleaned, "we are in love we are in love\n")
