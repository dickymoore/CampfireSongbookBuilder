import json
import sys
import tempfile
import unittest
import types
from pathlib import Path
from unittest.mock import patch

from app.content_models import build_source_attempt_record
from app.source_attempts import (
    append_source_attempt_record,
    load_source_attempts,
    record_source_attempt,
)


if "bs4" not in sys.modules:
    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:
        pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub

from app import fetch_data


class TestSourceAttempts(unittest.TestCase):
    def _build_attempt(self, source, status, content_type="lyrics", error=None, retrieved_at=None):
        return build_source_attempt_record(
            artist="The Campfire Trio",
            title="Trail Song",
            content_type=content_type,
            source=source,
            status=status,
            error=error,
            retrieved_at=retrieved_at,
        )

    def test_append_and_load_round_trip_preserves_order(self):
        first = self._build_attempt(
            "Genius",
            "not_found",
            retrieved_at="2026-05-19T14:13:56+01:00",
        )
        second = self._build_attempt(
            "Lyrics.ovh",
            "candidate",
            retrieved_at="2026-05-19T14:13:57+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"

            self.assertTrue(append_source_attempt_record(target_path, first))
            self.assertTrue(append_source_attempt_record(target_path, second))

            records, errors = load_source_attempts(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(records, [first, second])

    def test_missing_file_loads_as_empty_history(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"

            records, errors = load_source_attempts(target_path)

            self.assertEqual(records, [])
            self.assertEqual(errors, [])

    def test_load_reports_malformed_lines_without_losing_valid_records(self):
        valid = self._build_attempt(
            "Genius",
            "candidate",
            retrieved_at="2026-05-19T14:13:56+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                "\n".join(
                    [
                        "not json",
                        "[]",
                        "",
                        json.dumps(valid),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            records, errors = load_source_attempts(target_path)

            self.assertEqual(records, [valid])
            self.assertEqual(len(errors), 2)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(errors[0]["field"], "[line 1]")
            self.assertIn("Invalid JSON", errors[0]["reason"])
            self.assertEqual(errors[1]["field"], "[line 2]")

    def test_record_source_attempt_writes_contract_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"

            self.assertTrue(
                record_source_attempt(
                    "The Campfire Trio",
                    "Trail Song",
                    "lyrics",
                    "Genius",
                    "candidate",
                    retrieved_at="2026-05-19T14:13:56+01:00",
                    file_path=target_path,
                )
            )

            records, errors = load_source_attempts(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                records,
                [
                    {
                        "artist": "The Campfire Trio",
                        "title": "Trail Song",
                        "song_key": "The Campfire Trio - Trail Song",
                        "content_type": "lyrics",
                        "source": "Genius",
                        "status": "candidate",
                        "error": None,
                        "retrieved_at": "2026-05-19T14:13:56+01:00",
                    }
                ],
            )

    def test_append_failure_is_recoverable(self):
        attempt = self._build_attempt(
            "Genius",
            "candidate",
            retrieved_at="2026-05-19T14:13:56+01:00",
        )

        with patch.object(Path, "open", side_effect=OSError("disk full")):
            self.assertFalse(append_source_attempt_record("/tmp/unwritable/source_attempts.jsonl", attempt))

    def test_fetch_lyrics_records_attempts_and_continues_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"
            with patch.object(fetch_data, "SOURCE_ATTEMPTS_PATH", target_path), patch.object(
                fetch_data, "get_lyrics_from_genius", side_effect=RuntimeError("boom")
            ), patch.object(
                fetch_data, "get_lyrics_from_lyrics_ovh", return_value="Lyrics not found."
            ), patch.object(
                fetch_data, "get_lyrics_from_azlyrics", return_value="First line\nSecond line"
            ), patch.object(fetch_data, "get_manual_lyrics", return_value=None):
                lyrics, source_name, tried_log, quality_result = fetch_data.get_lyrics_from_sources(
                    "Trail Song", "The Campfire Trio"
                )

            self.assertEqual(lyrics, "First line\nSecond line")
            self.assertEqual(source_name, "AZLyrics")
            self.assertEqual(quality_result["quality"], "clean")
            self.assertEqual(
                tried_log,
                [
                    "Lyrics.ovh (The Campfire Trio – Trail Song)",
                    "AZLyrics (The Campfire Trio – Trail Song)",
                ],
            )

            records, errors = load_source_attempts(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                [record["status"] for record in records],
                ["error", "not_found", "candidate"],
            )
            self.assertEqual(
                [record["source"] for record in records],
                ["Genius", "Lyrics.ovh", "AZLyrics"],
            )
            self.assertEqual(
                [record["song_key"] for record in records],
                ["The Campfire Trio - Trail Song"] * 3,
            )
            self.assertTrue(all(record["content_type"] == "lyrics" for record in records))

    def test_fetch_chords_records_attempts_and_continues_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"
            with patch.object(fetch_data, "SOURCE_ATTEMPTS_PATH", target_path), patch.object(
                fetch_data, "get_chords_from_chordie", side_effect=RuntimeError("boom")
            ), patch.object(
                fetch_data, "get_chords_from_ultimate_guitar", return_value="Chords not found."
            ), patch.object(
                fetch_data, "get_chords_from_echords", return_value="x32010\n320003"
            ), patch.object(fetch_data, "get_chords_from_songsterr", return_value="not used"), patch.object(
                fetch_data, "get_chords_from_yousician", return_value="not used"
            ):
                chords, source_name, tried_log, quality_result = fetch_data.get_chords_from_sources(
                    "Trail Song", "The Campfire Trio"
                )

            self.assertEqual(chords, "x32010\n320003")
            self.assertEqual(source_name, "E-Chords")
            self.assertEqual(quality_result["quality"], "clean")
            self.assertEqual(
                tried_log,
                [
                    "Ultimate Guitar (The Campfire Trio – Trail Song)",
                    "E-Chords (The Campfire Trio – Trail Song)",
                ],
            )

            records, errors = load_source_attempts(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                [record["status"] for record in records],
                ["error", "not_found", "candidate"],
            )
            self.assertEqual(
                [record["source"] for record in records],
                ["Chordie", "Ultimate Guitar", "E-Chords"],
            )
            self.assertEqual(
                [record["song_key"] for record in records],
                ["The Campfire Trio - Trail Song"] * 3,
            )
            self.assertTrue(all(record["content_type"] == "chords" for record in records))


if __name__ == "__main__":
    unittest.main()
