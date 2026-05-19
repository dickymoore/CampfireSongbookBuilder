import tempfile
import unittest
from math import isnan
from pathlib import Path

from app.load_songs import load_songs


class TestLoadSongs(unittest.TestCase):
    def test_load_songs_reports_invalid_rows_and_preserves_valid_rows(self):
        csv_text = """Artist,Title,Skip
"The Campfire Trio ","Trail Song",
,Missing Artist Song,
The Campfire Trio,"   ",
Hidden Band,Skipped Song,sKiP
Broken Band,,skip
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "songs.csv"
            csv_path.write_text(csv_text, encoding="utf-8")

            with self.assertLogs("app.load_songs", level="WARNING") as logs:
                songs, invalid_rows = load_songs(csv_path)

        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0]["Artist"], "The Campfire Trio ")
        self.assertEqual(songs[0]["Title"], "Trail Song")
        self.assertEqual(len(invalid_rows), 3)

        first_invalid = invalid_rows[0]
        self.assertEqual(first_invalid["row_number"], 3)
        self.assertIsNone(first_invalid["artist"])
        self.assertEqual(first_invalid["title"], "Missing Artist Song")
        self.assertTrue(isnan(first_invalid["raw_artist"]))
        self.assertEqual(first_invalid["raw_title"], "Missing Artist Song")
        self.assertTrue(isnan(first_invalid["skip"]))
        self.assertEqual(first_invalid["reason"], "missing artist")

        second_invalid = invalid_rows[1]
        self.assertEqual(second_invalid["row_number"], 4)
        self.assertEqual(second_invalid["artist"], "The Campfire Trio")
        self.assertIsNone(second_invalid["title"])
        self.assertEqual(second_invalid["raw_artist"], "The Campfire Trio")
        self.assertEqual(second_invalid["raw_title"], "   ")
        self.assertTrue(isnan(second_invalid["skip"]))
        self.assertEqual(second_invalid["reason"], "missing title")

        third_invalid = invalid_rows[2]
        self.assertEqual(third_invalid["row_number"], 6)
        self.assertEqual(third_invalid["artist"], "Broken Band")
        self.assertIsNone(third_invalid["title"])
        self.assertEqual(third_invalid["raw_artist"], "Broken Band")
        self.assertTrue(isnan(third_invalid["raw_title"]))
        self.assertEqual(third_invalid["skip"], "skip")
        self.assertEqual(third_invalid["reason"], "missing title")

        log_output = "\n".join(logs.output)
        self.assertIn("row_number': 3", log_output)
        self.assertIn("row_number': 4", log_output)
        self.assertIn("row_number': 6", log_output)
        self.assertIn("'raw_artist': nan", log_output)
        self.assertIn("'raw_title': '   '", log_output)
        self.assertIn("'skip': 'skip'", log_output)
        self.assertIn("'reason': 'missing artist'", log_output)
        self.assertIn("'reason': 'missing title'", log_output)


if __name__ == "__main__":
    unittest.main()
