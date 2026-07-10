
# Campfire Songbook Builder

## Overview

Campfire Songbook Builder is a Python-based application designed to generate songbooks with lyrics and chords for campfire sing-alongs. It fetches song lyrics from Genius and chords from Chordie or Ultimate Guitar, processes them, and generates a formatted document.

## Features

- Fetch song lyrics and chords from online sources.
- Cache lyrics and chords to minimize repeated API calls.
- Generate formatted documents with lyrics and chords.
- Command-line interface for various operations.

## Prerequisites

- Python 3.8+
- Access to Genius API (requires a client access token)

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/CampfireSongbookBuilder.git
   cd CampfireSongbookBuilder
   ```

2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

4. Set up the directory structure:
   ```sh
   mkdir -p data/config data/output # On Windows use `@("data/config", "data/output") | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force }`
   ```

5. Copy the example config and fill in your Genius API credentials:
   ```sh
   cp data/config/config.example.json data/config/config.json
   # Then edit data/config/config.json and add your Genius API token
   ```
   Example config:
   ```json
   {
       "genius": {
           "client_access_token": "your_genius_client_access_token"
       }
   }
   ```

6. Place your song list in `data/src/CampfireSongs.csv`. The CSV file should have the following columns: `Artist`, `Title`, and optionally `Skip`, `Favourite`, and `Tags`.
   Use `Favourite` for simple per-song membership in favourite-only workflows. Truthy values such as `yes`, `true`, or `1` are treated as favourite rows.
   Use `Tags` for arbitrary grouping such as `Jessica Protest Karaoke` or `Dicky Karaoke`. Tags are parsed from comma / semicolon / pipe separated values.

## Usage

Run the application from the repo root.

### Core generation

- Generate full books from the current cache using the default quality gate:
  ```sh
  python main.py --generate-from-cache
  ```

- Generate full books from cache and produce PDFs:
  ```sh
  python main.py --generate-from-cache --pdf
  ```

- Generate full books from cache, including `questionable` content and excluding only true `missing` / `unusable` content:
  ```sh
  python main.py --generate-from-cache --pdf --include-questionable
  ```

  This is the mode to use if you want broad output and do not want the quality gate to suppress noisy-but-present songs.

### Layout and margins

- Default PDF/DOCX generation uses mirrored binding margins, so odd and even pages have different inside/outside spacing for printing and stapling:
  ```sh
  python main.py --generate-from-cache --pdf
  ```

- Use equal left/right margins instead:
  ```sh
  python main.py --generate-from-cache --pdf --equal-margins
  ```

- Equal margins also work with broader catalogue generation:
  ```sh
  python main.py --generate-from-cache --pdf --include-questionable --equal-margins
  ```

- Rebuild the quality state from the current cache and write a fresh report:
  ```sh
  python main.py --refresh-quality-state
  ```

### Lyrics-only / chords-only

- Generate lyrics only:
  ```sh
  python main.py --lyrics-only
  ```

- Generate chords only:
  ```sh
  python main.py --chords-only
  ```

- Get song titles and lyric character counts:
  ```sh
  python main.py --get-song-info
  ```

### Filtering by favourites, selections, and tags

- Restrict any run to songs marked as favourites:
  ```sh
  python main.py --favourites-only --generate-from-cache --pdf
  ```

- Restrict any run to a named selection from `data/selections/<name>.json`:
  ```sh
  python main.py --selection trip-night --generate-from-cache --pdf
  ```

- Restrict any run to songs whose tags contain a case-insensitive match:
  ```sh
  python main.py --tags "Jessica Protest Karaoke" --generate-from-cache --pdf
  python main.py --tags "Dicky Karaoke" --generate-from-cache --pdf
  python main.py --tags "Karaoke" --generate-from-cache --pdf
  ```

  Tag matching is substring-based, so `Karaoke` will match both `Jessica Protest Karaoke` and `Dicky Karaoke`.

- Combine tag filtering with `--include-questionable`:
  ```sh
  python main.py --tags "Karaoke" --generate-from-cache --pdf --include-questionable
  ```

- Combine tag filtering with favourites:
  ```sh
  python main.py --favourites-only --tags "Karaoke" --generate-from-cache --pdf
  ```

Generated file names reflect the filter where possible, for example:

- `data/output/Favourites_Lyrics_Document.pdf`
- `data/output/Selection_trip-night_Chords_Document.pdf`
- `data/output/Tag_Karaoke_Lyrics_Document.pdf`
- `data/output/Favourites_Tag_Karaoke_Chords_Document.pdf`

### Manual Lyrics / Chords Import

If you have copied lyrics or chords manually and want to use those local versions instead of network sources, put the pasted text into `data/manual_import.txt` and run:

```sh
python main.py --import-manual data/manual_import.txt
```

This writes two local override files:

- `data/manual_lyrics.json`
- `data/manual_chords.json`

Typical manual-refresh workflow:

```sh
python main.py --import-manual data/manual_import.txt
python main.py --favourites-only --cache-only
python main.py --favourites-only --generate-from-cache --pdf
```

What each step does:

- `--import-manual` parses pasted sections such as `# Artist - Title lyrics`, `# Title chords`, or `# Title by Artist` and writes deterministic local overrides.
- `--cache-only` refreshes the cache from those manual overrides so later generation uses the cleaned local text.
- `--generate-from-cache --pdf` builds the DOCX and PDF outputs from the refreshed cache.

If you want the refreshed manual content to be included even when it is still scored as `questionable`, add `--include-questionable` on the generation step:

```sh
python main.py --import-manual data/manual_import.txt
python main.py --cache-only
python main.py --generate-from-cache --pdf --include-questionable
```

### Duplicate detection

To scan the source catalogue for exact duplicates and fuzzy near-duplicates:

```sh
python main.py --find-duplicate-songs
```

This writes a report to `data/review/reports/song_duplicate_report-YYYYMMDD.md`.

Current output files:

- `data/output/Lyrics_Document.docx`
- `data/output/Lyrics_Document.pdf`
- `data/output/Chords_Document.docx`
- `data/output/Chords_Document.pdf`

## Running Tests & Linting

A minimal test and linter configuration is provided for code quality:

- To run tests (after adding tests to the `tests/` directory):
  ```sh
  python -m unittest discover tests
  ```
- To check code style with flake8:
  ```sh
  flake8 app/ main.py
  ```

## Project Structure

```
CampfireSongbookBuilder/
│
├── app/
│   ├── __init__.py
│   ├── cache.py
│   ├── document_creation.py
│   ├── document_formatting.py
│   ├── document_generation.py
│   ├── fetch_data.py
│   ├── song_info.py
│   └── text_cleaning.py
│
├── data/
│   ├── config/
│   │   ├── config.example.json
│   │   └── config.json
│   ├── src/
│   │   └── CampfireSongs.csv
│   ├── cache/
│   │   ├── lyrics_cache.json
│   │   └── chords_cache.json
│   └── output/
│       ├── Lyrics_Document.docx
│       └── Chords_Document.docx
│
├── main.py
├── README.md
└── requirements.txt
```

## Contributing

Feel free to submit issues and pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
