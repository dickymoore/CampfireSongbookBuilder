import unittest

from app.content_models import (
    CONTENT_TYPES,
    QUALITY_VALUES,
    REVIEW_DECISIONS,
    SIGNAL_SEVERITIES,
    SOURCE_OUTCOMES,
    build_candidate_record,
    build_favourite_record,
    build_quality_signal,
    build_quality_status,
    build_review_decision,
    build_source_attempt_record,
    compute_content_hash,
    derive_song_key,
    validate_content_hash,
    validate_content_type,
    validate_quality,
    validate_review_decision,
    validate_severity,
    validate_source_outcome,
)


class TestContentModels(unittest.TestCase):
    def test_derive_song_key_preserves_exact_values(self):
        artist = "  The Campfire Band "
        title = "Singalong Night  "

        self.assertEqual(derive_song_key(artist, title), "  The Campfire Band  - Singalong Night  ")

    def test_compute_content_hash_uses_sha256_prefix(self):
        content_hash = compute_content_hash("hello campfire")

        self.assertTrue(content_hash.startswith("sha256:"))
        self.assertEqual(len(content_hash), len("sha256:") + 64)
        self.assertEqual(
            content_hash,
            "sha256:a4f430ef835d3970f18823c39d98e9577e3a3b0b571ffce09acddb9579058cd2",
        )

    def test_build_candidate_record_includes_expected_contract_fields(self):
        candidate = build_candidate_record(
            artist="The Campfire Band",
            title="Singalong Night",
            content_type="lyrics",
            source="genius",
            content="First line\nSecond line",
            source_artist=None,
            source_title=None,
            status="candidate",
            error=None,
            retrieved_at="2026-05-19T13:00:00+01:00",
        )

        self.assertEqual(candidate["artist"], "The Campfire Band")
        self.assertEqual(candidate["title"], "Singalong Night")
        self.assertEqual(candidate["song_key"], "The Campfire Band - Singalong Night")
        self.assertEqual(candidate["content_type"], "lyrics")
        self.assertEqual(candidate["source"], "genius")
        self.assertEqual(candidate["content"], "First line\nSecond line")
        self.assertEqual(candidate["content_hash"], compute_content_hash("First line\nSecond line"))
        self.assertIsNone(candidate["source_artist"])
        self.assertIsNone(candidate["source_title"])
        self.assertEqual(candidate["status"], "candidate")
        self.assertIsNone(candidate["error"])
        self.assertEqual(candidate["retrieved_at"], "2026-05-19T13:00:00+01:00")

    def test_build_favourite_record_preserves_exact_identity_and_derives_song_key(self):
        favourite = build_favourite_record(
            "  The Campfire Band ",
            "Singalong Night  ",
        )

        self.assertEqual(
            favourite,
            {
                "artist": "  The Campfire Band ",
                "title": "Singalong Night  ",
                "song_key": "  The Campfire Band  - Singalong Night  ",
            },
        )

    def test_build_favourite_record_rejects_mismatched_song_key(self):
        with self.assertRaises(ValueError):
            build_favourite_record(
                "The Campfire Band",
                "Singalong Night",
                song_key="Other Artist - Other Song",
            )

    def test_build_quality_signal_uses_known_fields(self):
        signal = build_quality_signal(
            code="missing_chords",
            severity="error",
            message="Chords are missing or unusable.",
            content_type="chords",
        )

        self.assertEqual(
            signal,
            {
                "code": "missing_chords",
                "severity": "error",
                "message": "Chords are missing or unusable.",
                "content_type": "chords",
            },
        )

    def test_build_quality_status_includes_signals_and_hash(self):
        signal = build_quality_signal(
            code="missing_lyrics",
            severity="warning",
            message="Lyrics were not found.",
            content_type="lyrics",
        )
        status = build_quality_status(
            artist="The Campfire Band",
            title="Singalong Night",
            content_type="lyrics",
            content_hash=compute_content_hash("First line\nSecond line"),
            quality="questionable",
            signals=[signal],
            assessed_at="2026-05-19T13:00:00+01:00",
        )

        self.assertEqual(status["song_key"], "The Campfire Band - Singalong Night")
        self.assertEqual(status["quality"], "questionable")
        self.assertEqual(status["signals"], [signal])
        self.assertEqual(status["assessed_at"], "2026-05-19T13:00:00+01:00")

    def test_build_quality_status_rejects_malformed_signal(self):
        with self.assertRaises(ValueError):
            build_quality_status(
                artist="The Campfire Band",
                title="Singalong Night",
                content_type="lyrics",
                content_hash="sha256:1234",
                quality="questionable",
                signals=[{"code": "missing_lyrics"}],
                assessed_at=None,
            )

    def test_build_review_decision_uses_hash_bound_contract(self):
        expected_hash = compute_content_hash("Manually reviewed and playable.")
        decision = build_review_decision(
            song_key="The Campfire Band - Singalong Night",
            content_type="chords",
            content_hash=expected_hash,
            decision="accept",
            reason="Manually reviewed and playable.",
            decided_at="2026-05-19T13:00:00+01:00",
        )

        self.assertEqual(
            decision,
            {
                "song_key": "The Campfire Band - Singalong Night",
                "content_type": "chords",
                "content_hash": expected_hash,
                "decision": "accept",
                "reason": "Manually reviewed and playable.",
                "decided_at": "2026-05-19T13:00:00+01:00",
            },
        )

    def test_build_source_attempt_record_uses_exact_identity_and_status_contract(self):
        attempt = build_source_attempt_record(
            artist="The Campfire Band",
            title="Trail Song",
            content_type="lyrics",
            source="Genius",
            status="candidate",
            error=None,
            retrieved_at="2026-05-19T14:13:56+01:00",
        )

        self.assertEqual(
            attempt,
            {
                "artist": "The Campfire Band",
                "title": "Trail Song",
                "song_key": "The Campfire Band - Trail Song",
                "content_type": "lyrics",
                "source": "Genius",
                "status": "candidate",
                "error": None,
                "retrieved_at": "2026-05-19T14:13:56+01:00",
            },
        )

    def test_build_review_decision_rejects_invalid_content_hash(self):
        with self.assertRaises(ValueError):
            build_review_decision(
                song_key="The Campfire Band - Singalong Night",
                content_type="chords",
                content_hash="sha256:abcd",
                decision="accept",
                reason=None,
                decided_at=None,
            )

    def test_validate_helpers_accept_known_contract_values(self):
        self.assertEqual(validate_content_type("lyrics"), "lyrics")
        self.assertEqual(validate_quality("clean"), "clean")
        self.assertEqual(validate_review_decision("override"), "override")
        self.assertEqual(validate_severity("warning"), "warning")
        self.assertEqual(validate_source_outcome("not_found"), "not_found")
        self.assertEqual(
            validate_content_hash(
                "sha256:a4f430ef835d3970f18823c39d98e9577e3a3b0b571ffce09acddb9579058cd2"
            ),
            "sha256:a4f430ef835d3970f18823c39d98e9577e3a3b0b571ffce09acddb9579058cd2",
        )

    def test_validate_helpers_reject_invalid_values(self):
        with self.assertRaises(ValueError):
            validate_content_type("tabs")

        with self.assertRaises(ValueError):
            validate_quality("great")

        with self.assertRaises(ValueError):
            validate_review_decision("maybe")

        with self.assertRaises(ValueError):
            validate_severity("fatal")

        with self.assertRaises(ValueError):
            validate_source_outcome("pending")

        with self.assertRaises(ValueError):
            validate_content_hash("sha256:abcd")

    def test_contract_constant_sets_cover_expected_values(self):
        self.assertEqual(CONTENT_TYPES, ("lyrics", "chords"))
        self.assertEqual(QUALITY_VALUES, ("clean", "questionable", "missing"))
        self.assertEqual(REVIEW_DECISIONS, ("accept", "reject", "override"))
        self.assertEqual(SIGNAL_SEVERITIES, ("info", "warning", "error"))
        self.assertEqual(SOURCE_OUTCOMES, ("candidate", "not_found", "error"))


if __name__ == "__main__":
    unittest.main()
