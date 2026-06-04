import unittest

from app.duplicate_detection import find_song_duplicates, normalize_duplicate_text


class TestDuplicateDetection(unittest.TestCase):
    def test_normalize_duplicate_text_collapses_punctuation_and_case(self):
        self.assertEqual(
            normalize_duplicate_text("The Smiths & Friends!"),
            "the smiths and friends",
        )

    def test_find_song_duplicates_reports_exact_and_fuzzy_candidates(self):
        songs = [
            {"Artist": "The Smiths", "Title": "I Don't Owe You Anything"},
            {"Artist": "The Smiths", "Title": "I Don't Owe you Anything"},
            {"Artist": "Blur", "Title": "Girls and Boys"},
            {"Artist": "Blur", "Title": "Girls & Boys"},
        ]

        analysis = find_song_duplicates(songs, threshold=0.85)

        self.assertEqual(len(analysis["exact_duplicate_groups"]), 2)
        exact_titles = sorted(
            tuple(record["title"] for record in group)
            for group in analysis["exact_duplicate_groups"]
        )
        self.assertEqual(
            exact_titles,
            [
                ("Girls and Boys", "Girls & Boys"),
                ("I Don't Owe You Anything", "I Don't Owe you Anything"),
            ],
        )
        self.assertEqual(len(analysis["fuzzy_candidates"]), 0)


if __name__ == "__main__":
    unittest.main()
