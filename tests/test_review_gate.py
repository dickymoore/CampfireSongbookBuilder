import unittest

from app.document_verification import build_document_verification_record
from app.review_gate import (
    build_review_gate_decision,
    compute_review_gate_decision,
    compute_review_gate_decisions,
)


class TestReviewGate(unittest.TestCase):
    def test_compute_review_gate_decision_marks_passed_artifact_review_ready(self):
        verification_record = build_document_verification_record(
            artifact_path="data/output/Lyrics_Document.md",
            artifact_type="markdown",
            verification_status="passed",
            verification_reasons=["meets_neatness_thresholds"],
            verified_at="2026-05-22T17:02:00+01:00",
        )

        decision = compute_review_gate_decision(
            verification_record,
            computed_at="2026-05-22T17:03:00+01:00",
        )

        self.assertEqual(
            decision,
            build_review_gate_decision(
                artifact_path="data/output/Lyrics_Document.md",
                artifact_type="markdown",
                review_ready=True,
                failure_reasons=[],
                computed_at="2026-05-22T17:03:00+01:00",
            ),
        )

    def test_compute_review_gate_decision_preserves_failure_reasons(self):
        verification_record = build_document_verification_record(
            artifact_path="data/output/Lyrics_Document.docx",
            artifact_type="docx",
            verification_status="failed",
            verification_reasons=["sparse_layout", "fragmented_song_blocks"],
            verified_at="2026-05-22T17:02:00+01:00",
        )

        decision = compute_review_gate_decision(
            verification_record,
            computed_at="2026-05-22T17:03:00+01:00",
        )

        self.assertFalse(decision["review_ready"])
        self.assertEqual(
            decision["failure_reasons"],
            ["sparse_layout", "fragmented_song_blocks"],
        )
        self.assertEqual(decision["artifact_type"], "docx")

    def test_compute_review_gate_decisions_preserves_input_order(self):
        records = [
            build_document_verification_record(
                artifact_path="data/output/Lyrics_Document.md",
                artifact_type="markdown",
                verification_status="passed",
                verification_reasons=["meets_neatness_thresholds"],
                verified_at="2026-05-22T17:02:00+01:00",
            ),
            build_document_verification_record(
                artifact_path="data/output/Lyrics_Document.docx",
                artifact_type="docx",
                verification_status="failed",
                verification_reasons=["sparse_layout"],
                verified_at="2026-05-22T17:02:00+01:00",
            ),
        ]

        decisions = compute_review_gate_decisions(
            records,
            computed_at="2026-05-22T17:03:00+01:00",
        )

        self.assertEqual(
            [decision["artifact_path"] for decision in decisions],
            [
                "data/output/Lyrics_Document.md",
                "data/output/Lyrics_Document.docx",
            ],
        )


if __name__ == "__main__":
    unittest.main()
