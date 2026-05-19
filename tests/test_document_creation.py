import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.content_models import build_favourite_record, build_review_decision, compute_content_hash
from app.review_state import save_review_decisions
from tests.docx_stub import install_docx_stub

install_docx_stub()

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
            markdown_text = output_path.with_suffix(".md").read_text(encoding="utf-8")
            report_entries = {entry["title"]: entry for entry in report_data["entries"]}

            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Missing Song by The Campfire Trio", text)
            self.assertNotIn("Long Song by The Campfire Trio", text)
            self.assertIn("Trail Song by The Campfire Trio", markdown_text)
            self.assertNotIn("Missing Song by The Campfire Trio", markdown_text)
            self.assertNotIn("Long Song by The Campfire Trio", markdown_text)
            self.assertTrue(report_entries["Trail Song"]["included"])
            self.assertFalse(report_entries["Missing Song"]["included"])
            self.assertFalse(report_entries["Long Song"]["included"])
            self.assertEqual(
                report_entries["Long Song"]["reason"],
                "Questionable content is excluded by default.",
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

    def test_create_document_from_cache_filters_selected_songs_in_selection_order(self):
        selection_records = [
            build_favourite_record("The Campfire Trio", "Trail Song"),
            build_favourite_record("The Campfire Trio", "Missing Song"),
            build_favourite_record("The Campfire Trio", "Override Song"),
        ]
        lyrics_cache = {
            "The Campfire Trio - Trail Song": "First line\nSecond line",
            "The Campfire Trio - Missing Song": "Lyrics not found.",
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
                reason="Approved for this selected book.",
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
                report_data = create_document_from_cache(
                    [],
                    lyrics_cache,
                    {},
                    lyrics_output=output_path,
                    selection_records=selection_records,
                    report_source="generate_from_selection",
                )
            finally:
                document_creation.QUALITY_STATUS_PATH = original_quality_status_path
                document_creation.REVIEW_DECISIONS_PATH = original_review_decisions_path

            text = self._read_document_text(output_path)
            report_entries = {entry["title"]: entry for entry in report_data["entries"]}

            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertIn("Override Song by The Campfire Trio", text)
            self.assertLess(
                text.index("Trail Song by The Campfire Trio"),
                text.index("Override Song by The Campfire Trio"),
            )
            self.assertNotIn("Missing Song by The Campfire Trio", text)
            self.assertTrue(report_entries["Trail Song"]["included"])
            self.assertFalse(report_entries["Missing Song"]["included"])
            self.assertEqual(
                report_entries["Missing Song"]["reason"],
                "Questionable content is excluded by default.",
            )
            self.assertTrue(report_entries["Override Song"]["included"])
            self.assertEqual(report_entries["Override Song"]["decision_source"], "review_override")
            self.assertEqual(report_data["source"], "generate_from_selection")

    def test_create_document_from_cache_reports_selection_completeness_issues_before_output(self):
        selection_records = [
            build_favourite_record("The Campfire Trio", "Trail Song"),
            build_favourite_record("The Campfire Trio", "Missing Song"),
        ]
        lyrics_cache = {
            "The Campfire Trio - Trail Song": "First line\nSecond line",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_path = tmp_path / "lyrics.docx"

            report_data = create_document_from_cache(
                [],
                lyrics_cache,
                {},
                lyrics_output=output_path,
                selection_records=selection_records,
                report_source="generate_from_selection",
            )

            text = self._read_document_text(output_path)
            report_entries = {entry["title"]: entry for entry in report_data["entries"]}

            self.assertIn("Trail Song by The Campfire Trio", text)
            self.assertNotIn("Missing Song by The Campfire Trio", text)
            self.assertTrue(report_entries["Trail Song"]["included"])
            self.assertFalse(report_entries["Missing Song"]["included"])
            self.assertEqual(
                report_entries["Missing Song"]["reason"],
                "Missing content is excluded by default.",
            )
            self.assertEqual(len(report_data["selection_issues"]), 1)
            self.assertEqual(report_data["selection_issues"][0]["song_key"], "The Campfire Trio - Missing Song")
            self.assertEqual(report_data["selection_issues"][0]["issue_type"], "missing_content")
            self.assertEqual(report_data["source"], "generate_from_selection")

    def test_create_document_from_cache_writes_pdf_when_converter_succeeds(self):
        song_list = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        lyrics_cache = {"The Campfire Trio - Trail Song": "First line\nSecond line"}

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "lyrics.docx"

            def fake_convert(docx_path, pdf_path=None, runner=None, which=None):  # noqa: ARG001
                target_path = Path(docx_path).with_suffix(".pdf")
                target_path.write_text("pdf", encoding="utf-8")
                return target_path, None

            with patch("app.document_creation.convert_document_to_pdf", side_effect=fake_convert):
                report_data = create_document_from_cache(
                    song_list,
                    lyrics_cache,
                    {},
                    lyrics_output=output_path,
                    pdf_output=True,
                )

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.with_suffix(".md").exists())
            self.assertTrue(output_path.with_suffix(".pdf").exists())
            self.assertEqual(report_data["pdf_outputs"], [str(output_path.with_suffix(".pdf"))])
            self.assertEqual(report_data["pdf_errors"], [])

    def test_create_document_from_cache_preserves_artifacts_when_pdf_conversion_fails(self):
        song_list = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        lyrics_cache = {"The Campfire Trio - Trail Song": "First line\nSecond line"}

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "lyrics.docx"

            with patch(
                "app.document_creation.convert_document_to_pdf",
                return_value=(None, "converter missing"),
            ):
                report_data = create_document_from_cache(
                    song_list,
                    lyrics_cache,
                    {},
                    lyrics_output=output_path,
                    pdf_output=True,
                )

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.with_suffix(".md").exists())
            self.assertFalse(output_path.with_suffix(".pdf").exists())
            self.assertEqual(report_data["pdf_outputs"], [])
            self.assertEqual(len(report_data["pdf_errors"]), 1)
            self.assertEqual(report_data["pdf_errors"][0]["reason"], "converter missing")


if __name__ == "__main__":
    unittest.main()
