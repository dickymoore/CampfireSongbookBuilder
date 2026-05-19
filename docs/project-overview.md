# CampfireSongbookBuilder - Project Overview

**Date:** 2026-05-17
**Type:** CLI application
**Architecture:** Single-process Python CLI with helper modules

## Executive Summary

CampfireSongbookBuilder is a Python command-line tool for building campfire songbooks. It loads a CSV song list, fetches or reuses cached lyrics and chords, cleans source text, and generates Word documents for lyrics and chords.

The project is a small monolith: `main.py` coordinates command-line workflows and delegates work to flat helper modules under `app/`. Runtime state lives under `data/`, including local config, source CSV input, JSONL caches, and generated `.docx` outputs.

## Project Classification

- **Repository Type:** Monolith
- **Project Type:** CLI
- **Primary Language:** Python
- **Architecture Pattern:** Thin CLI orchestration with cache-first fetch helpers and document-generation helpers

## Technology Stack Summary

| Category | Technology | Version / Source | Purpose |
| --- | --- | --- | --- |
| Language | Python | README: 3.8+; local verification: 3.12.3 | CLI runtime |
| CLI | `argparse` | standard library | Command-line options |
| Config | `json` | standard library | `data/config/config.json` loading |
| CSV | `pandas` | 2.2.2 | Song list loading and skip filtering |
| HTTP | `requests` | 2.32.3 | Lyric/chord source fetching |
| HTML parsing | `beautifulsoup4` / `lxml` | 4.12.3 / 5.2.2 | Scraper parsing |
| Lyrics API | `lyricsgenius` | 3.0.1 | Genius API client |
| Documents | `python-docx` | 1.1.2 | `.docx` generation |
| Tests | `unittest` | standard library | Current test runner |
| Lint config | `flake8` | `.flake8` | Max line length 100 |

## Key Features

- Load songs from `data/src/CampfireSongs.csv`.
- Skip rows where optional `Skip` column is set to `skip`.
- Fetch lyrics from Genius, Lyrics.ovh, AZLyrics, and manual JSON fallback.
- Fetch chords from Chordie, Ultimate Guitar, E-Chords, Songsterr, and Yousician.
- Cache lyrics and chords in JSONL files under `data/cache/`.
- Generate lyrics and chords Word documents under `data/output/`.
- Support cache-only, cache-to-document, lyrics-only, chords-only, API-test, and song-info CLI modes.

## Architecture Highlights

- `main.py` owns argument parsing, config loading, workflow selection, and top-level exit behavior.
- `app/fetch_data.py` owns source-specific HTTP and scraper logic.
- `app/cache.py` owns JSONL cache reads/writes.
- `app/document_generation.py` owns cache population workflows.
- `app/document_creation.py` and `app/document_formatting.py` own Word document creation and formatting.
- `app/text_cleaning.py` owns lyric/chord cleanup.

## Development Overview

### Prerequisites

- Python 3.8+
- Dependencies from `requirements.txt`
- Genius API token in local `data/config/config.json`
- Song list at `data/src/CampfireSongs.csv`

### Getting Started

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp data/config/config.example.json data/config/config.json
python3 main.py --generate-from-cache
```

### Key Commands

- **Install:** `pip install -r requirements.txt`
- **Run default workflow:** `python3 main.py`
- **Generate from cache:** `python3 main.py --generate-from-cache`
- **Cache only:** `python3 main.py --cache-only`
- **Run tests:** `python3 -m unittest discover -s tests -p 'test_*.py'`

## Repository Structure

The repository is organized around a small CLI application:

- `main.py`: CLI entrypoint and workflow coordinator.
- `app/`: application helper modules.
- `data/config/`: local configuration template and ignored runtime config.
- `data/src/`: CSV song input.
- `data/cache/`: JSONL lyric/chord caches.
- `data/output/`: generated Word documents, ignored by `.gitignore`.
- `tests/`: `unittest` tests.
- `_bmad-output/`: BMAD-generated planning/context artifacts.
- `docs/`: generated project documentation.

## Documentation Map

- [index.md](./index.md) - Master documentation index
- [architecture.md](./architecture.md) - Technical architecture
- [source-tree-analysis.md](./source-tree-analysis.md) - Directory structure
- [development-guide.md](./development-guide.md) - Development workflow
- [component-inventory.md](./component-inventory.md) - Module inventory

---

_Generated using BMAD Method `document-project` workflow_
