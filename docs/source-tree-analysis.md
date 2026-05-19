# CampfireSongbookBuilder - Source Tree Analysis

**Date:** 2026-05-17

## Overview

This repository is a small Python CLI monolith. The source tree separates application helpers (`app/`), runtime data (`data/`), tests (`tests/`), generated BMAD artifacts (`_bmad-output/`), and generated project documentation (`docs/`).

## Complete Directory Structure

```text
CampfireSongbookBuilder/
├── .flake8                         # flake8 config, max line length 100
├── .gitignore                      # Python/gitignored runtime outputs and local state
├── LICENSE
├── README.md                       # Existing human overview
├── main.py                         # CLI entrypoint
├── requirements.txt                # Pinned runtime dependencies
├── app/
│   ├── __init__.py
│   ├── cache.py                    # JSONL cache helpers
│   ├── document_creation.py        # Word document creation from caches
│   ├── document_formatting.py      # python-docx formatting helpers
│   ├── document_generation.py      # Cache population workflows
│   ├── fetch_data.py               # External source fetching and scraping
│   ├── load_config.py              # JSON config loading
│   ├── load_songs.py               # CSV song loading and skip filtering
│   ├── song_info.py                # Lyric length reporting
│   └── text_cleaning.py            # Lyrics/chords cleanup
├── data/
│   ├── cache/
│   │   ├── chords_cache.jsonl      # Chord cache, JSONL
│   │   └── lyrics_cache.jsonl      # Lyrics cache, JSONL
│   ├── config/
│   │   └── config.example.json     # Template Genius config
│   └── src/
│       └── CampfireSongs.csv       # Song input list
├── docs/                           # Generated brownfield docs
├── tests/
│   └── test_config.py              # unittest coverage
├── _bmad-output/
│   └── project-context.md          # AI implementation rules
├── clean_chords_cache.py           # Maintenance script
├── clean_chords_cache_brackets.py  # Maintenance script
├── fix_mojibake_in_cache.py        # Maintenance script
└── migrate_cache_to_jsonl.py       # Maintenance script
```

## Critical Directories

### `app/`

Application logic lives here as flat helper modules. Preserve absolute imports like `from app.cache import ...` unless the CLI entrypoint and tests are migrated together.

**Purpose:** Python application helpers
**Contains:** cache, fetch, document, config, CSV, text-cleaning, and reporting logic
**Entry Points:** Called by `main.py`

### `data/`

Runtime inputs and outputs live here. `data/config/config.json` and `data/output/*` are ignored; caches and source CSV are tracked in the current repo.

**Purpose:** Runtime data and generated output
**Contains:** config template, song CSV, JSONL caches, ignored generated documents

### `tests/`

Current test suite uses Python `unittest`.

**Purpose:** Regression tests
**Contains:** `test_*.py` files
**Entry Points:** `python3 -m unittest discover -s tests -p 'test_*.py'`

### `_bmad-output/`

BMAD-generated planning/context artifacts.

**Purpose:** AI planning and project context
**Contains:** `project-context.md`, planning/implementation artifact folders

### `docs/`

Generated brownfield documentation for humans and AI agents.

**Purpose:** Project documentation
**Contains:** index, overview, architecture, source tree, development guide, module inventory, scan state

## Entry Points

- **Main Entry:** `main.py`
- **Test Entry:** `python3 -m unittest discover -s tests -p 'test_*.py'`
- **Generated Document Entry:** `docs/index.md`
- **AI Context Entry:** `_bmad-output/project-context.md`

## File Organization Patterns

- Flat helper modules under `app/`.
- Small maintenance scripts at repo root.
- File-based runtime state under `data/`.
- Generated BMAD planning artifacts under `_bmad-output/`.
- Generated brownfield docs under `docs/`.

## Key File Types

### Python source

- **Pattern:** `*.py`
- **Purpose:** CLI, helpers, tests, maintenance scripts
- **Examples:** `main.py`, `app/fetch_data.py`, `tests/test_config.py`

### JSONL cache

- **Pattern:** `data/cache/*.jsonl`
- **Purpose:** One JSON object per line for cached lyrics/chords
- **Examples:** `data/cache/lyrics_cache.jsonl`

### CSV input

- **Pattern:** `data/src/*.csv`
- **Purpose:** Song list input
- **Examples:** `data/src/CampfireSongs.csv`

### Word output

- **Pattern:** `data/output/*.docx`
- **Purpose:** Generated songbooks
- **Examples:** `Lyrics_Document.docx`, `Chords_Document.docx`

## Configuration Files

- `.flake8`: flake8 max line length and exclusions.
- `.gitignore`: ignores generated output, local config, Codex state, and user config.
- `requirements.txt`: pinned runtime dependencies.
- `data/config/config.example.json`: example Genius API token shape.
- `_bmad-output/project-context.md`: AI implementation rules and durable project context.

## Notes for Development

- Run commands from the repository root.
- Do not introduce path assumptions based on arbitrary current working directories.
- Avoid committing local/private state, including `.codex/`, `data/config/config.json`, generated docs output, and `*.user.toml`.
- Keep helper boundaries intact unless a deliberate refactor updates tests and docs.

---

_Generated using BMAD Method `document-project` workflow_
