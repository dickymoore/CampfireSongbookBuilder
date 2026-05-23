import json
import tempfile
import unittest
from pathlib import Path

from app.content_models import build_quality_status
from app.content_models import build_review_decision, compute_content_hash
from app.content_scoring import build_content_score
from app.review_state import (
    load_content_scores,
    load_quality_status,
    load_review_decisions,
    save_content_scores,
    save_quality_status,
    save_review_decisions,
)


class TestReviewState(unittest.TestCase):
    def _build_status(self, artist, title, content_type, content, quality, signals=None):
        return build_quality_status(
            artist,
            title,
            content_type,
            content,
            quality,
            signals=signals,
            assessed_at="2026-05-19T14:03:45+01:00",
        )

    def test_save_and_load_quality_status_round_trip(self):
        lyric_status = self._build_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "clean",
            signals=[
                {
                    "code": "clean_lyrics",
                    "severity": "info",
                    "message": "Lyrics look clean.",
                    "content_type": "lyrics",
                }
            ],
        )
        chord_status = self._build_status(
            "The Campfire Trio",
            "Trail Song",
            "chords",
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "questionable",
            signals=[
                {
                    "code": "print_hostile_content",
                    "severity": "warning",
                    "message": "Chords are likely too long for comfortable printing.",
                    "content_type": "chords",
                }
            ],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"

            save_quality_status(target_path, [lyric_status, chord_status])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())

            state, errors = load_quality_status(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["lyrics"], lyric_status)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["chords"], chord_status)

    def test_load_missing_quality_status_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"

            state, errors = load_quality_status(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertIsNone(state["updated_at"])
            self.assertEqual(state["entries"], {})

    def test_load_malformed_quality_status_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("{not valid json", encoding="utf-8")

            state, errors = load_quality_status(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(errors[0]["field"], "$")
            self.assertIn("JSON", errors[0]["reason"])

    def test_load_missing_entries_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                json.dumps({"version": 1, "updated_at": "2026-05-19T14:03:45+01:00"}),
                encoding="utf-8",
            )

            state, errors = load_quality_status(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(errors[0]["field"], "entries")
            self.assertIn("required", errors[0]["reason"])

    def test_load_invalid_nested_entry_reports_field_path_and_preserves_valid_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            valid_status = self._build_status(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",
                "clean",
            )
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "lyrics": valid_status,
                        "chords": {
                            "artist": "The Campfire Trio",
                            "title": "Trail Song",
                            "song_key": "The Campfire Trio - Trail Song",
                            "content_type": "chords",
                            "content_hash": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
                            "quality": "clean-ish",
                            "signals": [],
                            "assessed_at": "2026-05-19T14:03:45+01:00",
                        },
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_quality_status(target_path)

            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["lyrics"], valid_status)
            self.assertNotIn("chords", state["entries"]["The Campfire Trio - Trail Song"])
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(
                errors[0]["field"],
                "entries['The Campfire Trio - Trail Song'].chords.quality",
            )
            self.assertIn("quality must be one of", errors[0]["reason"])

    def test_load_rejects_nested_content_type_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "lyrics": {
                            "artist": "The Campfire Trio",
                            "title": "Trail Song",
                            "song_key": "The Campfire Trio - Trail Song",
                            "content_type": "chords",
                            "content_hash": "sha256:6666666666666666666666666666666666666666666666666666666666666666",
                            "quality": "clean",
                            "signals": [],
                            "assessed_at": "2026-05-19T14:03:45+01:00",
                        }
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_quality_status(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(
                errors[0]["field"],
                "entries['The Campfire Trio - Trail Song'].lyrics.content_type",
            )
            self.assertIn("must match enclosing entry key", errors[0]["reason"])

    def test_save_creates_parent_directories_automatically(self):
        lyric_status = self._build_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:5555555555555555555555555555555555555555555555555555555555555555",
            "clean",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "nested" / "quality_status.json"

            save_quality_status(target_path, [lyric_status])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())
            self.assertTrue(target_path.parent.parent.exists())

    def _build_review_decision(
        self,
        song_key,
        content_type,
        content,
        decision="accept",
        reason="Manually reviewed and playable.",
        decided_at="2026-05-19T14:03:45+01:00",
    ):
        return build_review_decision(
            song_key=song_key,
            content_type=content_type,
            content_hash=compute_content_hash(content),
            decision=decision,
            reason=reason,
            decided_at=decided_at,
        )

    def _build_content_score(
        self,
        artist,
        title,
        content_type,
        content_hash,
        quality_score,
        quality_band=None,
        score_reasons=None,
        scored_at="2026-05-23T19:00:00+01:00",
    ):
        return build_content_score(
            artist,
            title,
            content_type,
            content_hash,
            quality_score,
            quality_band=quality_band,
            score_reasons=score_reasons or [],
            scored_at=scored_at,
        )

    def test_save_and_load_content_scores_round_trip(self):
        lyric_score = self._build_content_score(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:8888888888888888888888888888888888888888888888888888888888888888",
            82,
            score_reasons=["missing_structure_signal"],
        )
        chord_score = self._build_content_score(
            "The Campfire Trio",
            "Trail Song",
            "chords",
            "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            38,
            score_reasons=["missing_chords"],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "content_scores.json"

            save_content_scores(target_path, [lyric_score, chord_score])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())

            state, errors = load_content_scores(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["lyrics"], lyric_score)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["chords"], chord_score)

    def test_load_missing_content_scores_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "content_scores.json"

            state, errors = load_content_scores(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertIsNone(state["updated_at"])
            self.assertEqual(state["entries"], {})

    def test_load_invalid_content_score_reports_field_path_and_preserves_valid_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "content_scores.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            valid_score = self._build_content_score(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                82,
                score_reasons=["missing_structure_signal"],
            )
            payload = {
                "version": 1,
                "updated_at": "2026-05-23T19:00:00+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "lyrics": valid_score,
                        "chords": {
                            "artist": "The Campfire Trio",
                            "title": "Trail Song",
                            "song_key": "The Campfire Trio - Trail Song",
                            "content_type": "chords",
                            "content_hash": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                            "quality_score": 101,
                            "quality_band": "poor",
                            "score_version": "v1",
                            "score_reasons": [],
                            "scored_at": "2026-05-23T19:00:00+01:00",
                        },
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_content_scores(target_path)

            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["lyrics"], valid_score)
            self.assertNotIn("chords", state["entries"]["The Campfire Trio - Trail Song"])
            self.assertEqual(len(errors), 1)
            self.assertEqual(
                errors[0]["field"],
                "entries['The Campfire Trio - Trail Song'].chords.quality_score",
            )
            self.assertIn("0-100", errors[0]["reason"])

    def test_save_content_scores_creates_parent_directories_automatically(self):
        lyric_score = self._build_content_score(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            82,
            score_reasons=["missing_structure_signal"],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "nested" / "content_scores.json"

            save_content_scores(target_path, [lyric_score])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())
            self.assertTrue(target_path.parent.parent.exists())

    def test_save_and_load_review_decisions_round_trip(self):
        lyric_decision = self._build_review_decision(
            "The Campfire Trio - Trail Song",
            "lyrics",
            "First line\nSecond line",
            decision="accept",
        )
        chord_decision = self._build_review_decision(
            "The Campfire Trio - Trail Song",
            "chords",
            "[G]Trail song",
            decision="override",
            reason="Manually approved for a one-off print.",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_decisions.json"

            save_review_decisions(target_path, [lyric_decision, chord_decision])

            self.assertTrue(target_path.exists())
            self.assertTrue(target_path.parent.exists())

            state, errors = load_review_decisions(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["lyrics"], lyric_decision)
            self.assertEqual(state["entries"]["The Campfire Trio - Trail Song"]["chords"], chord_decision)

    def test_load_missing_review_decisions_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_decisions.json"

            state, errors = load_review_decisions(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertIsNone(state["updated_at"])
            self.assertEqual(state["entries"], {})

    def test_load_malformed_review_decisions_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_decisions.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("{not valid json", encoding="utf-8")

            state, errors = load_review_decisions(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["file_path"], str(target_path))
            self.assertEqual(errors[0]["field"], "$")
            self.assertIn("JSON", errors[0]["reason"])

    def test_load_review_decisions_reports_stale_hash_and_ignores_entry(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_decisions.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            current_hash = compute_content_hash("Current content")
            stale_decision = self._build_review_decision(
                "The Campfire Trio - Trail Song",
                "lyrics",
                "Reviewed content",
                decision="accept",
            )
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "lyrics": stale_decision,
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_review_decisions(
                target_path,
                current_content_hashes={
                    "The Campfire Trio - Trail Song": {
                        "lyrics": current_hash,
                    }
                },
            )

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["field"], "entries['The Campfire Trio - Trail Song'].lyrics.content_hash")
            self.assertIn("stale", errors[0]["reason"])

    def test_load_review_decisions_rejects_nested_content_type_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "review_decisions.json"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": "2026-05-19T14:03:45+01:00",
                "entries": {
                    "The Campfire Trio - Trail Song": {
                        "lyrics": {
                            "song_key": "The Campfire Trio - Trail Song",
                            "content_type": "chords",
                            "content_hash": "sha256:7777777777777777777777777777777777777777777777777777777777777777",
                            "decision": "accept",
                            "reason": "Looks good.",
                            "decided_at": "2026-05-19T14:03:45+01:00",
                        }
                    }
                },
            }
            target_path.write_text(json.dumps(payload), encoding="utf-8")

            state, errors = load_review_decisions(target_path)

            self.assertEqual(state["entries"], {})
            self.assertEqual(len(errors), 1)
            self.assertEqual(
                errors[0]["field"],
                "entries['The Campfire Trio - Trail Song'].lyrics.content_type",
            )
            self.assertIn("must match enclosing entry key", errors[0]["reason"])


if __name__ == "__main__":
    unittest.main()
