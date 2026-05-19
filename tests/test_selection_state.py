import json
import tempfile
import unittest
from pathlib import Path

from app.content_models import build_favourite_record
from app.selection_state import load_favourites, save_favourites


class TestSelectionState(unittest.TestCase):
    def test_save_and_load_favourites_round_trip_preserves_exact_identity(self):
        favourite = build_favourite_record("The Campfire Trio", "Trail Song")

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"

            save_favourites(target_path, [favourite])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())

            state, errors = load_favourites(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertIsNotNone(state["updated_at"])
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"], favourite)

    def test_load_entries_without_song_key_derives_canonical_key(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "artist": "The Campfire Trio",
                        "title": "Trail Song",
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_favourites(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                state["entries"]["The Campfire Trio - Trail Song"],
                {
                    "artist": "The Campfire Trio",
                    "title": "Trail Song",
                    "song_key": "The Campfire Trio - Trail Song",
                },
            )

    def test_load_missing_favourites_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"

            state, errors = load_favourites(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertIsNone(state["updated_at"])
            self.assertEqual(state["entries"], {})

    def test_load_malformed_favourites_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("{not valid json", encoding="utf-8")

            state, errors = load_favourites(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(errors[0]["field"], "$")
            self.assertIn("JSON", errors[0]["reason"])

    def test_load_top_level_shape_error_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

            state, errors = load_favourites(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["field"], "$")
            self.assertIn("top-level object", errors[0]["reason"])

    def test_load_invalid_entries_preserves_valid_records_and_reports_identity_errors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "favourites.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "artist": "The Campfire Trio",
                        "title": "Trail Song",
                    },
                    "The Campfire Trio - Broken Song": {
                        "artist": "The Campfire Trio",
                        "title": "Broken Song",
                        "song_key": "The Campfire Trio - Different Song",
                    },
                    "Missing Artist - Broken Song": {
                        "title": "Broken Song",
                    },
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_favourites(target_path)

            self.assertEqual(
                state["entries"]["The Campfire Trio - Trail Song"],
                {
                    "artist": "The Campfire Trio",
                    "title": "Trail Song",
                    "song_key": "The Campfire Trio - Trail Song",
                },
            )
            self.assertNotIn("The Campfire Trio - Broken Song", state["entries"])
            self.assertNotIn("Missing Artist - Broken Song", state["entries"])
            self.assertEqual(len(errors), 2)
            self.assertEqual(
                errors[0]["field"],
                "entries['The Campfire Trio - Broken Song'].song_key",
            )
            self.assertIn("derived song identity", errors[0]["reason"])
            self.assertEqual(errors[1]["field"], "entries['Missing Artist - Broken Song'].artist")
            self.assertIn("artist must be a non-empty string", errors[1]["reason"])

    def test_save_creates_parent_directories_automatically(self):
        favourite = build_favourite_record("The Campfire Trio", "Trail Song")

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = (
                Path(tmp_dir) / "data" / "selections" / "nested" / "favourites.json"
            )

            save_favourites(target_path, [favourite])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())
            self.assertTrue(target_path.parent.parent.exists())


if __name__ == "__main__":
    unittest.main()
