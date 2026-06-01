import tempfile
import unittest
from pathlib import Path

from app.review_gate import build_review_gate_decision
from app.review_gate_state import (
    load_review_gate_state,
    refresh_review_gate_state,
    save_review_gate_state,
)


class TestReviewGateState(unittest.TestCase):
    def test_refresh_replaces_existing_decision_for_same_artifact_identity(self):
        original = build_review_gate_decision(
            artifact_path="data/output/Lyrics_Document.md",
            artifact_type="markdown",
            review_ready=False,
            failure_reasons=["print_hostile_structure"],
            computed_at="2026-05-21T16:00:00+01:00",
        )
        refreshed = build_review_gate_decision(
            artifact_path="data/output/Lyrics_Document.md",
            artifact_type="markdown",
            review_ready=True,
            failure_reasons=[],
            computed_at="2026-05-21T17:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_gate_decisions.json"
            save_review_gate_state(target_path, [original])

            refresh_review_gate_state(
                target_path,
                [refreshed],
                updated_at="2026-05-21T17:00:00+01:00",
            )

            state, errors = load_review_gate_state(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                state["entries"]["data/output/Lyrics_Document.md"]["markdown"],
                refreshed,
            )
            self.assertEqual(state["updated_at"], "2026-05-21T17:00:00+01:00")

    def test_state_distinguishes_same_path_different_types(self):
        docx = build_review_gate_decision(
            artifact_path="data/output/Artifact",
            artifact_type="docx",
            review_ready=True,
            failure_reasons=[],
            computed_at="2026-05-21T16:00:00+01:00",
        )
        pdf = build_review_gate_decision(
            artifact_path="data/output/Artifact",
            artifact_type="pdf",
            review_ready=False,
            failure_reasons=["missing_pdf"],
            computed_at="2026-05-21T16:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_gate_decisions.json"
            save_review_gate_state(target_path, [docx, pdf])

            state, errors = load_review_gate_state(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(set(state["entries"]["data/output/Artifact"].keys()), {"docx", "pdf"})

    def test_refresh_does_not_remove_other_types_for_same_path(self):
        docx_original = build_review_gate_decision(
            artifact_path="data/output/Artifact",
            artifact_type="docx",
            review_ready=False,
            failure_reasons=["print_hostile_structure"],
            computed_at="2026-05-21T16:00:00+01:00",
        )
        pdf_original = build_review_gate_decision(
            artifact_path="data/output/Artifact",
            artifact_type="pdf",
            review_ready=False,
            failure_reasons=["missing_pdf"],
            computed_at="2026-05-21T16:00:00+01:00",
        )
        docx_refreshed = build_review_gate_decision(
            artifact_path="data/output/Artifact",
            artifact_type="docx",
            review_ready=True,
            failure_reasons=[],
            computed_at="2026-05-21T17:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_gate_decisions.json"
            save_review_gate_state(target_path, [docx_original, pdf_original])

            refresh_review_gate_state(
                target_path,
                [docx_refreshed],
                updated_at="2026-05-21T17:00:00+01:00",
            )

            state, errors = load_review_gate_state(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(
                state["entries"]["data/output/Artifact"]["docx"],
                docx_refreshed,
            )
            self.assertEqual(
                state["entries"]["data/output/Artifact"]["pdf"],
                pdf_original,
            )

    def test_refresh_can_remove_stale_decisions(self):
        decision = build_review_gate_decision(
            artifact_path="data/output/Lyrics_Document.md",
            artifact_type="markdown",
            review_ready=False,
            failure_reasons=["print_hostile_structure"],
            computed_at="2026-05-21T16:00:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_gate_decisions.json"
            save_review_gate_state(target_path, [decision])

            refresh_review_gate_state(
                target_path,
                [],
                remove_artifact_paths=["data/output/Lyrics_Document.md"],
                updated_at="2026-05-21T17:00:00+01:00",
            )

            state, errors = load_review_gate_state(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["entries"], {})
