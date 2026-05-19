# CampfireSongbookBuilder - Module Inventory

**Date:** 2026-05-17

This project has no UI component system. This inventory documents the Python modules that act as the project components.

## Application Modules

| Module | Main Functions | Responsibility | Key Dependencies |
| --- | --- | --- | --- |
| `main.py` | `main`, `test_genius_api` | CLI argument parsing and workflow orchestration | `argparse`, `logging`, `app.*` helpers |
| `app/cache.py` | `jsonl_load_entry`, `jsonl_save_entry`, `jsonl_load_all` | JSONL cache persistence | `json`, `os`, `logging` |
| `app/document_creation.py` | `create_document_from_cache` | Generate Word documents from loaded caches | `python-docx`, `app.document_formatting`, `app.text_cleaning` |
| `app/document_formatting.py` | `set_document_margins`, `set_paragraph_font`, `create_two_column_section`, `add_header_footer`, `sort_songs` | Word formatting and song sorting | `python-docx`, `re` |
| `app/document_generation.py` | `cache_lyrics`, `cache_chords` | Populate lyric/chord caches for a song list | `app.fetch_data`, `app.cache`, `app.text_cleaning` |
| `app/fetch_data.py` | `get_lyrics_from_sources`, `get_chords_from_sources`, source-specific helpers | External lyric/chord lookup and fallback orchestration | `requests`, `BeautifulSoup`, `lyricsgenius`, `app.cache` |
| `app/load_config.py` | `load_config` | Load Genius API config JSON | `json`, `logging` |
| `app/load_songs.py` | `load_songs` | Load song CSV and apply `Skip` filtering | `pandas`, `logging` |
| `app/song_info.py` | `get_song_lyrics_info` | Report lyric character counts | `app.fetch_data`, `app.cache`, `app.text_cleaning` |
| `app/text_cleaning.py` | `clean_lyrics`, `clean_chords`, helper cleaners | Remove lyric/chord noise and markup | `re` |

## Maintenance Scripts

| Script | Purpose |
| --- | --- |
| `migrate_cache_to_jsonl.py` | Convert older cache formats to JSONL |
| `clean_chords_cache.py` | Maintenance cleanup for chords cache |
| `clean_chords_cache_brackets.py` | Maintenance cleanup for bracket/markup patterns |
| `fix_mojibake_in_cache.py` | Repair mojibake in cache data |

## Critical Contracts

- `main.py` is the supported entrypoint and should stay thin.
- Cache helpers preserve one-record-per-line JSONL semantics.
- Fetch helpers preserve fallback order and sentinel values.
- Document helpers own `python-docx` behavior.
- Text cleaning tolerates `None` and non-string inputs.

## Extension Points

- Add new lyric sources as source-specific helpers in `app/fetch_data.py`, then compose them via `get_lyrics_from_sources`.
- Add new chord sources as source-specific helpers in `app/fetch_data.py`, then compose them via `get_chords_from_sources`.
- Add new document formatting behavior in `app/document_formatting.py`, not `main.py`.
- Add tests under `tests/test_*.py` using `unittest`.

---

_Generated using BMAD Method `document-project` workflow_
