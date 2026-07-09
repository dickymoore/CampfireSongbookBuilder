import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.docx_stub import install_docx_stub


def _install_bs4_stub():
    if "bs4" in sys.modules:
        return

    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:
        pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub


install_docx_stub()
_install_bs4_stub()

import main  # noqa: E402  pylint: disable=wrong-import-position
import app.document_creation  # noqa: E402  pylint: disable=wrong-import-position


class TestMain(unittest.TestCase):
    def test_resolve_output_paths_uses_favourites_prefix(self):
        args = types.SimpleNamespace(favourites_only=True, selection=None, tags=None)

        lyrics_path, chords_path = main._resolve_output_paths(args)

        self.assertEqual(lyrics_path, "data/output/Favourites_Lyrics_Document.docx")
        self.assertEqual(chords_path, "data/output/Favourites_Chords_Document.docx")

    def test_resolve_output_paths_uses_selection_prefix(self):
        args = types.SimpleNamespace(favourites_only=False, selection="trip-night", tags=None)

        lyrics_path, chords_path = main._resolve_output_paths(args)

        self.assertEqual(lyrics_path, "data/output/Selection_trip-night_Lyrics_Document.docx")
        self.assertEqual(chords_path, "data/output/Selection_trip-night_Chords_Document.docx")

    def test_resolve_output_paths_uses_tag_prefix(self):
        args = types.SimpleNamespace(favourites_only=False, selection=None, tags="Dicky Karaoke")

        lyrics_path, chords_path = main._resolve_output_paths(args)

        self.assertEqual(lyrics_path, "data/output/Tag_Dicky-Karaoke_Lyrics_Document.docx")
        self.assertEqual(chords_path, "data/output/Tag_Dicky-Karaoke_Chords_Document.docx")

    def test_generate_from_cache_favourites_only_filters_song_list_before_generation(self):
        songs = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song", "Favourite": True},
            {"Artist": "The Campfire Trio", "Title": "Night Run", "Favourite": False},
        ]
        report_data = {
            "generated_at": "2026-05-20T12:00:00+01:00",
            "report_type": "quality_run",
            "source": "generate_from_cache",
            "entries": [],
            "selection_issues": [],
            "pdf_outputs": [],
            "pdf_errors": [],
        }

        with patch.object(sys, "argv", ["main.py", "--generate-from-cache", "--favourites-only"]):
            with patch("main.load_config", return_value={"genius": {"client_access_token": "token"}}):
                with patch("main.load_songs", return_value=(songs, [])):
                    with patch("app.cache.jsonl_load_all", return_value={}):
                        with patch(
                            "app.document_creation.create_document_from_cache",
                            return_value=report_data,
                        ) as create_document:
                            with patch("main._write_generation_report") as write_report:
                                main.main()

        create_document.assert_called_once()
        passed_song_list = create_document.call_args.args[0]
        self.assertEqual(
            passed_song_list,
            [{"Artist": "The Campfire Trio", "Title": "Trail Song", "Favourite": True}],
        )
        self.assertEqual(
            create_document.call_args.args[3],
            "data/output/Favourites_Lyrics_Document.docx",
        )
        self.assertEqual(
            create_document.call_args.args[4],
            "data/output/Favourites_Chords_Document.docx",
        )
        write_report.assert_called_once()

    def test_generate_from_cache_tags_filters_song_list_before_generation(self):
        songs = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song", "Tags": ["Jessica Protest Karaoke"]},
            {"Artist": "The Campfire Trio", "Title": "Night Run", "Tags": ["Dicky Karaoke"]},
            {"Artist": "The Campfire Trio", "Title": "River Song", "Tags": ["Campfire"]},
        ]
        report_data = {
            "generated_at": "2026-05-20T12:00:00+01:00",
            "report_type": "quality_run",
            "source": "generate_from_cache",
            "entries": [],
            "selection_issues": [],
            "pdf_outputs": [],
            "pdf_errors": [],
        }

        with patch.object(sys, "argv", ["main.py", "--generate-from-cache", "--tags", "Karaoke"]):
            with patch("main.load_config", return_value={"genius": {"client_access_token": "token"}}):
                with patch("main.load_songs", return_value=(songs, [])):
                    with patch("app.cache.jsonl_load_all", return_value={}):
                        with patch(
                            "app.document_creation.create_document_from_cache",
                            return_value=report_data,
                        ) as create_document:
                            with patch("main._write_generation_report") as write_report:
                                main.main()

        create_document.assert_called_once()
        passed_song_list = create_document.call_args.args[0]
        self.assertEqual(
            passed_song_list,
            [
                {"Artist": "The Campfire Trio", "Title": "Trail Song", "Tags": ["Jessica Protest Karaoke"]},
                {"Artist": "The Campfire Trio", "Title": "Night Run", "Tags": ["Dicky Karaoke"]},
            ],
        )
        self.assertEqual(
            create_document.call_args.args[3],
            "data/output/Tag_Karaoke_Lyrics_Document.docx",
        )
        self.assertEqual(
            create_document.call_args.args[4],
            "data/output/Tag_Karaoke_Chords_Document.docx",
        )
        write_report.assert_called_once()

    def test_generate_from_cache_selection_uses_named_selection_records_and_reports_issues(self):
        songs = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song", "Favourite": True},
            {"Artist": "The Campfire Trio", "Title": "Night Run", "Favourite": False},
        ]
        report_data = {
            "generated_at": "2026-05-20T12:00:00+01:00",
            "report_type": "quality_run",
            "source": "generate_from_selection",
            "entries": [],
            "selection_issues": [],
            "pdf_outputs": [],
            "pdf_errors": [],
        }
        selection_state = {
            "selection_name": "trip-night",
            "entries": [
                {
                    "artist": "The Campfire Trio",
                    "title": "Night Run",
                    "song_key": "The Campfire Trio - Night Run",
                },
                {
                    "artist": "Missing Band",
                    "title": "Lost Song",
                    "song_key": "Missing Band - Lost Song",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            selection_dir = Path(tmp_dir) / "data" / "selections"
            selection_dir.mkdir(parents=True, exist_ok=True)
            (selection_dir / "trip-night.json").write_text("{}", encoding="utf-8")

            with patch.object(main, "SELECTIONS_DIR", selection_dir):
                with patch.object(
                    sys,
                    "argv",
                    ["main.py", "--generate-from-cache", "--selection", "trip-night"],
                ):
                    with patch("main.load_config", return_value={"genius": {"client_access_token": "token"}}):
                        with patch("main.load_songs", return_value=(songs, [])):
                            with patch("main.load_named_selection", return_value=(selection_state, [])):
                                with patch("app.cache.jsonl_load_all", return_value={}):
                                    with patch(
                                        "app.document_creation.create_document_from_cache",
                                        return_value=report_data,
                                    ) as create_document:
                                        with patch("main._write_generation_report") as write_report:
                                            main.main()

        create_document.assert_called_once()
        passed_song_list = create_document.call_args.args[0]
        self.assertEqual(
            passed_song_list,
            [{"Artist": "The Campfire Trio", "Title": "Night Run", "Favourite": False}],
        )
        self.assertEqual(
            create_document.call_args.kwargs["selection_records"],
            [{"Artist": "The Campfire Trio", "Title": "Night Run", "Favourite": False}],
        )
        self.assertEqual(
            create_document.call_args.kwargs["report_source"],
            "generate_from_selection",
        )
        written_report = write_report.call_args.args[0]
        self.assertEqual(written_report["source"], "generate_from_selection")
        self.assertEqual(len(written_report["selection_issues"]), 1)
        self.assertEqual(
            written_report["selection_issues"][0]["song_key"],
            "Missing Band - Lost Song",
        )

    def test_refresh_quality_state_rebuilds_from_cache_before_reporting(self):
        songs = [
            {"Artist": "The Campfire Trio", "Title": "Trail Song", "Favourite": True},
        ]
        report_data = {
            "generated_at": "2026-05-20T12:00:00+01:00",
            "report_type": "quality_run",
            "source": "refresh_quality_state",
            "entries": [],
            "selection_issues": [],
            "pdf_outputs": [],
            "pdf_errors": [],
        }

        with patch.object(sys, "argv", ["main.py", "--refresh-quality-state"]):
            with patch("main.load_config", return_value={"genius": {"client_access_token": "token"}}):
                with patch("main.load_songs", return_value=(songs, [])):
                    with patch("app.cache.jsonl_load_all", side_effect=[{"The Campfire Trio - Trail Song": "Verse 1"}, {}]):
                        with patch(
                            "main.refresh_quality_status_from_cache",
                            return_value={
                                "generated_at": "2026-05-20T12:00:00+01:00",
                                "refreshed_records": [],
                                "refreshed_count": 1,
                                "quality_status_path": "data/review/quality_status.json",
                            },
                        ) as refresh_quality:
                            with patch(
                                "app.document_creation.create_document_from_cache",
                                return_value=report_data,
                            ) as create_document:
                                with patch("main._write_generation_report") as write_report:
                                    main.main()

        refresh_quality.assert_called_once()
        create_document.assert_called_once()
        self.assertEqual(
            create_document.call_args.kwargs["report_source"],
            "refresh_quality_state",
        )
        write_report.assert_called_once()

    def test_load_selection_records_reports_validation_errors(self):
        songs = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        selection_state = {"selection_name": "trip-night", "entries": []}
        selection_errors = [
            {
                "field": "entries[0].artist",
                "reason": "artist must be a non-empty string; got None",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            selection_dir = Path(tmp_dir) / "data" / "selections"
            selection_dir.mkdir(parents=True, exist_ok=True)
            (selection_dir / "trip-night.json").write_text("{}", encoding="utf-8")

            with patch.object(main, "SELECTIONS_DIR", selection_dir):
                with patch("main.load_named_selection", return_value=(selection_state, selection_errors)):
                    selection_name, selection_records, selection_issues = main._load_selection_records(
                        "trip-night",
                        songs,
                    )

        self.assertEqual(selection_name, "trip-night")
        self.assertEqual(selection_records, [])
        self.assertEqual(len(selection_issues), 1)
        self.assertEqual(selection_issues[0]["field"], "entries[0].artist")
        self.assertEqual(selection_issues[0]["selection_name"], "trip-night")

    def test_load_selection_records_raises_for_missing_selection_file(self):
        with self.assertRaises(FileNotFoundError):
            main._load_selection_records("missing-selection", [])

    def test_load_caches_with_manual_overrides_prefers_manual_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lyrics_manual = Path(tmp_dir) / "manual_lyrics.json"
            chords_manual = Path(tmp_dir) / "manual_chords.json"
            lyrics_manual.write_text(
                '{\n  "The Campfire Trio - Trail Song": "manual lyrics\\n"\n}\n',
                encoding="utf-8",
            )
            chords_manual.write_text(
                '{\n  "The Campfire Trio - Trail Song": "manual chords\\n"\n}\n',
                encoding="utf-8",
            )

            with patch.object(main, "MANUAL_LYRICS_PATH", lyrics_manual):
                with patch.object(main, "MANUAL_CHORDS_PATH", chords_manual):
                    with patch(
                        "app.cache.jsonl_load_all",
                        side_effect=[
                            {"The Campfire Trio - Trail Song": "cached lyrics"},
                            {"The Campfire Trio - Trail Song": "cached chords"},
                        ],
                    ):
                        lyrics_cache, chords_cache = main._load_caches_with_manual_overrides()

        self.assertEqual(lyrics_cache["The Campfire Trio - Trail Song"], "manual lyrics\n")
        self.assertEqual(chords_cache["The Campfire Trio - Trail Song"], "manual chords\n")


if __name__ == "__main__":
    unittest.main()
