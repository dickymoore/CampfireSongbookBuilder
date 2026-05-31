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


class TestE2EStory43PdfReviewGate(unittest.TestCase):
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

    def _find_pdf_decision(self, decisions, artifact_path):
        for decision in decisions:
            if (
                decision.get("artifact_type") == "pdf"
                and decision.get("artifact_path") == str(artifact_path)
            ):
                return decision
        return None

    def test_pdf_verification_passed_marks_pdf_review_ready_in_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            expected_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            write_minimal_pdf(expected_pdf_path, "x" * 80)

            outputs = self._run_document_generation(tmp_path, (expected_pdf_path, None))

            report_payload = self._load_json(outputs["report_path"])
            decisions = report_payload.get("review_gate_decisions", [])
            manual_gate = report_payload.get("manual_review_gate", {})

            verification_types = [
                record.get("artifact_type")
                for record in outputs["report_data"]["document_verification"]
            ]
            decision_types = [
                decision.get("artifact_type")
                for decision in outputs["report_data"]["review_gate_decisions"]
            ]
            self.assertEqual(
                verification_types,
                decision_types,
            )
            self.assertEqual(
                decision_types,
                ["markdown", "docx", "pdf"],
            )

            pdf_decision = self._find_pdf_decision(decisions, expected_pdf_path)
            self.assertIsNotNone(pdf_decision)
            self.assertTrue(pdf_decision["review_ready"])
            self.assertEqual(pdf_decision["failure_reasons"], [])

            ready_paths = [
                item.get("artifact_path") for item in manual_gate.get("ready_artifacts", [])
            ]
            blocked_paths = [
                item.get("artifact_path") for item in manual_gate.get("blocked_artifacts", [])
            ]
            self.assertIn(str(expected_pdf_path), ready_paths)
            self.assertNotIn(str(expected_pdf_path), blocked_paths)

    def test_pdf_verification_failed_marks_pdf_not_review_ready_with_reasons_in_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            expected_pdf_path = tmp_path / "data" / "output" / "Lyrics_Document.pdf"
            expected_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            write_minimal_pdf(expected_pdf_path, "")

            outputs = self._run_document_generation(tmp_path, (expected_pdf_path, None))

            report_payload = self._load_json(outputs["report_path"])
            decisions = report_payload.get("review_gate_decisions", [])
            manual_gate = report_payload.get("manual_review_gate", {})

            pdf_decision = self._find_pdf_decision(decisions, expected_pdf_path)
            self.assertIsNotNone(pdf_decision)
            self.assertFalse(pdf_decision["review_ready"])
            self.assertEqual(
                pdf_decision["failure_reasons"],
                ["text_extraction_failed", "sparse_pages"],
            )

            blocked_entries = [
                item
                for item in manual_gate.get("blocked_artifacts", [])
                if (
                    item.get("artifact_type") == "pdf"
                    and item.get("artifact_path") == str(expected_pdf_path)
                )
            ]
            self.assertEqual(len(blocked_entries), 1)

            blocked_entry = blocked_entries[0]
            self.assertEqual(blocked_entry["verification_status"], "failed")
            self.assertEqual(
                blocked_entry["verification_reasons"],
                ["text_extraction_failed", "sparse_pages"],
            )
            self.assertEqual(
                blocked_entry["failure_reasons"],
                ["text_extraction_failed", "sparse_pages"],
            )


if __name__ == "__main__":
    unittest.main()
