import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.content_models import build_review_decision, compute_content_hash
from app.review_state import save_review_decisions
from app.selection_state import load_named_selection
from tests.docx_stub import install_docx_stub

install_docx_stub()

# pylint: disable=wrong-import-position
import app.document_creation as document_creation  # noqa: E402
from app.reporting import (  # noqa: E402
    build_traceable_quality_report,
    write_traceable_quality_report,
)


class TestE2EStory43SelectionGeneration(unittest.TestCase):
    def _load_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_named_selection_generation_applies_quality_rules_and_reports_exclusions(self):
        selection_payload = {
            "version": 1,
            "selection_name": "trip-night",
            "updated_at": "2026-05-19T15:14:19+01:00",
            "entries": [
                {"artist": "The Campfire Trio", "title": "Trail Song"},
                {"artist": "The Campfire Trio", "title": "Questionable Song"},
                {"artist": "The Campfire Trio", "title": "Missing Song"},
                {"artist": "The Campfire Trio", "title": "Override Song"},
            ],
        }

        lyrics_cache = {
            "The Campfire Trio - Trail Song": "First line\nSecond line",
            "The Campfire Trio - Questionable Song": "Lyrics not found.",
            "The Campfire Trio - Override Song": "Lyrics not found.",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            selection_path = tmp_path / "trip-night.json"
            selection_path.write_text(
                json.dumps(selection_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            original_selection_text = selection_path.read_text(encoding="utf-8")

            selection_state, selection_errors = load_named_selection(selection_path)
            self.assertEqual(selection_errors, [])
            selection_records = selection_state["entries"]

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

            output_path = tmp_path / "data" / "output" / "selection_lyrics.docx"
            reports_dir = tmp_path / "data" / "review" / "reports"

            with (
                patch.object(
                    document_creation,
                    "QUALITY_STATUS_PATH",
                    tmp_path / "data" / "review" / "quality_status.json",
                ),
                patch.object(document_creation, "REVIEW_DECISIONS_PATH", review_decisions_path),
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
            ):
                report_data = document_creation.create_document_from_cache(
                    [],
                    lyrics_cache,
                    {},
                    lyrics_output=str(output_path),
                    selection_records=selection_records,
                    report_source="generate_from_selection",
                )

            self.assertTrue(output_path.exists())
            markdown_path = output_path.with_suffix(".md")
            self.assertTrue(markdown_path.exists())

            markdown_text = markdown_path.read_text(encoding="utf-8")
            self.assertIn("Trail Song by The Campfire Trio", markdown_text)
            self.assertIn("Override Song by The Campfire Trio", markdown_text)
            self.assertNotIn("Questionable Song by The Campfire Trio", markdown_text)
            self.assertNotIn("Missing Song by The Campfire Trio", markdown_text)
            self.assertLess(
                markdown_text.index("Trail Song by The Campfire Trio"),
                markdown_text.index("Override Song by The Campfire Trio"),
            )

            report_entries = {entry["title"]: entry for entry in report_data["entries"]}
            self.assertTrue(report_entries["Trail Song"]["included"])
            self.assertFalse(report_entries["Questionable Song"]["included"])
            self.assertEqual(
                report_entries["Questionable Song"]["reason"],
                "Questionable content is excluded by default.",
            )
            self.assertFalse(report_entries["Missing Song"]["included"])
            self.assertEqual(
                report_entries["Missing Song"]["reason"],
                "Missing content is excluded by default.",
            )
            self.assertTrue(report_entries["Override Song"]["included"])
            self.assertEqual(report_entries["Override Song"]["decision_source"], "review_override")

            self.assertEqual(len(report_data["selection_issues"]), 1)
            self.assertEqual(report_data["selection_issues"][0]["issue_type"], "missing_content")
            self.assertEqual(
                report_data["selection_issues"][0]["song_key"],
                "The Campfire Trio - Missing Song",
            )
            self.assertEqual(report_data["source"], "generate_from_selection")

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
            report_payload = self._load_json(report_path)

            self.assertEqual(report_payload["summary"]["selection_issue_count"], 1)
            self.assertEqual(len(report_payload.get("selection_issues", [])), 1)
            self.assertEqual(
                report_payload["selection_issues"][0]["song_key"],
                "The Campfire Trio - Missing Song",
            )
            self.assertTrue(
                any(
                    song.get("song_key") == "The Campfire Trio - Override Song"
                    and song.get("decision_source") == "review_override"
                    for song in report_payload.get("songs", [])
                )
            )

            self.assertEqual(selection_path.read_text(encoding="utf-8"), original_selection_text)


if __name__ == "__main__":
    unittest.main()
