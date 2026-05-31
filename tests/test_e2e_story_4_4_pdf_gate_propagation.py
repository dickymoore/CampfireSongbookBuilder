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
from app.reporting import (  # noqa: E402
    build_traceable_quality_report,
    write_traceable_quality_report,
)


class TestE2EStory44PdfGatePropagation(unittest.TestCase):
    def _load_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _run_document_generation(self, tmp_path, convert_result):
        output_path = tmp_path / "data" / "output" / "Lyrics_Document.docx"
        reports_dir = tmp_path / "data" / "review" / "reports"

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
            patch.object(
                document_creation,
                "DOCUMENT_QUALITY_PATH",
                tmp_path / "data" / "review" / "document_quality.json",
            ),
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
            "report_data": report_data,
            "report_path": report_path,
        }

    def _find_pdf_gate_entry(self, artifacts, artifact_path):
        for item in artifacts:
            if item.get("artifact_type") == "pdf" and item.get("artifact_path") == str(artifact_path):
                return item
        return None

    def test_converter_failure_surfaces_as_manual_review_blocker_without_verification_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"

            outputs = self._run_document_generation(tmp_path, (None, "converter missing"))
            report_payload = self._load_json(outputs["report_path"])

            self.assertEqual(outputs["report_data"]["pdf_outputs"], [])
            self.assertEqual(len(outputs["report_data"]["pdf_errors"]), 1)
            self.assertEqual(outputs["report_data"]["pdf_errors"][0]["reason"], "converter missing")
            self.assertFalse(
                any(
                    record.get("artifact_type") == "pdf"
                    for record in outputs["report_data"].get("document_verification", [])
                )
            )

            manual_gate = report_payload.get("manual_review_gate", {})
            self.assertEqual(manual_gate.get("generation_failure_count"), 1)
            self.assertEqual(manual_gate.get("blocked_count"), 1)
            self.assertEqual(len(manual_gate.get("generation_failures", [])), 1)
            self.assertEqual(manual_gate["generation_failures"][0]["artifact_path"], str(expected_pdf_path))
            self.assertEqual(manual_gate["generation_failures"][0]["blocking_stage"], "pdf_generation")
            self.assertIsNone(manual_gate["generation_failures"][0].get("verification_status"))

    def test_converter_success_and_failed_pdf_verification_blocks_pdf_via_document_verification_gate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            expected_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            write_minimal_pdf(expected_pdf_path, [""])

            outputs = self._run_document_generation(tmp_path, (expected_pdf_path, None))
            report_payload = self._load_json(outputs["report_path"])
            manual_gate = report_payload.get("manual_review_gate", {})

            self.assertEqual(outputs["report_data"]["pdf_errors"], [])
            self.assertTrue(
                any(
                    record.get("artifact_type") == "pdf"
                    and record.get("artifact_path") == str(expected_pdf_path)
                    and record.get("verification_status") == "failed"
                    for record in outputs["report_data"].get("document_verification", [])
                )
            )

            self.assertEqual(manual_gate.get("generation_failure_count"), 0)
            blocked_entry = self._find_pdf_gate_entry(manual_gate.get("blocked_artifacts", []), expected_pdf_path)
            self.assertIsNotNone(blocked_entry)
            self.assertEqual(blocked_entry.get("blocking_stage"), "document_verification")

    def test_converter_success_and_passing_pdf_verification_marks_pdf_ready_for_manual_review(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            expected_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            write_minimal_pdf(expected_pdf_path, "x" * 80)

            outputs = self._run_document_generation(tmp_path, (expected_pdf_path, None))
            report_payload = self._load_json(outputs["report_path"])
            manual_gate = report_payload.get("manual_review_gate", {})

            self.assertEqual(outputs["report_data"]["pdf_errors"], [])
            self.assertEqual(manual_gate.get("generation_failure_count"), 0)
            ready_entry = self._find_pdf_gate_entry(manual_gate.get("ready_artifacts", []), expected_pdf_path)
            self.assertIsNotNone(ready_entry)
            self.assertTrue(ready_entry.get("review_ready"))


if __name__ == "__main__":
    unittest.main()

