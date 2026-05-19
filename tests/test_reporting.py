import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from app.reporting import (
    build_traceable_quality_report,
    summarize_traceable_quality_report,
    write_traceable_quality_report,
)


def _install_docx_stubs():
    if "docx" in sys.modules:
        return

    docx_stub = types.ModuleType("docx")
    docx_stub.Document = lambda *args, **kwargs: None

    shared_stub = types.ModuleType("docx.shared")
    shared_stub.Pt = lambda value: value
    shared_stub.Inches = lambda value: value

    oxml_stub = types.ModuleType("docx.oxml")
    oxml_stub.OxmlElement = lambda *args, **kwargs: None

    ns_stub = types.ModuleType("docx.oxml.ns")
    ns_stub.qn = lambda value: value

    sys.modules["docx"] = docx_stub
    sys.modules["docx.shared"] = shared_stub
    sys.modules["docx.oxml"] = oxml_stub
    sys.modules["docx.oxml.ns"] = ns_stub


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
            },
        ]
        source_attempts = [
            {
                "artist": "The Campfire Trio",
                "title": "Trail Song",
                "song_key": "The Campfire Trio - Trail Song",
                "content_type": "lyrics",
                "source": "Genius",
                "status": "candidate",
                "retrieved_at": "2026-05-19T15:00:00+01:00",
            }
        ]

        report = build_traceable_quality_report(
            generation_results,
            source="generate_from_cache",
            source_attempts=source_attempts,
            generated_at="2026-05-19T15:14:19+01:00",
        )

        self.assertEqual(report["summary"]["included_count"], 2)
        self.assertEqual(report["summary"]["excluded_count"], 0)
        self.assertEqual(report["summary"]["missing_count"], 1)
        self.assertEqual(report["summary"]["questionable_count"], 1)
        self.assertEqual(report["summary"]["overridden_count"], 1)
        self.assertEqual(report["songs"][0]["source_attempts"], source_attempts)
        self.assertEqual(report["songs"][1]["source_attempts"], [])
        self.assertEqual(report["songs"][2]["review_decision"]["decision"], "override")

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
            with patch.object(main, "load_config", return_value={"genius": {"client_access_token": "secret-token"}}), patch.object(
                main, "load_songs", return_value=([{"Artist": "The Campfire Trio", "Title": "Trail Song"}], [])
            ), patch.object(main, "get_genius_client", return_value=object()), patch(
                "app.cache.jsonl_load_all", side_effect=[{"The Campfire Trio - Trail Song": "First line"}, {}]
            ), patch("app.document_creation.create_document_from_cache", return_value=report_data), patch.object(
                main, "load_source_attempts", return_value=([], [])
            ), patch.object(main, "write_traceable_quality_report", return_value=report_path), patch.object(
                sys, "argv", ["main.py", "--generate-from-cache"]
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
                main.main()

        output = stdout.getvalue()
        self.assertIn(str(report_path), output)
        self.assertIn("included 1", output)
        self.assertNotIn("secret-token", output)

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
            with patch.object(main, "load_config", return_value={"genius": {"client_access_token": "secret-token"}}), patch.object(
                main, "load_songs", return_value=([{"Artist": "The Campfire Trio", "Title": "Trail Song"}], [])
            ), patch.object(main, "get_genius_client", return_value=object()), patch.object(
                main, "cache_lyrics", return_value=None
            ), patch(
                "app.cache.jsonl_load_all", return_value={"The Campfire Trio - Trail Song": "First line"}
            ), patch("app.document_creation.create_document_from_cache", return_value=report_data), patch.object(
                main, "load_source_attempts", return_value=([], [])
            ), patch.object(main, "write_traceable_quality_report", return_value=report_path), patch.object(
                sys, "argv", ["main.py", "--lyrics-only"]
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
                main.main()

        output = stdout.getvalue()
        self.assertIn(str(report_path), output)
        self.assertIn("included 1", output)
        self.assertNotIn("secret-token", output)


if __name__ == "__main__":
    unittest.main()
