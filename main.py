import logging
import argparse
import sys
from pathlib import Path
from app.load_config import load_config
from app.load_songs import filter_favourite_songs, load_songs
from app.content_models import derive_song_key
from app.document_generation import cache_lyrics, cache_chords
from app.fetch_data import get_genius_client
from app.song_info import get_song_lyrics_info
from app.reporting import (
    build_traceable_quality_report,
    summarize_traceable_quality_report,
    write_traceable_quality_report,
)
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
    )
    report_path = write_traceable_quality_report(report)
    print(summarize_traceable_quality_report(report, report_path))
    return report_path


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
        '--import-manual',
        help='Parse a pasted manual import text file and write data/manual_lyrics.json and data/manual_chords.json',
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
        entries = parse_manual_import(import_path.read_text(encoding="utf-8"))
        write_manual_json(MANUAL_LYRICS_PATH, entries, "lyrics")
        write_manual_json(MANUAL_CHORDS_PATH, entries, "chords")
        logging.info(
            "Wrote %d manual song entr%s to %s and %s.",
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

    # The following cache loading is not needed with the new JSONL logic
    # lyrics_cache = load_cache(LYRICS_CACHE_PATH)
    # chords_cache = load_cache(CHORDS_CACHE_PATH)

    if args.generate_from_cache:
        logging.info("Generating documents from cache only.")
        lyrics_output = LYRICS_DOC_PATH if not args.chords_only else None
        chords_output = CHORDS_DOC_PATH if not args.lyrics_only else None
        # The document generation functions will now load from JSONL as needed
        from app.cache import jsonl_load_all
        lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
        chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            lyrics_cache,
            chords_cache,
            lyrics_output,
            chords_output,
            selection_records=selection_records,
            report_source="generate_from_selection" if args.selection else "generate_from_cache",
        )
        report_data["source"] = "generate_from_selection" if args.selection else "generate_from_cache"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    if args.lyrics_only:
        cache_lyrics(songs, _lazy_genius_client())
        from app.cache import jsonl_load_all
        lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            lyrics_cache,
            {},
            lyrics_output=LYRICS_DOC_PATH,
            selection_records=selection_records,
            report_source="lyrics_only_selection" if args.selection else "lyrics_only",
        )
        report_data["source"] = "lyrics_only_selection" if args.selection else "lyrics_only"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    if args.chords_only:
        cache_chords(songs)
        from app.cache import jsonl_load_all
        chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
        from app.document_creation import create_document_from_cache
        report_data = create_document_from_cache(
            songs,
            {},
            chords_cache,
            chords_output=CHORDS_DOC_PATH,
            selection_records=selection_records,
            report_source="chords_only_selection" if args.selection else "chords_only",
        )
        report_data["source"] = "chords_only_selection" if args.selection else "chords_only"
        report_data["invalid_song_rows"] = invalid_song_rows
        report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
        _write_generation_report(report_data)
        return

    # Default: cache both and generate both docs
    cache_lyrics(songs, _lazy_genius_client())
    cache_chords(songs)
    from app.cache import jsonl_load_all
    lyrics_cache = jsonl_load_all(LYRICS_CACHE_PATH, 'lyrics')
    chords_cache = jsonl_load_all(CHORDS_CACHE_PATH, 'chords')
    from app.document_creation import create_document_from_cache
    report_data = create_document_from_cache(
        songs,
        lyrics_cache,
        chords_cache,
        lyrics_output=LYRICS_DOC_PATH,
        chords_output=CHORDS_DOC_PATH,
        selection_records=selection_records,
        report_source="full_generation_selection" if args.selection else "full_generation",
    )
    report_data["source"] = "full_generation_selection" if args.selection else "full_generation"
    report_data["invalid_song_rows"] = invalid_song_rows
    report_data["selection_issues"] = selection_issues + report_data.get("selection_issues", [])
    _write_generation_report(report_data)

if __name__ == "__main__":
    main()
