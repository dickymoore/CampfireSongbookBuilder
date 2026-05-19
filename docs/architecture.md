# CampfireSongbookBuilder - Architecture

**Date:** 2026-05-17
**Scope:** Single-part Python CLI application

## Executive Summary

CampfireSongbookBuilder is a thin command-line orchestrator around a set of flat Python helper modules. The core workflow is:

1. Load config and song list.
2. Fetch lyrics/chords or read JSONL caches.
3. Clean text and skip missing/oversized content.
4. Generate Word documents.

The most important architectural constraint is preserving repo-root execution: the supported invocation is `python3 main.py ...`, and modules use absolute `app.*` imports.

## Architecture Pattern

**Pattern:** Single-process CLI with functional helper modules.

`main.py` coordinates workflows and delegates to `app/` modules. There is no web server, database, persistent service, queue, or UI framework.

## Runtime Flow

```text
main.py
  -> load_config(config.json)
  -> load_songs(CampfireSongs.csv)
  -> selected CLI mode
     -> cache_lyrics/cache_chords
        -> get_*_from_sources
           -> cache lookup
           -> source-specific HTTP/scraper fallback
           -> JSONL cache write
     -> jsonl_load_all
     -> create_document_from_cache
        -> clean_lyrics/clean_chords
        -> python-docx formatting
        -> data/output/*.docx
```

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `main.py` | CLI argument parsing, config/song loading, workflow selection, top-level exit handling |
| `app/load_config.py` | JSON config loading and user-friendly load errors |
| `app/load_songs.py` | CSV loading and `Skip` filtering |
| `app/cache.py` | JSONL cache read/write helpers |
| `app/fetch_data.py` | Genius client setup, source-specific lyric/chord fetching, scraper fallback ordering |
| `app/document_generation.py` | Cache population workflows for lyrics and chords |
| `app/document_creation.py` | Build lyrics/chords Word documents from cache dictionaries |
| `app/document_formatting.py` | `python-docx` margins, headers/footers, columns, font sizing, sorting |
| `app/text_cleaning.py` | Lyrics/chords cleanup and markup removal |
| `app/song_info.py` | Lyrics length reporting |

## Data Architecture

The application has file-based runtime state, not a database.

| Path | Purpose | Version Control |
| --- | --- | --- |
| `data/config/config.example.json` | Template Genius API config | Tracked |
| `data/config/config.json` | Local private config | Ignored |
| `data/src/CampfireSongs.csv` | Song input list | Tracked in current repo |
| `data/cache/lyrics_cache.jsonl` | Lyrics cache | Tracked in current repo |
| `data/cache/chords_cache.jsonl` | Chords cache | Tracked in current repo |
| `data/output/*.docx` | Generated documents | Ignored |

Cache records are one JSON object per line, using fields such as `artist`, `title`, and either `lyrics` or `chords`. Many readers also use `"Artist - Title"` mapping keys derived from the exact artist/title values.

## External Integrations

| Source | Type | Usage |
| --- | --- | --- |
| Genius | API/client | Primary lyrics source via `lyricsgenius` |
| Lyrics.ovh | HTTP JSON API | Lyrics fallback |
| AZLyrics | HTML scraping | Lyrics fallback |
| Manual JSON | Local file | Lyrics fallback via `data/manual_lyrics.json` if present |
| Chordie | HTML scraping | Chords source |
| Ultimate Guitar | HTML/embedded JSON scraping | Chords fallback |
| E-Chords | HTML scraping | Chords source |
| Songsterr | HTML scraping | Chords source |
| Yousician | HTML scraping | Chords source |

Network/source failures are intended to be recoverable in scraper flows. Source helpers generally return sentinel values such as `"Lyrics not found."` or `"Chords not found."` and allow later sources to be attempted.

## CLI Modes

| Mode | Behavior |
| --- | --- |
| default | Cache lyrics/chords, load caches, generate both documents |
| `--cache-only` | Populate caches only |
| `--generate-from-cache` | Generate documents without fetching |
| `--lyrics-only` | Fetch/cache lyrics and generate lyrics document |
| `--chords-only` | Fetch/cache chords and generate chords document |
| `--get-song-info` | Print lyric character counts |
| `--test-api` | Test Genius API token with a known search |

## Error Handling

- `main.py` catches config and song-load failures and exits with code 1.
- Config loading raises clearer `FileNotFoundError` and `ValueError` errors after the merged bug-fix branch.
- CSV loading tolerates blank `Skip` cells.
- Text cleaning tolerates `None` and non-string inputs by returning `''`.
- Fetch/scraper helpers usually log failures and continue fallback behavior.

## Testing Strategy

Current tests use `unittest`. The key command is:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

High-value future coverage areas are config errors, CSV skip filtering, JSONL cache behavior, text cleaning, source fallback orchestration, CLI mode branching, and document-generation output behavior.

## Known Constraints and Risks

- Imports assume repo-root execution with `app.*` imports.
- Some runtime paths are constants in `main.py`, while cache paths are also hardcoded in helper modules.
- Network scraping depends on external site HTML and may be brittle.
- `python-docx` may be missing in some local environments, blocking document-generation verification.
- The unmerged `origin/misc_improvements` branch contains broader refactor/test/CI changes and should be reviewed before merging.

---

_Generated using BMAD Method `document-project` workflow_
