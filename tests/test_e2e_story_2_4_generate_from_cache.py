import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.docx_stub import install_docx_stub


def _install_bs4_stub():
    if "bs4" in sys.modules:
        return

    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:
        pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub


install_docx_stub()
_install_bs4_stub()

import main  # noqa: E402  pylint: disable=wrong-import-position

from docx import Document  # noqa: E402  pylint: disable=wrong-import-position

import app.document_creation as document_creation  # noqa: E402  pylint: disable=wrong-import-position
from app.content_models import build_review_decision, compute_content_hash  # noqa: E402
from app.review_state import save_review_decisions  # noqa: E402


class TestE2EStory24GenerateFromCache(unittest.TestCase):
    def _write_json(self, path, payload):
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _write_csv(self, path, lines):
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _write_jsonl_cache(self, path, value_field, entries):
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(
                {
                    "artist": entry["artist"],
                    "title": entry["title"],
                    value_field: entry[value_field],
                },
                ensure_ascii=False,
            )
            for entry in entries
        ]
        target_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _read_document_text(self, path):
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)

    def _run_generate_from_cache(self, tmp_path, review_decision_records=None):
        config_path = tmp_path / "data" / "config" / "config.json"
        songs_path = tmp_path / "data" / "src" / "CampfireSongs.csv"
        lyrics_cache_path = tmp_path / "data" / "cache" / "lyrics_cache.jsonl"
        chords_cache_path = tmp_path / "data" / "cache" / "chords_cache.jsonl"
        lyrics_doc_path = tmp_path / "data" / "output" / "Lyrics_Document.docx"
        reports_dir = tmp_path / "data" / "review" / "reports"
        review_decisions_path = tmp_path / "data" / "review" / "review_decisions.json"
        document_quality_path = tmp_path / "data" / "review" / "document_quality.json"
        content_scores_path = tmp_path / "data" / "review" / "content_scores.json"

        self._write_json(config_path, {"genius": {"client_access_token": "token"}})
        self._write_csv(
            songs_path,
            [
                "Artist,Title",
                "The Campfire Trio,Trail Song",
                "The Campfire Trio,Missing Song",
            ],
        )
        self._write_jsonl_cache(
            lyrics_cache_path,
            "lyrics",
            [
                {
                    "artist": "The Campfire Trio",
                    "title": "Trail Song",
                    "lyrics": "First line\nSecond line",
                },
                {
                    "artist": "The Campfire Trio",
                    "title": "Missing Song",
                    "lyrics": "Lyrics not found.",
                },
            ],
        )
        chords_cache_path.unlink(missing_ok=True)

        if review_decision_records is None:
            review_decisions_path.unlink(missing_ok=True)
        else:
            save_review_decisions(review_decisions_path, review_decision_records)

        def _write_report_to_tmp(report):
            import app.reporting as reporting

            return reporting.write_traceable_quality_report(report, output_dir=reports_dir)

        with (
            patch.object(
                sys,
                "argv",
                ["main.py", "--generate-from-cache", "--lyrics-only"],
            ),
            patch.object(main, "CONFIG_PATH", str(config_path)),
            patch.object(main, "SONGS_CSV_PATH", str(songs_path)),
            patch.object(main, "LYRICS_CACHE_PATH", str(lyrics_cache_path)),
            patch.object(main, "CHORDS_CACHE_PATH", str(chords_cache_path)),
            patch.object(main, "LYRICS_DOC_PATH", str(lyrics_doc_path)),
            patch.object(main, "load_source_attempts", return_value=([], [])),
            patch.object(main, "write_traceable_quality_report", side_effect=_write_report_to_tmp),
            patch.object(
                document_creation,
                "QUALITY_STATUS_PATH",
                tmp_path / "data" / "review" / "quality_status.json",
            ),
            patch.object(document_creation, "REVIEW_DECISIONS_PATH", review_decisions_path),
            patch.object(document_creation, "DOCUMENT_QUALITY_PATH", document_quality_path),
            patch.object(document_creation, "CONTENT_SCORES_PATH", content_scores_path),
        ):
            main.main()

        report_paths = list(reports_dir.glob("*.json"))
        if len(report_paths) != 1:
            raise AssertionError(
                "Expected exactly 1 traceability report under {}; found {}".format(
                    reports_dir,
                    len(report_paths),
                )
            )

        return {
            "lyrics_doc_path": lyrics_doc_path,
            "lyrics_markdown_path": lyrics_doc_path.with_suffix(".md"),
            "report_path": report_paths[0],
        }

    def _load_report_songs(self, report_path):
        payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
        return payload.get("songs", [])

    def test_generate_from_cache_excludes_questionable_content_by_default(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            outputs = self._run_generate_from_cache(tmp_path)

            self.assertTrue(outputs["lyrics_doc_path"].exists())
            self.assertTrue(outputs["lyrics_markdown_path"].exists())

            text = self._read_document_text(outputs["lyrics_doc_path"])
            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Missing Song by The Campfire Trio", text)

            songs = self._load_report_songs(outputs["report_path"])
            missing_song = next(
                song
                for song in songs
                if song.get("title") == "Missing Song" and song.get("content_type") == "lyrics"
            )
            self.assertFalse(missing_song["included"])
            self.assertEqual(missing_song["decision_source"], "default_exclude")
            self.assertEqual(missing_song["quality"], "questionable")
            self.assertEqual(missing_song["reason"], "Questionable content is excluded by default.")

    def test_generate_from_cache_includes_questionable_content_with_override_decision(self):
        override_content = "Lyrics not found."
        override_decision = build_review_decision(
            "The Campfire Trio - Missing Song",
            "lyrics",
            compute_content_hash(override_content),
            "override",
            reason="Manually approved for printing.",
            decided_at="2026-05-28T10:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            outputs = self._run_generate_from_cache(
                tmp_path,
                review_decision_records=[override_decision],
            )

            text = self._read_document_text(outputs["lyrics_doc_path"])
            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertIn("Missing Song by The Campfire Trio", text)

            songs = self._load_report_songs(outputs["report_path"])
            missing_song = next(
                song
                for song in songs
                if song.get("title") == "Missing Song" and song.get("content_type") == "lyrics"
            )
            self.assertTrue(missing_song["included"])
            self.assertEqual(missing_song["decision_source"], "review_override")
            self.assertIsInstance(missing_song.get("review_decision"), dict)

    def test_generate_from_cache_ignores_stale_review_decisions(self):
        stale_decision = build_review_decision(
            "The Campfire Trio - Missing Song",
            "lyrics",
            compute_content_hash("Reviewed content"),
            "accept",
            reason="Previously reviewed.",
            decided_at="2026-05-28T10:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            outputs = self._run_generate_from_cache(tmp_path, review_decision_records=[stale_decision])

            text = self._read_document_text(outputs["lyrics_doc_path"])
            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Missing Song by The Campfire Trio", text)

            songs = self._load_report_songs(outputs["report_path"])
            missing_song = next(
                song
                for song in songs
                if song.get("title") == "Missing Song" and song.get("content_type") == "lyrics"
            )
            self.assertFalse(missing_song["included"])
            self.assertEqual(missing_song["decision_source"], "default_exclude")


if __name__ == "__main__":
    unittest.main()

