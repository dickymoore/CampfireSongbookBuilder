import unittest

from app.content_scoring import (
    SCORE_VERSION_V1,
    build_content_score,
    compose_content_score,
    compose_content_scores,
    quality_band_for_score,
)
from app.content_models import build_quality_status, build_quality_signal


class TestContentScoring(unittest.TestCase):
    def _build_quality_status(self, artist, title, content_type, content_hash, quality, signals=None):
        return build_quality_status(
            artist,
            title,
            content_type,
            content_hash,
            quality,
            signals=signals or [],
            assessed_at="2026-05-23T19:00:00+01:00",
        )

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

    def test_compose_content_score_keeps_clean_records_at_top_band(self):
        quality_status = self._build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "clean",
            signals=[],
        )

        score = compose_content_score(
            quality_status,
            scored_at="2026-05-23T19:01:00+01:00",
        )

        self.assertEqual(score["quality_score"], 100)
        self.assertEqual(score["quality_band"], "clean")
        self.assertEqual(score["score_reasons"], [])

    def test_compose_content_score_uses_existing_signals_for_reviewable_and_questionable_outcomes(self):
        reviewable_status = self._build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "questionable",
            signals=[],
        )
        questionable_status = self._build_quality_status(
            "The Campfire Trio",
            "Night Run",
            "lyrics",
            "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            "questionable",
            signals=[
                build_quality_signal(
                    "print_hostile_content",
                    "warning",
                    "Content is likely too long for comfortable printing.",
                    "lyrics",
                )
            ],
        )

        reviewable_score = compose_content_score(reviewable_status)
        questionable_score = compose_content_score(questionable_status)

        self.assertEqual(reviewable_score["quality_band"], "reviewable")
        self.assertEqual(reviewable_score["quality_score"], 70)
        self.assertEqual(reviewable_score["score_reasons"], ["quality:questionable"])
        self.assertEqual(questionable_score["quality_band"], "questionable")
        self.assertIn("quality:questionable", questionable_score["score_reasons"])
        self.assertIn("signal:print_hostile_content", questionable_score["score_reasons"])

    def test_compose_content_score_marks_missing_content_poor(self):
        quality_status = self._build_quality_status(
            "The Campfire Trio",
            "Missing Song",
            "chords",
            "sha256:4444444444444444444444444444444444444444444444444444444444444444",
            "missing",
            signals=[
                build_quality_signal(
                    "missing_chords",
                    "error",
                    "Chords are missing or unusable.",
                    "chords",
                )
            ],
        )

        score = compose_content_score(quality_status)

        self.assertEqual(score["quality_score"], 0)
        self.assertEqual(score["quality_band"], "poor")
        self.assertEqual(
            score["score_reasons"],
            ["quality:missing", "signal:missing_chords"],
        )

    def test_compose_content_score_allows_lyrics_and_chords_to_diverge(self):
        lyrics_status = self._build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:5555555555555555555555555555555555555555555555555555555555555555",
            "questionable",
            signals=[
                build_quality_signal(
                    "low_confidence_match",
                    "warning",
                    "Source artist does not match the requested song.",
                    "lyrics",
                )
            ],
        )
        chords_status = self._build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "chords",
            "sha256:6666666666666666666666666666666666666666666666666666666666666666",
            "questionable",
            signals=[
                build_quality_signal(
                    "low_confidence_match",
                    "warning",
                    "Source artist does not match the requested song.",
                    "chords",
                )
            ],
        )

        lyrics_score = compose_content_score(lyrics_status)
        chords_score = compose_content_score(chords_status)

        self.assertNotEqual(lyrics_score["quality_score"], chords_score["quality_score"])
        self.assertLess(lyrics_score["quality_score"], chords_score["quality_score"])

    def test_compose_content_scores_is_deterministic_for_identical_inputs(self):
        quality_status = self._build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:7777777777777777777777777777777777777777777777777777777777777777",
            "questionable",
            signals=[
                build_quality_signal(
                    "html_residue",
                    "warning",
                    "HTML residue was detected in the source text.",
                    "lyrics",
                ),
                build_quality_signal(
                    "low_confidence_match",
                    "warning",
                    "Source artist does not match the requested song.",
                    "lyrics",
                ),
            ],
        )

        first = compose_content_scores(
            [quality_status],
            scored_at="2026-05-23T19:01:00+01:00",
        )
        second = compose_content_scores(
            [quality_status],
            scored_at="2026-05-23T19:01:00+01:00",
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
