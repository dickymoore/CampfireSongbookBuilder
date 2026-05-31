import json
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
from app.reporting import (  # noqa: E402
    build_traceable_quality_report,
    write_traceable_quality_report,
)
# pylint: enable=wrong-import-position


class TestE2EStory41PdfVerificationRecords(unittest.TestCase):
    def _load_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _run_document_generation(self, tmp_path, convert_result):
        output_path = tmp_path / "data" / "output" / "Lyrics_Document.docx"
        reports_dir = tmp_path / "data" / "review" / "reports"
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
            patch("app.document_creation.convert_document_to_pdf", return_value=convert_result),
        ):
            report_data = document_creation.create_document_from_cache(
                song_list,
                lyrics_cache,
                {},
                lyrics_output=str(output_path),
                pdf_output=True,
            )

        report = build_traceable_quality_report(
            report_data.get("entries", []),
            source=report_data.get("source", "generate_from_cache"),
            report_type=report_data.get("report_type", "quality_run"),
            generated_at=report_data.get("generated_at"),
            selection_issues=report_data.get("selection_issues", []),
            pdf_outputs=report_data.get("pdf_outputs", []),
            pdf_errors=report_data.get("pdf_errors", []),
            document_verification=report_data.get("document_verification", []),
            review_gate_decisions=report_data.get("review_gate_decisions", []),
            content_scores=report_data.get("content_scores", []),
        )
        report_path = write_traceable_quality_report(report, output_dir=reports_dir)

        return {
            "output_path": output_path,
            "reports_dir": reports_dir,
            "report_data": report_data,
            "report_path": report_path,
            "document_quality_path": document_quality_path,
        }

    def test_pdf_converter_success_emits_verification_record_and_traceability_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            expected_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            write_minimal_pdf(expected_pdf_path, "x" * 80)

            outputs = self._run_document_generation(tmp_path, (expected_pdf_path, None))

            self.assertTrue(outputs["output_path"].exists())
            self.assertTrue(outputs["output_path"].with_suffix(".md").exists())
            self.assertTrue(expected_pdf_path.exists())
            self.assertEqual(outputs["report_data"]["pdf_errors"], [])
            self.assertEqual(outputs["report_data"]["pdf_outputs"], [str(expected_pdf_path)])

            state, errors = load_document_verification(outputs["document_quality_path"])
            self.assertEqual(errors, [])
            self.assertIn(str(expected_pdf_path), state["entries"])

            pdf_record = state["entries"][str(expected_pdf_path)]
            self.assertEqual(pdf_record["artifact_type"], "pdf")
            self.assertEqual(pdf_record["verification_status"], "passed")
            self.assertIn("meets_neatness_thresholds", pdf_record["verification_reasons"])

            report_payload = self._load_json(outputs["report_path"])
            self.assertEqual(report_payload["summary"]["pdf_output_count"], 1)
            self.assertEqual(report_payload["summary"]["pdf_error_count"], 0)
            self.assertEqual(report_payload["pdf_outputs"], [str(expected_pdf_path)])
            self.assertEqual(report_payload["pdf_errors"], [])
            self.assertTrue(
                any(
                    record.get("artifact_type") == "pdf"
                    and record.get("artifact_path") == str(expected_pdf_path)
                    for record in report_payload.get("document_verification", [])
                )
            )

    def test_pdf_converter_failure_records_generation_error_without_verification_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"

            outputs = self._run_document_generation(tmp_path, (None, "converter missing"))

            self.assertTrue(outputs["output_path"].exists())
            self.assertTrue(outputs["output_path"].with_suffix(".md").exists())
            self.assertFalse(expected_pdf_path.exists())
            self.assertEqual(outputs["report_data"]["pdf_outputs"], [])
            self.assertEqual(len(outputs["report_data"]["pdf_errors"]), 1)
            self.assertEqual(outputs["report_data"]["pdf_errors"][0]["reason"], "converter missing")

            state, errors = load_document_verification(outputs["document_quality_path"])
            self.assertEqual(errors, [])
            self.assertNotIn(str(expected_pdf_path), state["entries"])
            self.assertFalse(
                any(
                    record.get("artifact_type") == "pdf"
                    for record in outputs["report_data"].get("document_verification", [])
                )
            )

            report_payload = self._load_json(outputs["report_path"])
            self.assertEqual(report_payload["summary"]["pdf_output_count"], 0)
            self.assertEqual(report_payload["summary"]["pdf_error_count"], 1)
            self.assertEqual(report_payload["pdf_outputs"], [])
            self.assertEqual(len(report_payload["pdf_errors"]), 1)
            self.assertEqual(report_payload["pdf_errors"][0]["reason"], "converter missing")
            self.assertFalse(
                any(
                    record.get("artifact_type") == "pdf"
                    for record in report_payload.get("document_verification", [])
                )
            )


if __name__ == "__main__":
    unittest.main()
