import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.docx_stub import install_docx_stub
from app.reporting import (
    build_traceable_quality_report,
    summarize_traceable_quality_report,
    write_traceable_quality_report,
)


def _install_docx_stubs():
    install_docx_stub()


def _install_bs4_stub():
    if "bs4" in sys.modules:
        return

    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:
        pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub


_install_docx_stubs()
_install_bs4_stub()

import main  # noqa: E402  pylint: disable=wrong-import-position


class TestReporting(unittest.TestCase):
    def test_build_traceable_quality_report_includes_trace_data(self):
        generation_results = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "quality": "clean",
                "included": True,
                "decision_source": "quality_clean",
                "reason": "Content passed quality checks.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "clean",
                },
                "review_decision": None,
            },
            {
                "artist": "The Campfire Trio",
                "title": "Missing Song",
                "song_key": "The Campfire Trio - Missing Song",
                "content_type": "lyrics",
                "content_hash": None,
                "quality": "missing",
                "included": False,
                "decision_source": "quality_missing",
                "reason": "Missing content is excluded by default.",
                "signals": [
                    {
                        "code": "missing_lyrics",
                        "severity": "error",
                        "message": "Lyrics are missing or unusable.",
                        "content_type": "lyrics",
                    }
                ],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "missing",
                },
                "review_decision": None,
            },
            {
                "artist": "The Campfire Trio",
                "title": "Override Song",
                "song_key": "The Campfire Trio - Override Song",
                "content_type": "lyrics",
                "content_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "quality": "questionable",
                "included": True,
                "decision_source": "review_override",
                "reason": "Questionable content explicitly allowed by a current review decision.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "questionable",
                },
                "review_decision": {
                    "song_key": "The Campfire Trio - Override Song",
                    "content_type": "lyrics",
                    "content_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                    "decision": "override",
                    "reason": "Approved for this print run.",
                    "decided_at": "2026-05-19T15:14:19+01:00",
                },
                "signals": [
                    {
                        "code": "print_hostile_content",
                        "severity": "warning",
                        "message": "Content is likely too long for comfortable printing.",
                        "content_type": "lyrics",
                    }
                ],
            },
        ]
        invalid_song_rows = [
            {
                "row_number": 7,
                "raw_artist": None,
                "raw_title": "Untitled Song",
                "skip": "skip",
                "reason": "missing artist",
            }
        ]
        source_attempts = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "source": "Genius",
                "status": "candidate",
                "error": None,
                "retrieved_at": "2026-05-19T15:00:00+01:00",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            source_attempts=source_attempts,
            generated_at="2026-05-19T15:14:19+01:00",
            invalid_song_rows=invalid_song_rows,
        )

        self.assertEqual(report["summary"]["included_count"], 2)
        self.assertEqual(report["summary"]["excluded_count"], 0)
        self.assertEqual(report["summary"]["missing_count"], 1)
        self.assertEqual(report["summary"]["questionable_count"], 1)
        self.assertEqual(report["summary"]["overridden_count"], 1)
        self.assertEqual(report["summary"]["clean_count"], 1)
        self.assertEqual(report["summary"]["invalid_input_count"], 1)
        self.assertEqual(report["summary"]["counts"]["clean"], 1)
        self.assertEqual(report["summary"]["counts"]["questionable"], 1)
        self.assertEqual(report["summary"]["counts"]["missing"], 1)
        self.assertEqual(report["summary"]["counts"]["invalid_input"], 1)
        self.assertEqual(
            report["summary"]["clean_songs"][0]["song_key"],
            "The Campfire Trio - Trail Song",
        )
        self.assertEqual(
            report["summary"]["questionable_songs"][0]["top_signal"]["code"],
            "print_hostile_content",
        )
        self.assertEqual(
            report["summary"]["missing_songs"][0]["reason"],
            "Missing content is excluded by default.",
        )
        self.assertEqual(report["summary"]["invalid_input_rows"][0]["row_number"], 7)
        self.assertIsNone(report["summary"]["invalid_input_rows"][0]["raw_artist"])
        self.assertEqual(report["summary"]["invalid_input_rows"][0]["raw_title"], "Untitled Song")
        self.assertEqual(report["songs"][0]["source_attempts"], source_attempts)
        self.assertEqual(report["songs"][1]["source_attempts"], [])
        self.assertEqual(report["songs"][2]["review_decision"]["decision"], "override")

    def test_build_traceable_quality_report_includes_selection_issues(self):
        generation_results = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": None,
                "quality": "missing",
                "included": False,
                "decision_source": "quality_missing",
                "reason": "Missing content is excluded by default.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "missing",
                },
                "review_decision": None,
            }
        ]
        selection_issues = [
            {
                "selection_name": "trip-night",
                "issue_type": "missing_content",
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "reason": "Missing content is excluded by default.",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_selection",
            generated_at="2026-05-19T15:14:19+01:00",
            selection_issues=selection_issues,
        )

        self.assertEqual(report["summary"]["selection_issue_count"], 1)
        self.assertEqual(report["summary"]["counts"]["selection_issue"], 1)
        self.assertEqual(report["summary"]["selection_issues"][0]["selection_name"], "trip-night")
        self.assertEqual(report["selection_issues"], selection_issues)

    def test_build_traceable_quality_report_includes_pdf_artifacts(self):
        generation_results = []
        pdf_outputs = ["/tmp/output/lyrics.pdf"]
        pdf_errors = [
            {
                "source": "/tmp/output/lyrics.docx",
                "target": "/tmp/output/lyrics.pdf",
                "reason": "converter missing",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_selection",
            generated_at="2026-05-19T15:14:19+01:00",
            pdf_outputs=pdf_outputs,
            pdf_errors=pdf_errors,
        )

        self.assertEqual(report["summary"]["pdf_output_count"], 1)
        self.assertEqual(report["summary"]["pdf_error_count"], 1)
        self.assertEqual(report["summary"]["counts"]["pdf_output"], 1)
        self.assertEqual(report["summary"]["counts"]["pdf_error"], 1)
        self.assertEqual(report["pdf_outputs"], pdf_outputs)
        self.assertEqual(report["pdf_errors"], pdf_errors)

    def test_build_traceable_quality_report_preserves_source_attempt_errors(self):
        generation_results = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "quality": "missing",
                "included": False,
                "decision_source": "quality_missing",
                "reason": "Missing content is excluded by default.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "missing",
                },
                "review_decision": None,
            }
        ]
        source_attempts = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "source": "Genius",
                "status": "error",
                "error": "timeout while fetching lyrics",
                "retrieved_at": "2026-05-19T15:00:00+01:00",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            source_attempts=source_attempts,
            generated_at="2026-05-19T15:14:19+01:00",
        )

        self.assertEqual(report["songs"][0]["source_attempts"][0]["status"], "error")
        self.assertEqual(report["songs"][0]["source_attempts"][0]["error"], "timeout while fetching lyrics")

    def test_build_traceable_quality_report_handles_excluded_clean_and_invalid_rows(self):
        generation_results = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "quality": "clean",
                "included": True,
                "decision_source": "quality_clean",
                "reason": "Content passed quality checks.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "clean",
                },
                "review_decision": None,
            },
            {
                "artist": "The Campfire Trio",
                "title": "Long Song",
                "song_key": "The Campfire Trio - Long Song",
                "content_type": "lyrics",
                "content_hash": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
                "quality": "clean",
                "included": False,
                "decision_source": "quality_clean",
                "reason": "Lyrics are too long and were excluded from the document.",
                "signals": [],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "clean",
                },
                "review_decision": None,
            },
        ]
        invalid_song_rows = [
            {
                "row_number": 8,
                "raw_artist": float("nan"),
                "raw_title": float("nan"),
                "reason": "missing artist and missing title",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            generated_at="2026-05-19T15:14:19+01:00",
            invalid_song_rows=invalid_song_rows,
        )

        self.assertEqual(report["summary"]["clean_count"], 2)
        self.assertEqual(report["summary"]["excluded_clean_count"], 1)
        self.assertEqual(report["summary"]["counts"]["clean"], 2)
        self.assertEqual(report["summary"]["counts"]["excluded_clean"], 1)
        self.assertEqual(
            [song["song_key"] for song in report["summary"]["clean_songs"]],
            ["The Campfire Trio - Trail Song", "The Campfire Trio - Long Song"],
        )
        self.assertEqual(
            report["summary"]["excluded_clean_songs"][0]["song_key"],
            "The Campfire Trio - Long Song",
        )
        self.assertIsNone(report["summary"]["invalid_input_rows"][0]["raw_artist"])
        self.assertIsNone(report["summary"]["invalid_input_rows"][0]["raw_title"])
        json.dumps(report, allow_nan=False)

    def test_build_traceable_quality_report_includes_review_gate_decisions(self):
        generation_results = []
        document_verification = [
            {
                "artifact_path": "data/output/Lyrics_Document.md",
                "artifact_type": "markdown",
                "verification_status": "passed",
                "verification_reasons": ["meets_neatness_thresholds"],
                "verified_at": "2026-05-22T17:03:00+01:00",
            }
        ]
        review_gate_decisions = [
            {
                "artifact_path": "data/output/Lyrics_Document.md",
                "artifact_type": "markdown",
                "review_ready": True,
                "failure_reasons": [],
                "computed_at": "2026-05-22T17:04:00+01:00",
            },
            {
                "artifact_path": "data/output/Chords_Document.docx",
                "artifact_type": "docx",
                "review_ready": False,
                "failure_reasons": ["sparse_layout"],
                "computed_at": "2026-05-22T17:04:00+01:00",
            },
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            generated_at="2026-05-22T17:04:00+01:00",
            document_verification=document_verification,
            review_gate_decisions=review_gate_decisions,
        )

        self.assertEqual(report["summary"]["review_ready_count"], 1)
        self.assertEqual(report["summary"]["not_review_ready_count"], 1)
        self.assertEqual(report["summary"]["counts"]["review_ready"], 1)
        self.assertEqual(report["summary"]["counts"]["not_review_ready"], 1)
        self.assertEqual(report["summary"]["manual_review_ready_count"], 1)
        self.assertEqual(report["summary"]["manual_review_blocked_count"], 1)
        self.assertEqual(report["summary"]["counts"]["manual_review_ready"], 1)
        self.assertEqual(report["summary"]["counts"]["manual_review_blocked"], 1)
        self.assertEqual(report["document_verification"], document_verification)
        self.assertEqual(report["review_gate_decisions"], review_gate_decisions)
        self.assertEqual(report["manual_review_gate"]["ready_count"], 1)
        self.assertEqual(report["manual_review_gate"]["blocked_count"], 1)
        self.assertEqual(
            report["manual_review_gate"]["blocked_artifacts"][0]["blocking_stage"],
            "document_verification",
        )
        self.assertEqual(
            report["manual_review_gate"]["blocked_artifacts"][0]["failure_reasons"],
            ["sparse_layout"],
        )

    def test_build_traceable_quality_report_keeps_manual_review_blocks_separate_from_song_quality(self):
        generation_results = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "quality": "questionable",
                "included": False,
                "decision_source": "quality_questionable",
                "reason": "Song content needs review.",
                "signals": [
                    {
                        "code": "low_confidence_match",
                        "severity": "warning",
                        "message": "Source metadata does not match the requested song.",
                        "content_type": "lyrics",
                    }
                ],
                "quality_status": {
                    "content_type": "lyrics",
                    "quality": "questionable",
                },
                "review_decision": None,
            }
        ]
        document_verification = [
            {
                "artifact_path": "data/output/Lyrics_Document.docx",
                "artifact_type": "docx",
                "verification_status": "failed",
                "verification_reasons": ["fragmented_song_blocks"],
                "verified_at": "2026-05-23T18:00:00+01:00",
            }
        ]
        review_gate_decisions = [
            {
                "artifact_path": "data/output/Lyrics_Document.docx",
                "artifact_type": "docx",
                "review_ready": False,
                "failure_reasons": ["fragmented_song_blocks"],
                "computed_at": "2026-05-23T18:01:00+01:00",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            generated_at="2026-05-23T18:01:00+01:00",
            document_verification=document_verification,
            review_gate_decisions=review_gate_decisions,
        )

        self.assertEqual(report["summary"]["questionable_count"], 1)
        self.assertEqual(report["summary"]["manual_review_blocked_count"], 1)
        self.assertEqual(
            report["summary"]["questionable_songs"][0]["song_key"],
            "The Campfire Trio - Trail Song",
        )
        self.assertEqual(
            report["manual_review_gate"]["blocked_artifacts"][0]["verification_reasons"],
            ["fragmented_song_blocks"],
        )
        self.assertTrue(
            report["manual_review_gate"]["blocked_artifacts"][0]["blocked_from_manual_review"]
        )

    def test_write_traceable_quality_report_redacts_sensitive_values(self):
        report = {
            "generated_at": "2026-05-19T15:14:19+01:00",
            "report_type": "quality_run",
            "source": "generate_from_cache",
            "summary": {
                "included_count": 1,
                "excluded_count": 0,
                "missing_count": 0,
                "questionable_count": 0,
                "overridden_count": 0,
            },
            "songs": [
                {
                    "song_key": "The Campfire Trio - Trail Song",
                    "content_type": "lyrics",
                    "review_decision": {
                        "decision": "accept",
                        "client_access_token": "super-secret",
                    },
                    "config": {
                        "api_token": "super-secret",
                        "nested": {"password": "also-secret"},
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = write_traceable_quality_report(report, output_dir=Path(tmp_dir))
            text = Path(report_path).read_text(encoding="utf-8")

        self.assertNotIn("client_access_token", text)
        self.assertNotIn("api_token", text)
        self.assertNotIn("password", text)
        self.assertNotIn("super-secret", text)

    def test_cli_summary_mentions_report_path_without_secrets(self):
        report_data = {
            "generated_at": "2026-05-19T15:14:19+01:00",
            "report_type": "quality_run",
            "source": "generate_from_cache",
            "entries": [
                {
                    "artist": "The Campfire Trio",
                    "title": "Trail Song",
                    "song_key": "The Campfire Trio - Trail Song",
                    "content_type": "lyrics",
                    "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    "quality": "clean",
                    "included": True,
                    "decision_source": "quality_clean",
                    "reason": "Content passed quality checks.",
                    "signals": [],
                    "quality_status": {"quality": "clean"},
                    "review_decision": None,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-report.json"
            with patch.object(
                main,
                "load_config",
                return_value={"genius": {"client_access_token": "secret-token"}},
            ), patch.object(
                main,
                "load_songs",
                return_value=(
                    [{"Artist": "The Campfire Trio", "Title": "Trail Song"}],
                    [
                        {
                            "row_number": 7,
                            "raw_artist": None,
                            "raw_title": "Untitled Song",
                            "reason": "missing artist",
                        }
                    ],
                ),
            ), patch.object(main, "get_genius_client", return_value=object()) as mock_get_genius_client, patch(
                "app.cache.jsonl_load_all",
                side_effect=[{"The Campfire Trio - Trail Song": "First line"}, {}],
            ), patch(
                "app.document_creation.create_document_from_cache",
                return_value=report_data,
            ), patch.object(main, "load_source_attempts", return_value=([], [])), patch.object(
                main,
                "write_traceable_quality_report",
                return_value=report_path,
            ), patch.object(sys, "argv", ["main.py", "--generate-from-cache"]), patch(
                "sys.stdout",
                new_callable=io.StringIO,
            ) as stdout:
                main.main()

        output = stdout.getvalue()
        self.assertIn(str(report_path), output)
        self.assertIn("clean 1", output)
        self.assertIn("invalid input 1", output)
        self.assertNotIn("secret-token", output)
        mock_get_genius_client.assert_not_called()

    def test_cli_summary_mentions_report_path_for_lyrics_only(self):
        report_data = {
            "generated_at": "2026-05-19T15:14:19+01:00",
            "report_type": "quality_run",
            "source": "lyrics_only",
            "entries": [
                {
                    "artist": "The Campfire Trio",
                    "title": "Trail Song",
                    "song_key": "The Campfire Trio - Trail Song",
                    "content_type": "lyrics",
                    "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    "quality": "clean",
                    "included": True,
                    "decision_source": "quality_clean",
                    "reason": "Content passed quality checks.",
                    "signals": [],
                    "quality_status": {"quality": "clean"},
                    "review_decision": None,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "lyrics-only-report.json"
            with patch.object(
                main,
                "load_config",
                return_value={"genius": {"client_access_token": "secret-token"}},
            ), patch.object(
                main,
                "load_songs",
                return_value=([{"Artist": "The Campfire Trio", "Title": "Trail Song"}], []),
            ), patch.object(main, "get_genius_client", return_value=object()), patch.object(
                main, "cache_lyrics", return_value=None
            ), patch(
                "app.cache.jsonl_load_all",
                return_value={"The Campfire Trio - Trail Song": "First line"},
            ), patch(
                "app.document_creation.create_document_from_cache",
                return_value=report_data,
            ), patch.object(main, "load_source_attempts", return_value=([], [])), patch.object(
                main,
                "write_traceable_quality_report",
                return_value=report_path,
            ), patch.object(sys, "argv", ["main.py", "--lyrics-only"]), patch(
                "sys.stdout",
                new_callable=io.StringIO,
            ) as stdout:
                main.main()

        output = stdout.getvalue()
        self.assertIn(str(report_path), output)
        self.assertIn("clean 1", output)
        self.assertNotIn("secret-token", output)


if __name__ == "__main__":
    unittest.main()
