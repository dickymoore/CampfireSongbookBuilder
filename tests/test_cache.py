import json
import tempfile
import unittest
from pathlib import Path

from app.cache import jsonl_load_all, jsonl_load_entry


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


if __name__ == "__main__":
    unittest.main()
