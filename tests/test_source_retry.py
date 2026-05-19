import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from app.content_models import build_quality_status, compute_content_hash, build_quality_signal
from app.review_state import save_quality_status
from app.source_attempts import load_source_attempts


if "bs4" not in sys.modules:
    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:
        pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub

if "docx" not in sys.modules:
    docx_stub = types.ModuleType("docx")
    shared_stub = types.ModuleType("docx.shared")
    oxml_stub = types.ModuleType("docx.oxml")
    oxml_ns_stub = types.ModuleType("docx.oxml.ns")

    class _UnitStub:
        def __init__(self, value):
            self.value = value

    def _qn(value):
        return value

    def _oxml_element(name):
        return {"name": name}

    shared_stub.Pt = _UnitStub
    shared_stub.Inches = _UnitStub
    oxml_ns_stub.qn = _qn
    oxml_stub.OxmlElement = _oxml_element

    sys.modules["docx"] = docx_stub
    sys.modules["docx.shared"] = shared_stub
    sys.modules["docx.oxml"] = oxml_stub
    sys.modules["docx.oxml.ns"] = oxml_ns_stub

from app import document_generation, fetch_data


class TestSourceRetry(unittest.TestCase):
    def test_retry_continues_past_questionable_candidate_until_clean_source(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"
            with patch.object(fetch_data, "SOURCE_ATTEMPTS_PATH", target_path), patch.object(
                fetch_data, "get_lyrics_from_genius", return_value="<div>Verse</div>"
            ), patch.object(
                fetch_data, "get_lyrics_from_lyrics_ovh", return_value="Lyrics not found."
            ), patch.object(
                fetch_data, "get_lyrics_from_azlyrics", return_value="First line\nSecond line"
            ), patch.object(fetch_data, "get_manual_lyrics", return_value=None):
                lyrics, source_name, tried_log, quality_result = fetch_data.get_lyrics_from_sources(
                    "Trail Song", "The Campfire Trio"
                )

            self.assertEqual(lyrics, "First line\nSecond line")
            self.assertEqual(source_name, "AZLyrics")
            self.assertEqual(quality_result["quality"], "clean")
            self.assertEqual(
                tried_log,
                [
                    "Genius (The Campfire Trio – Trail Song)",
                    "Lyrics.ovh (The Campfire Trio – Trail Song)",
                    "AZLyrics (The Campfire Trio – Trail Song)",
                ],
            )

    def test_retry_exhaustion_returns_questionable_final_candidate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "source_attempts.jsonl"
            with patch.object(fetch_data, "SOURCE_ATTEMPTS_PATH", target_path), patch.object(
                fetch_data, "get_chords_from_chordie", return_value="<div>Chord</div>"
            ), patch.object(
                fetch_data, "get_chords_from_ultimate_guitar", return_value="<div>Chord</div>"
            ), patch.object(
                fetch_data, "get_chords_from_echords", return_value="<div>Chord</div>"
            ), patch.object(
                fetch_data, "get_chords_from_songsterr", return_value="<div>Chord</div>"
            ), patch.object(
                fetch_data, "get_chords_from_yousician", return_value="<div>Chord</div>"
            ):
                chords, source_name, tried_log, quality_result = fetch_data.get_chords_from_sources(
                    "Trail Song", "The Campfire Trio"
                )

            self.assertEqual(chords, "<div>Chord</div>")
            self.assertEqual(source_name, "Yousician")
            self.assertEqual(quality_result["quality"], "questionable")
            self.assertGreater(len(quality_result["signals"]), 0)
            self.assertGreater(len(tried_log), 0)

            records, errors = load_source_attempts(target_path)
            self.assertEqual(errors, [])
            self.assertTrue(records)
            self.assertTrue(all(record["status"] == "candidate" for record in records))

    def test_cache_first_skips_live_requests_when_clean_quality_exists(self):
        song_list = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        clean_status = build_quality_status(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            compute_content_hash("First line\nSecond line"),
            "clean",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            quality_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            save_quality_status(quality_path, [clean_status])

            with patch.object(document_generation, "QUALITY_STATUS_PATH", quality_path), patch.object(
                document_generation, "sort_songs", return_value=song_list
            ), patch.object(
                document_generation, "jsonl_load_entry", return_value="First line\nSecond line"
            ), patch.object(
                document_generation, "get_lyrics_from_sources",
                side_effect=AssertionError("live fetch should not run for clean cached content"),
            ), patch.object(
                document_generation, "jsonl_save_entry",
                side_effect=AssertionError("raw cache should not be rewritten for clean cached content"),
            ), patch.object(
                document_generation, "save_quality_status",
                side_effect=AssertionError("quality status should not be rewritten for clean cached content"),
            ):
                document_generation.cache_lyrics(song_list, genius_client=None)

    def test_questionable_final_candidate_is_persisted_through_quality_status(self):
        song_list = [{"Artist": "The Campfire Trio", "Title": "Trail Song"}]
        signals = [
            build_quality_signal(
                "html_residue",
                "warning",
                "HTML residue was detected in the source text.",
                "lyrics",
            )
        ]
        quality_result = {
            "quality": "questionable",
            "signals": signals,
            "summary": {
                "line_count": 1,
                "total_characters": 15,
                "longest_line_length": 15,
                "has_print_hostile_content": False,
                "has_html_residue": True,
            },
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            quality_path = Path(tmp_dir) / "data" / "review" / "quality_status.json"
            persisted_records = []

            def _capture_quality_status(path, records, updated_at=None):
                persisted_records.extend(records)
                return {"version": 1, "updated_at": updated_at, "entries": {}}

            with patch.object(document_generation, "QUALITY_STATUS_PATH", quality_path), patch.object(
                document_generation, "sort_songs", return_value=song_list
            ), patch.object(
                document_generation, "jsonl_load_entry", return_value=None
            ), patch.object(
                document_generation, "get_lyrics_from_sources",
                return_value=("<div>Verse</div>", "AZLyrics", ["AZLyrics (...)"], quality_result),
            ), patch.object(
                document_generation, "jsonl_save_entry"
            ) as save_cache_mock, patch.object(
                document_generation, "load_quality_status",
                return_value=({"version": 1, "updated_at": None, "entries": {}}, []),
            ), patch.object(
                document_generation, "save_quality_status",
                side_effect=_capture_quality_status,
            ):
                document_generation.cache_lyrics(song_list, genius_client=None)

        save_cache_mock.assert_called_once_with(
            "data/cache/lyrics_cache.jsonl",
            "The Campfire Trio",
            "Trail Song",
            "<div>Verse</div>",
            "lyrics",
        )
        self.assertEqual(len(persisted_records), 1)
        self.assertEqual(persisted_records[0]["quality"], "questionable")
        self.assertEqual(persisted_records[0]["content_hash"], compute_content_hash("<div>Verse</div>"))
        self.assertEqual([signal["code"] for signal in persisted_records[0]["signals"]], ["html_residue"])


if __name__ == "__main__":
    unittest.main()
