# CampfireSongbookBuilder - Development Guide

**Date:** 2026-05-17

## Prerequisites

- Python 3.8+.
- Network access for live lyric/chord fetching.
- Genius API token for Genius searches.
- Dependencies from `requirements.txt`.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp data/config/config.example.json data/config/config.json
```

Edit `data/config/config.json` and set `genius.client_access_token`.

## Runtime Inputs

- `data/config/config.json`: local private Genius API config.
- `data/src/CampfireSongs.csv`: song list with `Artist`, `Title`, and optional `Skip`.
- `data/cache/lyrics_cache.jsonl`: lyric cache.
- `data/cache/chords_cache.jsonl`: chord cache.

## Common Commands

```bash
# Run default workflow: cache lyrics/chords and generate both documents
python3 main.py

# Generate documents from existing caches only
python3 main.py --generate-from-cache

# Populate caches without generating documents
python3 main.py --cache-only

# Generate lyrics document only
python3 main.py --lyrics-only

# Generate chords document only
python3 main.py --chords-only

# Print lyric character counts
python3 main.py --get-song-info

# Test Genius API token
python3 main.py --test-api
```

## Testing

Run tests from the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current tests are minimal. High-value additions include:

- Config load failures.
- CSV `Skip` filtering with blank cells.
- JSONL cache update/append behavior.
- Text cleaning of `None`, non-string, and markup inputs.
- Fetch fallback orchestration using mocks.
- CLI branch behavior using mocks/temp files.
- Document-generation output behavior when `python-docx` is installed.

## Linting

The repository has `.flake8` with max line length 100:

```bash
flake8 app/ main.py tests/
```

`flake8` may need to be installed separately in a local environment.

## Development Rules

- Keep imports compatible with `python3 main.py` from the repository root.
- Keep helper modules flat under `app/`.
- Do not move scraper, cache, or document-layout logic into `main.py`.
- Do not make unit tests depend on live external sites or local private config.
- Use temp files/directories for test cache/config/CSV/output data.
- Report missing local dependencies clearly if verification cannot run.

## Generated Outputs

Expected generated documents:

- `data/output/Lyrics_Document.docx`
- `data/output/Chords_Document.docx`

`data/output/*` is ignored by `.gitignore`.

## Version Control Notes

Do not commit:

- `.codex/`
- `data/config/config.json`
- `data/output/*`
- `_bmad/*.user.toml`
- `_bmad/custom/*.user.toml`

The `2026-upgrade` branch currently contains BMAD assets, generated project context, and the merged narrow bug-fix branch. The broader `origin/misc_improvements` branch remains unmerged and should be reviewed separately.

---

_Generated using BMAD Method `document-project` workflow_
