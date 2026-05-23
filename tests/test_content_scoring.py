import unittest

from app.content_scoring import (
    SCORE_VERSION_V1,
    build_content_score,
    quality_band_for_score,
)


class TestContentScoring(unittest.TestCase):
    def test_build_content_score_preserves_identity_and_defaults_band(self):
        score = build_content_score(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            82,
            score_reasons=["missing_structure_signal"],
            scored_at="2026-05-23T19:00:00+01:00",
        )

        self.assertEqual(score["song_key"], "The Campfire Trio - Trail Song")
        self.assertEqual(score["quality_score"], 82)
        self.assertEqual(score["quality_band"], "reviewable")
        self.assertEqual(score["score_version"], SCORE_VERSION_V1)
        self.assertEqual(score["score_reasons"], ["missing_structure_signal"])

    def test_quality_band_for_score_uses_v1_thresholds(self):
        self.assertEqual(quality_band_for_score(100), "clean")
        self.assertEqual(quality_band_for_score(85), "clean")
        self.assertEqual(quality_band_for_score(84), "reviewable")
        self.assertEqual(quality_band_for_score(60), "reviewable")
        self.assertEqual(quality_band_for_score(59), "questionable")
        self.assertEqual(quality_band_for_score(40), "questionable")
        self.assertEqual(quality_band_for_score(39), "poor")
        self.assertEqual(quality_band_for_score(0), "poor")

    def test_build_content_score_rejects_band_mismatch(self):
        with self.assertRaises(ValueError):
            build_content_score(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                82,
                quality_band="clean",
                score_reasons=[],
                scored_at="2026-05-23T19:00:00+01:00",
            )


if __name__ == "__main__":
    unittest.main()
