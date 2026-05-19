import unittest

from app.content_models import build_review_decision, compute_content_hash
from app.generation_filtering import evaluate_cached_content


class TestGenerationFiltering(unittest.TestCase):
    def test_clean_content_is_included_without_review_decision(self):
        result = evaluate_cached_content(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "First line\nSecond line",
        )

        self.assertTrue(result["included"])
        self.assertEqual(result["decision_source"], "quality_clean")
        self.assertEqual(result["quality"], "clean")
        self.assertIsNone(result["review_decision"])

    def test_questionable_content_is_excluded_by_default(self):
        result = evaluate_cached_content(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "Lyrics not found.",
        )

        self.assertFalse(result["included"])
        self.assertEqual(result["decision_source"], "default_exclude")
        self.assertEqual(result["quality"], "questionable")
        self.assertIsNone(result["review_decision"])

    def test_questionable_content_is_included_with_override(self):
        content = "Lyrics not found."
        review_decision = build_review_decision(
            "The Campfire Trio - Trail Song",
            "lyrics",
            compute_content_hash(content),
            "override",
            reason="Manually approved for printing.",
            decided_at="2026-05-19T15:00:34+01:00",
        )

        result = evaluate_cached_content(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            content,
            review_decision_record=review_decision,
        )

        self.assertTrue(result["included"])
        self.assertEqual(result["decision_source"], "review_override")
        self.assertEqual(result["review_decision"], review_decision)

    def test_reject_decision_excludes_clean_content(self):
        content = "First line\nSecond line"
        review_decision = build_review_decision(
            "The Campfire Trio - Trail Song",
            "lyrics",
            compute_content_hash(content),
            "reject",
            reason="Not suitable for printing.",
            decided_at="2026-05-19T15:00:34+01:00",
        )

        result = evaluate_cached_content(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            content,
            review_decision_record=review_decision,
        )

        self.assertFalse(result["included"])
        self.assertEqual(result["decision_source"], "review_reject")
        self.assertEqual(result["review_decision"], review_decision)

    def test_stale_review_decision_is_ignored(self):
        review_decision = build_review_decision(
            "The Campfire Trio - Trail Song",
            "lyrics",
            compute_content_hash("Reviewed content"),
            "accept",
            reason="Previously reviewed.",
            decided_at="2026-05-19T15:00:34+01:00",
        )

        result = evaluate_cached_content(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "Lyrics not found.",
            review_decision_record=review_decision,
        )

        self.assertFalse(result["included"])
        self.assertEqual(result["decision_source"], "default_exclude")
        self.assertEqual(result["quality"], "questionable")
        self.assertIsNone(result["review_decision"])


if __name__ == "__main__":
    unittest.main()
