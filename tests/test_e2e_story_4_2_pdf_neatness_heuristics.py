import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.docx_stub import install_docx_stub
from tests.pdf_fixtures import write_minimal_pdf

install_docx_stub()

# pylint: disable=wrong-import-position
import app.document_creation as document_creation  # noqa: E402
from app.document_verification import load_document_verification  # noqa: E402
# pylint: enable=wrong-import-position


class TestE2EStory42PdfNeatnessHeuristics(unittest.TestCase):
    def _run_document_generation(self, tmp_path, pdf_path):
        output_path = tmp_path / "data" / "output" / "Lyrics_Document.docx"
        document_quality_path = tmp_path / "data" / "review" / "document_quality.json"

        song_list = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        lyrics_cache = {"The Campfire Trio - Trail Song": "First line\nSecond line"}

        with (
            patch.object(
                document_creation,
                "QUALITY_STATUS_PATH",
                tmp_path / "data" / "review" / "quality_status.json",
            ),
            patch.object(
                document_creation,
                "REVIEW_DECISIONS_PATH",
                tmp_path / "data" / "review" / "review_decisions.json",
            ),
            patch.object(document_creation, "DOCUMENT_QUALITY_PATH", document_quality_path),
            patch.object(
                document_creation,
                "CONTENT_SCORES_PATH",
                tmp_path / "data" / "review" / "content_scores.json",
            ),
            patch("app.document_creation.convert_document_to_pdf", return_value=(pdf_path, None)),
        ):
            report_data = document_creation.create_document_from_cache(
                song_list,
                lyrics_cache,
                {},
                lyrics_output=str(output_path),
                pdf_output=True,
            )

        return {
            "output_path": output_path,
            "report_data": report_data,
            "document_quality_path": document_quality_path,
        }

    def test_sparse_pages_pdf_emits_failed_verification_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            write_minimal_pdf(pdf_path, ["x" * 80, "", ""])
            outputs = self._run_document_generation(tmp_path, pdf_path)

            self.assertEqual(outputs["report_data"]["pdf_errors"], [])
            self.assertEqual(outputs["report_data"]["pdf_outputs"], [str(pdf_path)])

            state, errors = load_document_verification(outputs["document_quality_path"])
            self.assertEqual(errors, [])
            self.assertIn(str(pdf_path), state["entries"])
            pdf_record = state["entries"][str(pdf_path)]
            self.assertEqual(pdf_record["artifact_type"], "pdf")
            self.assertEqual(pdf_record["verification_status"], "failed")
            self.assertEqual(pdf_record["verification_reasons"], ["sparse_pages"])

    def test_text_extraction_failure_pdf_emits_all_applicable_reasons(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            write_minimal_pdf(pdf_path, [""])
            outputs = self._run_document_generation(tmp_path, pdf_path)

            state, errors = load_document_verification(outputs["document_quality_path"])
            self.assertEqual(errors, [])
            pdf_record = state["entries"][str(pdf_path)]
            self.assertEqual(pdf_record["verification_status"], "failed")
            self.assertEqual(
                pdf_record["verification_reasons"],
                ["text_extraction_failed", "sparse_pages"],
            )


if __name__ == "__main__":
    unittest.main()
