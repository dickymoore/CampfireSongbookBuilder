import json
import os
import tempfile
import unittest
from pathlib import Path

from app.cache import (
    backup_jsonl_file,
    jsonl_load_all,
    jsonl_load_entry,
    jsonl_sync_entries_from_mapping,
)


class TestCacheCompatibility(unittest.TestCase):
    def test_jsonl_load_helpers_preserve_legacy_and_augmented_records(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_path = Path(tmp_dir) / "lyrics_cache.jsonl"
            cache_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "artist": "The Campfire Trio",
                                "title": "Trail Song",
                                "lyrics": "First line\nSecond line",
                            }
                        ),
                        json.dumps(
                            {
                                "artist": "The Campfire Trio",
                                "title": "Future Song",
                                "lyrics": "Future line",
                                "quality_status": {
                                    "quality": "clean",
                                    "content_hash": "sha256:1234",
                                },
                                "review_decision": {
                                    "decision": "accept",
                                    "content_hash": "sha256:1234",
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            loaded_all = jsonl_load_all(cache_path, "lyrics")

            self.assertEqual(
                loaded_all,
                {
                    "The Campfire Trio - Trail Song": "First line\nSecond line",
                    "The Campfire Trio - Future Song": "Future line",
                },
            )
            self.assertEqual(
                jsonl_load_entry(cache_path, "The Campfire Trio", "Trail Song", "lyrics"),
                "First line\nSecond line",
            )
            self.assertEqual(
                jsonl_load_entry(cache_path, "The Campfire Trio", "Future Song", "lyrics"),
                "Future line",
            )

    def test_backup_jsonl_file_copies_existing_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_path = Path(tmp_dir) / "chords_cache.jsonl"
            backups_dir = Path(tmp_dir) / "backups"
            cache_path.write_text('{"artist":"A","title":"B","chords":"C"}\n', encoding="utf-8")

            backup_path = backup_jsonl_file(cache_path, backups_dir, "pre_manual_sync")

            self.assertIsNotNone(backup_path)
            self.assertTrue(os.path.exists(backup_path))
            self.assertEqual(Path(backup_path).read_text(encoding="utf-8"), cache_path.read_text(encoding="utf-8"))

    def test_jsonl_sync_entries_from_mapping_overwrites_existing_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_path = Path(tmp_dir) / "chords_cache.jsonl"
            cache_path.write_text(
                "\n".join(
                    [
                        json.dumps({"artist": "The Campfire Trio", "title": "Trail Song", "chords": "old chords"}),
                        json.dumps({"artist": "The Campfire Trio", "title": "Night Run", "chords": "keep me"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            updated = jsonl_sync_entries_from_mapping(
                cache_path,
                "chords",
                {
                    "The Campfire Trio - Trail Song": "new chords\n",
                    "New Artist - New Song": "fresh chords\n",
                },
            )

            self.assertEqual(updated, 2)
            self.assertEqual(
                jsonl_load_entry(cache_path, "The Campfire Trio", "Trail Song", "chords"),
                "new chords\n",
            )
            self.assertEqual(
                jsonl_load_entry(cache_path, "The Campfire Trio", "Night Run", "chords"),
                "keep me",
            )
            self.assertEqual(
                jsonl_load_entry(cache_path, "New Artist", "New Song", "chords"),
                "fresh chords\n",
            )


if __name__ == "__main__":
    unittest.main()
