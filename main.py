import logging
import argparse
import sys
import re
import json
from pathlib import Path
from app.load_config import load_config
from app.load_songs import filter_favourite_songs, filter_tagged_songs, load_songs
from app.content_models import derive_song_key
from app.document_generation import cache_lyrics, cache_chords
from app.document_generation import refresh_quality_status_from_cache
from app.fetch_data import get_genius_client
from app.song_info import get_song_lyrics_info
from app.reporting import (
    build_traceable_quality_report,
    summarize_traceable_quality_report,
    write_traceable_quality_report,
)
from app.duplicate_detection import find_song_duplicates, write_duplicate_report
from app.source_attempts import load_source_attempts
from app.selection_state import load_named_selection
from app.manual_import import parse_manual_import, write_manual_json
# from app.cache import load_cache  # Remove this import, not needed with JSONL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_PATH = 'data/config/config.json'
SONGS_CSV_PATH = 'data/src/CampfireSongs.csv'
LYRICS_CACHE_PATH = 'data/cache/lyrics_cache.jsonl'
CHORDS_CACHE_PATH = 'data/cache/chords_cache.jsonl'
LYRICS_DOC_PATH = 'data/output/Lyrics_Document.docx'
CHORDS_DOC_PATH = 'data/output/Chords_Document.docx'
SELECTIONS_DIR = Path('data/selections')
MANUAL_LYRICS_PATH = Path('data/manual_lyrics.json')
MANUAL_CHORDS_PATH = Path('data/manual_chords.json')


def _resolve_output_paths(args):
    prefixes = []
    if getattr(args, "favourites_only", False):
        prefixes.append("Favourites")
    if getattr(args, "selection", None):
        prefixes.append("Selection_{}".format(args.selection))
    if getattr(args, "tags", None):
        tag_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", args.tags).strip("-") or "Tags"
        prefixes.append("Tag_{}".format(tag_slug))

    prefix = "_".join(prefixes) if prefixes else None

    if prefix is None:
        return LYRICS_DOC_PATH, CHORDS_DOC_PATH

    return (
        "data/output/{}_Lyrics_Document.docx".format(prefix),
        "data/output/{}_Chords_Document.docx".format(prefix),
    )


def _write_generation_report(report_data):
    if report_data is None:
        raise ValueError("create_document_from_cache did not return report data.")
    if not isinstance(report_data, dict):
        report_data = dict(report_data)
    source_attempt_records, source_attempt_errors = load_source_attempts()
    if source_attempt_errors:
        logging.warning(
            "Source attempt load reported %d recoverable issue(s).",
            len(source_attempt_errors),
        )

    report = build_traceable_quality_report(
        report_data.get("entries", []),
        source=report_data.get("source", "generate_from_cache"),
        report_type=report_data.get("report_type", "quality_run"),
        source_attempts=source_attempt_records,
        generated_at=report_data.get("generated_at"),
        invalid_song_rows=report_data.get("invalid_song_rows", []),
        selection_issues=report_data.get("selection_issues", []),
        pdf_outputs=report_data.get("pdf_outputs", []),
        pdf_errors=report_data.get("pdf_errors", []),
        document_verification=report_data.get("document_verification", []),
        review_gate_decisions=report_data.get("review_gate_decisions", []),
        content_scores=report_data.get("content_scores", []),
        chords_layout_audit=report_data.get("chords_layout_audit", []),
    )
    report_path = write_traceable_quality_report(report)
    print(summarize_traceable_quality_report(report, report_path))
    return report_path


def _load_manual_override_entries(path):
    target = Path(path)
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str) and value.strip()
    }


def _load_caches_with_manual_overrides(include_lyrics=True, include_chords=True):
    from app.cache import jsonl_load_all

    lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics') if include_lyrics else {}
    chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords') if include_chords else {}

    if include_lyrics:
        lyrics_cache.update(_load_manual_override_entries(MANUAL_LYRICS_PATH))
    if include_chords:
        chords_cache.update(_load_manual_override_entries(MANUAL_CHORDS_PATH))

    return lyrics_cache, chords_cache


def _selection_issue(file_path, field, reason, record=None):
    issue = {
        "selection_name": Path(file_path).stem,
        "issue_type": "selection_validation",
        "file_path": str(file_path),
        "field": field,
        "reason": reason,
    }

    if isinstance(record, dict):
        issue["artist"] = record.get("artist")
        issue["title"] = record.get("title")
        issue["song_key"] = record.get("song_key")

    return issue


def _load_selection_records(selection_name, songs):
    selection_path = SELECTIONS_DIR / "{}.json".format(selection_name)
    if not selection_path.exists():
        raise FileNotFoundError(
            "Selection file not found: {}".format(selection_path)
        )

    selection_state, selection_errors = load_named_selection(selection_path)
    song_index = {
        derive_song_key(song.get("Artist"), song.get("Title")): song
        for song in songs
    }

    selection_records = []
    selection_issues = []
    for error in selection_errors:
        selection_issues.append(
            _selection_issue(
                selection_path,
                error.get("field"),
                error.get("reason"),
            )
        )

    for record in selection_state.get("entries", []):
        song_key = record["song_key"]
        song = song_index.get(song_key)
        if song is None:
            selection_issues.append(
                {
                    "selection_name": selection_state.get("selection_name"),
                    "issue_type": "missing_song",
                    "artist": record.get("artist"),
                    "title": record.get("title"),
                    "song_key": song_key,
                    "reason": "Selection entry does not match any source-list song.",
                    "file_path": str(selection_path),
                }
            )
            continue

        selection_records.append(song)

    return selection_state.get("selection_name"), selection_records, selection_issues

def test_genius_api(genius_client):
    """Test the Genius API key by searching for a well-known song."""
    try:
        song = genius_client.search_song("Imagine", "John Lennon")
        if song:
            print("Genius API key is valid! Example search succeeded: Found song:", song.title)
            return True
        else:
            print("Genius API key appears valid, but test song not found.")
            return False
    except Exception as e:
        print("Genius API key test failed:", e)
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate chord and lyrics documents from a list of songs.")
    parser.add_argument('--get-song-info', action='store_true', help='Get song titles and the character length of the lyrics')
    parser.add_argument('--lyrics-only', action='store_true', help='Generate document for lyrics only')
    parser.add_argument('--chords-only', action='store_true', help='Generate document for chords only')
    parser.add_argument('--generate-from-cache', action='store_true', help='Generate documents from cache only')
    parser.add_argument(
        '--include-questionable',
        action='store_true',
        help='Include questionable content in generated documents; only missing/unusable content stays excluded',
    )
    parser.add_argument(
        '--refresh-quality-state',
        action='store_true',
        help='Rebuild data/review/quality_status.json from the current cache, then write a fresh quality report',
    )
    parser.add_argument('--pdf', action='store_true', help='Also generate PDFs when producing DOCX outputs (requires pandoc or LibreOffice)')
    parser.add_argument('--test-api', action='store_true', help='Test the Genius API key')
    parser.add_argument('--cache-only', action='store_true', help='Fetch and cache all lyrics and chords, but do not generate documents')
    parser.add_argument(
        '--favourites-only',
        action='store_true',
        help='Restrict the run to songs marked as favourites in the source CSV',
    )
    parser.add_argument(
        '--selection',
        help='Restrict the run to a named selection from data/selections/<name>.json',
    )
    parser.add_argument(
        '--tags',
        help='Restrict the run to songs whose tags contain this case-insensitive match; supports partial matches like Karaoke',
    )
    parser.add_argument(
        '--import-manual',
        help='Parse a pasted manual import text file and merge entries into data/manual_lyrics.json and data/manual_chords.json',
    )
    parser.add_argument(
        '--find-duplicate-songs',
        action='store_true',
        help='Analyze the source CSV for exact and fuzzy duplicate song entries and write a report',
    )
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(CONFIG_PATH)
        if not config or 'genius' not in config or 'client_access_token' not in config['genius']:
            raise ValueError("Missing 'genius' or 'client_access_token' in config file.")
        genius_access_token = config['genius']['client_access_token']
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    genius_client = None

    def _lazy_genius_client():
        nonlocal genius_client
        if genius_client is None:
            genius_client = get_genius_client(genius_access_token)
        return genius_client

    if args.test_api:
        test_genius_api(_lazy_genius_client())
        return

    if args.import_manual:
        import_path = Path(args.import_manual)
        if not import_path.exists():
            logging.error("Manual import file not found: %s", import_path)
            sys.exit(1)
        # Allow headers like "# Toxic chords" by inferring the artist from the source list.
        known_songs = {}
        try:
            songs, _ = load_songs(SONGS_CSV_PATH)
            for song in songs:
                artist = song.get("Artist")
                title = song.get("Title")
                if isinstance(artist, str) and isinstance(title, str):
                    key = (title.lower().strip())
                    # manual_import normalizes punctuation + whitespace, so do the same here:
                    import re

                    norm = re.sub(r"\\s+", " ", key)
                    norm = re.sub(r"[^a-z0-9 ]", "", norm).strip()
                    if norm and norm not in known_songs:
                        known_songs[norm] = (artist, title)
        except Exception:
            known_songs = {}

        entries = parse_manual_import(
            import_path.read_text(encoding="utf-8"),
            known_songs=known_songs or None,
        )
        write_manual_json(MANUAL_LYRICS_PATH, entries, "lyrics")
        write_manual_json(MANUAL_CHORDS_PATH, entries, "chords")
        logging.info(
            "Merged %d manual song entr%s into %s and %s.",
            len(entries),
            "y" if len(entries) == 1 else "ies",
            MANUAL_LYRICS_PATH,
            MANUAL_CHORDS_PATH,
        )
        return

    # Load songs
    try:
        songs, invalid_song_rows = load_songs(SONGS_CSV_PATH)
        if invalid_song_rows:
            logging.warning(
                "Source list validation reported %d invalid row(s).",
                len(invalid_song_rows),
            )
    except Exception as e:
        logging.error(f"Failed to load songs: {e}")
        sys.exit(1)

    if args.find_duplicate_songs:
        analysis = find_song_duplicates(songs)
        report_path = write_duplicate_report(analysis)
        print(
            "Duplicate report written to {} (exact groups {}, fuzzy candidates {}).".format(
                report_path,
                len(analysis["exact_duplicate_groups"]),
                analysis["fuzzy_candidate_count"],
            )
        )
        return

    if args.favourites_only:
        songs = filter_favourite_songs(songs)
        logging.info(
            "Filtered source list to %d favourite song(s).",
            len(songs),
        )

    selection_name = None
    selection_records = None
    selection_issues = []
    if args.selection:
        try:
            selection_name, selection_records, selection_issues = _load_selection_records(
                args.selection,
                songs,
            )
        except Exception as e:
            logging.error("Failed to load selection: %s", e)
            sys.exit(1)
        songs = selection_records
        logging.info(
            "Loaded selection '%s' with %d matched song(s) and %d issue(s).",
            selection_name or args.selection,
            len(selection_records),
            len(selection_issues),
        )

    if args.tags:
        songs = filter_tagged_songs(songs, args.tags)
        logging.info(
            "Filtered source list to %d tagged song(s) matching '%s'.",
            len(songs),
            args.tags,
        )

    if args.cache_only:
        logging.info("Caching all lyrics and chords for the song list (no document generation)...")
        cache_lyrics(songs, _lazy_genius_client())
        cache_chords(songs)
        logging.info("Caching complete.")
        return

    if args.get_song_info:
        song_info = get_song_lyrics_info(songs, _lazy_genius_client())
        for title, num_characters in song_info:
            print(f"{title}: {num_characters} characters")
        return

    lyrics_doc_path, chords_doc_path = _resolve_output_paths(args)

    # The following cache loading is not needed with the new JSONL logic
    # lyrics_cache = load_cache(LYRICS_CACHE_PATH)
    # chords_cache = load_cache(CHORDS_CACHE_PATH)

    if args.generate_from_cache:
        logging.info("Generating documents from cache only.")
        lyrics_output = lyrics_doc_path if not args.chords_only else None
        chords_output = chords_doc_path if not args.lyrics_only else None
        lyrics_cache, chords_cache = _load_caches_with_manual_overrides()
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            lyrics_cache,
            chords_cache,
            lyrics_output,
            chords_output,
            selection_records=selection_records,
            report_source="generate_from_selection" if args.selection else "generate_from_cache",
            pdf_output=bool(args.pdf),
            include_questionable=bool(args.include_questionable),
        )
        report_data["source"] = "generate_from_selection" if args.selection else "generate_from_cache"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    if args.refresh_quality_state:
        logging.info("Refreshing quality state from cache only.")
        lyrics_cache, chords_cache = _load_caches_with_manual_overrides()
        refresh_summary = refresh_quality_status_from_cache(
            songs,
            lyrics_cache,
            chords_cache,
        )
        logging.info(
            "Refreshed %d content record(s) into %s.",
            refresh_summary["refreshed_count"],
            refresh_summary["quality_status_path"],
        )
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            lyrics_cache,
            chords_cache,
            selection_records=selection_records,
            report_source="refresh_quality_state",
            pdf_output=False,
            report_all_content=True,
        )
        report_data["source"] = "refresh_quality_state"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    if args.lyrics_only:
        cache_lyrics(songs, _lazy_genius_client())
        lyrics_cache, _ = _load_caches_with_manual_overrides(include_chords=False)
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            lyrics_cache,
            {},
            lyrics_output=lyrics_doc_path,
            selection_records=selection_records,
            report_source="lyrics_only_selection" if args.selection else "lyrics_only",
            include_questionable=bool(args.include_questionable),
        )
        report_data["source"] = "lyrics_only_selection" if args.selection else "lyrics_only"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    if args.chords_only:
        cache_chords(songs)
        _, chords_cache = _load_caches_with_manual_overrides(include_lyrics=False)
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            {},
            chords_cache,
            chords_output=chords_doc_path,
            selection_records=selection_records,
            report_source="chords_only_selection" if args.selection else "chords_only",
            include_questionable=bool(args.include_questionable),
        )
        report_data["source"] = "chords_only_selection" if args.selection else "chords_only"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    # Default: cache both and generate both docs
    cache_lyrics(songs, _lazy_genius_client())
    cache_chords(songs)
    lyrics_cache, chords_cache = _load_caches_with_manual_overrides()
    from app.document_creation import create_document_from_cache
    report_data = create_document_from_cache(
        songs,
        lyrics_cache,
        chords_cache,
        lyrics_output=lyrics_doc_path,
        chords_output=chords_doc_path,
        selection_records=selection_records,
        report_source="full_generation_selection" if args.selection else "full_generation",
        include_questionable=bool(args.include_questionable),
    )
    report_data["source"] = "full_generation_selection" if args.selection else "full_generation"
    report_data["invalid_song_rows"] = invalid_song_rows
    report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
    _write_generation_report(report_data)

if __name__ == "__main__":
    main()
