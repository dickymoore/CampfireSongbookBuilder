import io
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


class TestE2EStory31InvalidSourceRowsGenerateFromCache(unittest.TestCase):
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

    def test_generate_from_cache_surfaces_invalid_source_rows_and_generates_for_valid_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
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
                    "Artist,Title,Skip",
                    "The Campfire Trio,Trail Song,",
                    ",Nameless Tune,",
                    "The Campfire Trio,,skip",
                    "Skipped Band,Skipped Song,skip",
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
                ],
            )
            chords_cache_path.unlink(missing_ok=True)
            review_decisions_path.unlink(missing_ok=True)

            def _write_report_to_tmp(report):
                import app.reporting as reporting

                return reporting.write_traceable_quality_report(report, output_dir=reports_dir)

            with self.assertLogs(level="WARNING") as captured_logs:
                with (
                    patch(
                        "sys.stdout",
                        new_callable=io.StringIO,
                    ),
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

            self.assertTrue(any("invalid row(s)" in line for line in captured_logs.output))

            report_paths = list(reports_dir.glob("*.json"))
            self.assertEqual(len(report_paths), 1)
            report_payload = json.loads(report_paths[0].read_text(encoding="utf-8"))

            summary = report_payload.get("summary", {})
            self.assertEqual(summary.get("invalid_input_count"), 2)
            invalid_rows = summary.get("invalid_input_rows", [])
            self.assertEqual(len(invalid_rows), 2)
            invalid_rows_by_number = {row["row_number"]: row for row in invalid_rows}
            self.assertEqual(invalid_rows_by_number[3]["reason"], "missing artist")
            self.assertIn("missing title", invalid_rows_by_number[4]["reason"])

            self.assertTrue(lyrics_doc_path.exists())
            text = self._read_document_text(lyrics_doc_path)
            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Nameless Tune", text)
            self.assertNotIn("Skipped Song", text)


if __name__ == "__main__":
    unittest.main()
