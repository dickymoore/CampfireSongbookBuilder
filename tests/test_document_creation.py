import tempfile
import unittest
from pathlib import Path

from app.content_models import build_review_decision, compute_content_hash
from app.review_state import save_review_decisions

try:
    from docx import Document
    from app.document_creation import create_document_from_cache
    DOCX_AVAILABLE = True
except ModuleNotFoundError:
    Document = None
    create_document_from_cache = None
    DOCX_AVAILABLE = False


@unittest.skipUnless(DOCX_AVAILABLE, "python-docx is not installed in this environment")
class TestDocumentCreation(unittest.TestCase):
    def _read_document_text(self, path):
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)

    def test_create_document_from_cache_excludes_questionable_and_overlong_content_by_default(self):
        song_list = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song"},
            {"Artist": "The Campfire Trio", "Title": "Long Song"},
            {"Artist": "The Campfire Trio", "Title": "Missing Song"},
        ]
        lyrics_cache = {
            "The Campfire Trio - Trail Song": "First line\nSecond line",
            "The Campfire Trio - Long Song": "\n".join(
                "Line {}".format(index) for index in range(5100)
            ),
            "The Campfire Trio - Missing Song": "Lyrics not found.",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "lyrics.docx"

            report_data = create_document_from_cache(
                song_list,
                lyrics_cache,
                {},
                lyrics_output=output_path,
            )

            text = self._read_document_text(output_path)
            report_entries = {entry["title"]: entry for entry in report_data["entries"]}

            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Missing Song by The Campfire Trio", text)
            self.assertNotIn("Long Song by The Campfire Trio", text)
            self.assertTrue(report_entries["Trail Song"]["included"])
            self.assertFalse(report_entries["Missing Song"]["included"])
            self.assertFalse(report_entries["Long Song"]["included"])
            self.assertEqual(
                report_entries["Long Song"]["reason"],
                "Lyrics are too long and were excluded from the document.",
            )

    def test_create_document_from_cache_includes_questionable_content_with_override(self):
        song_list = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song"},
            {"Artist": "The Campfire Trio", "Title": "Override Song"},
        ]
        lyrics_cache = {
            "The Campfire Trio - Trail Song": "First line\nSecond line",
            "The Campfire Trio - Override Song": "Lyrics not found.",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            review_decisions_path = tmp_path / "review_decisions.json"
            override_decision = build_review_decision(
                "The Campfire Trio - Override Song",
                "lyrics",
                compute_content_hash("Lyrics not found."),
                "override",
                reason="Approved for this print run.",
                decided_at="2026-05-19T15:00:34+01:00",
            )
            save_review_decisions(review_decisions_path, [override_decision])

            output_path = tmp_path / "lyrics.docx"

            import app.document_creation as document_creation

            original_quality_status_path = document_creation.QUALITY_STATUS_PATH
            original_review_decisions_path = document_creation.REVIEW_DECISIONS_PATH
            document_creation.QUALITY_STATUS_PATH = tmp_path / "missing_quality_status.json"
            document_creation.REVIEW_DECISIONS_PATH = review_decisions_path
            try:
                create_document_from_cache(
                    song_list,
                    lyrics_cache,
                    {},
                    lyrics_output=output_path,
                )
            finally:
                document_creation.QUALITY_STATUS_PATH = original_quality_status_path
                document_creation.REVIEW_DECISIONS_PATH = original_review_decisions_path

            text = self._read_document_text(output_path)

            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertIn("Override Song by The Campfire Trio", text)


if __name__ == "__main__":
    unittest.main()
