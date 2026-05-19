import unittest

from app.content_models import build_candidate_record, build_quality_signal
from app import quality_assessment
from app.quality_assessment import (
    assess_candidate_quality,
    assess_junk_content,
    assess_missing_content,
    assess_low_confidence_candidate,
    assess_print_hostile_and_low_confidence,
    assess_print_hostile_content,
)


class TestQualityAssessment(unittest.TestCase):
    def test_missing_inputs_mark_quality_missing_for_both_content_types(self):
        cases = [
            ("lyrics", "", "missing_lyrics", "Lyrics are missing or unusable."),
            ("lyrics", "   ", "missing_lyrics", "Lyrics are missing or unusable."),
            ("lyrics", None, "missing_lyrics", "Lyrics are missing or unusable."),
            ("lyrics", 42, "missing_lyrics", "Lyrics are missing or unusable."),
            ("chords", "", "missing_chords", "Chords are missing or unusable."),
            ("chords", "   ", "missing_chords", "Chords are missing or unusable."),
            ("chords", None, "missing_chords", "Chords are missing or unusable."),
            ("chords", 42, "missing_chords", "Chords are missing or unusable."),
        ]

        for content_type, content, code, message in cases:
            with self.subTest(content_type=content_type, content=content):
                result = assess_missing_content(content_type, content)

                self.assertEqual(result["quality"], "missing")
                self.assertEqual(
                    result["signals"],
                    [build_quality_signal(code, "error", message, content_type)],
                )

    def test_exact_sentinel_values_mark_quality_questionable(self):
        cases = [
            ("lyrics", "Lyrics not found.", "unusable_lyrics", "Lyrics were not found."),
            ("chords", "Chords not found.", "unusable_chords", "Chords were not found."),
        ]

        for content_type, content, code, message in cases:
            with self.subTest(content_type=content_type):
                result = assess_missing_content(content_type, content)

                self.assertEqual(result["quality"], "questionable")
                self.assertEqual(
                    result["signals"],
                    [build_quality_signal(code, "warning", message, content_type)],
                )

    def test_mismatched_sentinel_values_are_not_mislabeled(self):
        result = assess_missing_content("lyrics", "Chords not found.")

        self.assertEqual(result, {"quality": "clean", "signals": []})

    def test_valid_content_stays_clean_with_no_signals(self):
        cases = [
            ("lyrics", "This is a verse with lyrics."),
            ("chords", "[G]This is a chord line."),
            ("chords", "[G] [D] [Em] [C]"),
        ]

        for content_type, content in cases:
            with self.subTest(content_type=content_type):
                original = content
                result = assess_missing_content(content_type, content)

                self.assertEqual(content, original)
                self.assertEqual(result, {"quality": "clean", "signals": []})

    def test_print_hostile_content_stays_clean_at_thresholds(self):
        content = "\n".join(
            "Line {}".format(index)
            for index in range(quality_assessment.PRINT_HOSTILE_LINE_COUNT_LIMIT)
        )
        result = assess_print_hostile_content("lyrics", content)

        self.assertEqual(result["quality"], "clean")
        self.assertEqual(result["signals"], [])
        self.assertEqual(
            result["summary"]["line_count"],
            quality_assessment.PRINT_HOSTILE_LINE_COUNT_LIMIT,
        )
        self.assertFalse(result["summary"]["has_print_hostile_content"])

    def test_print_hostile_content_reports_warning_when_thresholds_exceeded(self):
        content = "\n".join(
            "Line {}".format(index)
            for index in range(quality_assessment.PRINT_HOSTILE_LINE_COUNT_LIMIT + 1)
        )
        result = assess_print_hostile_content("chords", content)

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "print_hostile_content",
                    "warning",
                    "Content is likely too long for comfortable printing.",
                    "chords",
                )
            ],
        )
        self.assertTrue(result["summary"]["has_print_hostile_content"])

    def test_print_hostile_content_counts_blank_lines_toward_page_pressure(self):
        content = "Verse\n" + ("\n" * 200) + "Chorus"
        result = assess_print_hostile_content("lyrics", content)

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "print_hostile_content",
                    "warning",
                    "Content is likely too long for comfortable printing.",
                    "lyrics",
                )
            ],
        )
        self.assertEqual(result["summary"]["line_count"], 202)

    def test_low_confidence_candidate_reports_source_mismatch(self):
        candidate = build_candidate_record(
            "Campfire Band",
            "Trail Song",
            "lyrics",
            "genius",
            "Short content",
            source_artist="Other Band",
            source_title="Trail Song",
        )
        result = assess_low_confidence_candidate(candidate)

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "low_confidence_match",
                    "warning",
                    "Source artist does not match the requested song.",
                    "lyrics",
                )
            ],
        )
        self.assertTrue(result["summary"]["has_low_confidence_match"])
        self.assertTrue(result["summary"]["artist_mismatch"])
        self.assertFalse(result["summary"]["title_mismatch"])

    def test_combined_print_hostile_and_low_confidence_signals_are_stable(self):
        content = "\n".join(
            "Line {}".format(index)
            for index in range(quality_assessment.PRINT_HOSTILE_LINE_COUNT_LIMIT + 1)
        )
        candidate = build_candidate_record(
            "Campfire Band",
            "Trail Song",
            "lyrics",
            "genius",
            content,
            source_artist="Other Band",
            source_title="Trail Song",
        )
        original = candidate["content"]
        result = assess_print_hostile_and_low_confidence(candidate)

        self.assertEqual(candidate["content"], original)
        self.assertEqual(
            [signal["code"] for signal in result["signals"]],
            ["print_hostile_content", "low_confidence_match"],
        )
        self.assertEqual(result["quality"], "questionable")
        self.assertTrue(result["summary"]["has_print_hostile_content"])
        self.assertTrue(result["summary"]["has_low_confidence_match"])

    def test_candidate_quality_composes_missing_junk_print_and_confidence_signals(self):
        candidate = {
            "artist": "Campfire Band",
            "title": "Trail Song",
            "content_type": "lyrics",
            "content": "<div>Verse</div>\nFrom: someone@example.com\n" + "\n".join(
                "Line {}".format(index) for index in range(quality_assessment.PRINT_HOSTILE_LINE_COUNT_LIMIT + 1)
            ),
            "source_artist": "Other Band",
            "source_title": "Trail Song",
        }

        result = assess_candidate_quality(candidate)

        self.assertEqual(result["quality"], "questionable")
        self.assertIn("has_html_residue", result["summary"])
        self.assertIn("has_print_hostile_content", result["summary"])
        self.assertIn("has_low_confidence_match", result["summary"])
        self.assertGreaterEqual(len(result["signals"]), 3)

    def test_junk_residue_and_header_artifacts_emit_warning_signals(self):
        content = "<div>Verse</div>\nFrom: someone@example.com\nLine"
        result = assess_junk_content("lyrics", content)

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            [signal["code"] for signal in result["signals"]],
            ["html_residue", "email_header_artifacts"],
        )
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "html_residue",
                    "warning",
                    "HTML residue was detected in the source text.",
                    "lyrics",
                ),
                build_quality_signal(
                    "email_header_artifacts",
                    "warning",
                    "Email or header artifacts were detected in the source text.",
                    "lyrics",
                ),
            ],
        )
        self.assertEqual(result["summary"]["has_html_residue"], True)
        self.assertEqual(result["summary"]["has_email_header_artifacts"], True)

    def test_duplicate_blocks_mark_content_as_missing(self):
        content = "Verse 1\nLine A\nVerse 2\nLine B\nVerse 1\nLine A"
        result = assess_junk_content("chords", content)

        self.assertEqual(result["quality"], "missing")
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "duplicate_block",
                    "error",
                    "Repeated blocks make the content difficult to trust.",
                    "chords",
                )
            ],
        )
        self.assertEqual(result["summary"]["has_duplicate_block"], True)

    def test_bracket_noise_is_reported_with_stable_summary(self):
        content = "[ch][tab][intro]\nG C D"
        result = assess_junk_content("lyrics", content)

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            result["signals"],
            [
                build_quality_signal(
                    "excessive_bracket_noise",
                    "warning",
                    "Bracket noise makes the content hard to read.",
                    "lyrics",
                )
            ],
        )
        self.assertEqual(result["summary"]["has_excessive_bracket_noise"], True)
        self.assertEqual(result["summary"]["bracket_tag_count"], 3)

    def test_numeric_html_entities_are_reported_as_residue(self):
        result = assess_junk_content("lyrics", "Verse &#39;one&#39;")

        self.assertEqual(result["quality"], "questionable")
        self.assertEqual(
            [signal["code"] for signal in result["signals"]],
            ["html_residue"],
        )

    def test_mixed_junk_inputs_trigger_multiple_signals_in_stable_order(self):
        content = (
            "<p>Verse</p>\n"
            "From: someone@example.com\n"
            "Verse line\n"
            "Verse line\n"
            "[ch][tab][intro]"
        )
        original = content
        result = assess_junk_content("lyrics", content)

        self.assertEqual(content, original)
        self.assertEqual(
            [signal["code"] for signal in result["signals"]],
            [
                "html_residue",
                "email_header_artifacts",
                "duplicate_block",
                "excessive_bracket_noise",
            ],
        )
        self.assertEqual(result["quality"], "missing")
        self.assertEqual(result["summary"]["line_count"], 5)

    def test_valid_content_stays_clean_with_no_junk_signals(self):
        result = assess_junk_content("lyrics", "This is a verse with lyrics.")

        self.assertEqual(
            result,
            {
                "quality": "clean",
                "signals": [],
                "summary": {
                    "line_count": 1,
                    "bracket_tag_count": 0,
                    "bracket_char_count": 0,
                    "has_html_residue": False,
                    "has_email_header_artifacts": False,
                    "has_duplicate_block": False,
                    "has_excessive_bracket_noise": False,
                },
            },
        )

    def test_invalid_content_type_fails_fast(self):
        with self.assertRaises(ValueError):
            assess_missing_content("tabs", "Lyrics not found.")

        with self.assertRaises(ValueError):
            assess_junk_content("tabs", "<div>Verse</div>")

        with self.assertRaises(ValueError):
            assess_print_hostile_content("tabs", "Line 1")

        with self.assertRaises(ValueError):
            assess_low_confidence_candidate(
                {
                    "artist": "Campfire Band",
                    "title": "Trail Song",
                    "content_type": "tabs",
                    "source_artist": "Other Band",
                    "source_title": "Trail Song",
                }
            )

    def test_result_shape_is_stable(self):
        result = assess_missing_content("lyrics", "")

        self.assertEqual(set(result.keys()), {"quality", "signals"})
        self.assertEqual(
            set(result["signals"][0].keys()),
            {"code", "severity", "message", "content_type"},
        )


if __name__ == "__main__":
    unittest.main()
