import json
import tempfile
import unittest
from pathlib import Path

from app.content_models import build_favourite_record
from app.selection_state import (
    load_named_selection,
    save_named_selection,
)


class TestSelectionState(unittest.TestCase):
    def test_save_and_load_named_selection_preserves_order(self):
        selection_records = [
            build_favourite_record("The Campfire Trio", "Trail Song"),
            build_favourite_record("The Campfire Trio", "Firelight Waltz"),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "trip-night.json"

            save_named_selection(
                target_path,
                selection_records,
                selection_name="trip-night",
                updated_at="2026-05-19T14:13:56+01:00",
            )

            state, errors = load_named_selection(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(state["selection_name"], "trip-night")
            self.assertEqual(state["updated_at"], "2026-05-19T14:13:56+01:00")
            self.assertEqual(state["entries"], selection_records)

    def test_load_missing_named_selection_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "trip-night.json"

            state, errors = load_named_selection(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(state["selection_name"], "trip-night")
            self.assertIsNone(state["updated_at"])
            self.assertEqual(state["entries"], [])

    def test_load_named_selection_reports_recoverable_errors_and_preserves_valid_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "trip-night.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "selection_name": "trip-night",
                "updated_at": "2026-05-19T14:13:56+01:00",
                "entries": [
                    {
                        "artist": "The Campfire Trio",
                        "title": "Trail Song",
                    },
                    {
                        "artist": "The Campfire Trio",
                        "title": "Broken Song",
                        "song_key": "The Campfire Trio - Different Song",
                    },
                    {
                        "title": "Missing Artist",
                    },
                ],
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_named_selection(target_path)

            self.assertEqual(
                state["entries"],
                [
                    {
                        "artist": "The Campfire Trio",
                        "title": "Trail Song",
                        "song_key": "The Campfire Trio - Trail Song",
                    }
                ],
            )
            self.assertEqual(len(errors), 2)
            self.assertEqual(errors[0]["field"], "entries[1].song_key")
            self.assertIn("derived song identity", errors[0]["reason"])
            self.assertEqual(errors[1]["field"], "entries[2].artist")
            self.assertIn("artist must be a non-empty string", errors[1]["reason"])

    def test_load_named_selection_reports_top_level_shape_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "selections" / "trip-night.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

            state, errors = load_named_selection(target_path)

            self.assertEqual(state["entries"], [])
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["field"], "$")
            self.assertIn("top-level object", errors[0]["reason"])

    def test_named_selection_same_song_can_be_saved_in_multiple_files(self):
        record = build_favourite_record("The Campfire Trio", "Trail Song")

        with tempfile.TemporaryDirectory() as tmp_dir:
            first_path = Path(tmp_dir) / "data" / "selections" / "trip-one.json"
            second_path = Path(tmp_dir) / "data" / "selections" / "trip-two.json"

            save_named_selection(first_path, [record], selection_name="trip-one")
            save_named_selection(second_path, [record], selection_name="trip-two")

            first_state, first_errors = load_named_selection(first_path)
            second_state, second_errors = load_named_selection(second_path)

            self.assertEqual(first_errors, [])
            self.assertEqual(second_errors, [])
            self.assertEqual(first_state["entries"], [record])
            self.assertEqual(second_state["entries"], [record])


if __name__ == "__main__":
    unittest.main()
