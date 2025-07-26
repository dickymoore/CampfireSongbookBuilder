# Campfire Songbook Builder

## Overview

Campfire Songbook Builder is a Python‑based application designed to generate songbooks with lyrics and chords for campfire sing‑alongs. It fetches song lyrics from Genius and chords from a variety of online sources (Chordie, Ultimate Guitar, E‑Chords, Songsterr and Yousician), processes them, and generates a formatted document.

## Features

* Fetch song lyrics and chords from online sources using flexible queries.
* Cache lyrics and chords to **JSONL** files (`data/cache/lyrics_cache.jsonl` and `data/cache/chords_cache.jsonl`) to minimise repeated API calls.  The previous JSON format has been deprecated in favour of JSONL for easier incremental updates.
* Generate formatted documents with lyrics and chords in two‑column layout using `python‑docx`.
* Command‑line interface for various operations such as caching, document generation and reporting lyric lengths.
* Comprehensive tests covering configuration loading, caching logic, text cleaning and sorting.
* A GitHub Actions workflow is included to lint the codebase and run the test suite automatically on pushes and pull requests.

## Prerequisites

* Python 3.8+ (tested on Python 3.11)
* Access to the Genius API (requires a client access token)
* Network access to external lyric/chord sites if you intend to build caches automatically.

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/CampfireSongbookBuilder.git
   cd CampfireSongbookBuilder
   ```

2. Create a virtual environment and activate it:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```sh
   pip install -r requirements.txt
   # Optional: install development tools for testing and linting
   pip install pytest flake8
   ```

4. Set up the directory structure.  The repository includes default `data` folders, but you can recreate them if starting from scratch:

   ```sh
   mkdir -p data/config data/src data/cache data/output
   ```

5. Copy the example config and fill in your Genius API credentials.  The application supports loading the token from the config file or the `GENIUS_CLIENT_ACCESS_TOKEN` environment variable:

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

6. Place your song list in `data/src/CampfireSongs.csv`.  The CSV file should have the following columns: `Artist`, `Title`, and optionally `Skip`.  Rows where `Skip` equals `skip` (case insensitive) will be ignored.

## Usage

Run the application from the command line with various options:

* To get song titles and character lengths of the lyrics:

  ```sh
  python main.py --get-song-info
  ```

* To generate a document with lyrics only:

  ```sh
  python main.py --lyrics-only
  ```

* To generate a document with chords only:

  ```sh
  python main.py --chords-only
  ```

* To generate documents from the cache without making any network requests:

  ```sh
  python main.py --generate-from-cache
  ```

* To test your Genius API key:

  ```sh
  python main.py --test-api
  ```

* To fetch and cache all lyrics and chords without generating documents:

  ```sh
  python main.py --cache-only
  ```

## Running Tests & Linting

This repository includes a comprehensive test suite and a linting configuration.  To run the tests and check code style, install the development tools (`pytest` and `flake8`) as shown above and run:

```sh
pytest
flake8 app/ main.py
```

Alternatively, you can run the builtin unittest discovery:

```sh
python -m unittest discover tests
```

## Continuous Integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) is provided.  The workflow installs dependencies, runs flake8 and the test suite automatically on pushes to any branch and on pull requests.  You can modify the workflow to suit your CI requirements.

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
│   ├── text_cleaning.py
│   ├── load_config.py
│   └── load_songs.py
│
├── data/
│   ├── config/
│   │   ├── config.example.json
│   │   └── config.json (user‑specific, not committed)
│   ├── src/
│   │   └── CampfireSongs.csv
│   ├── cache/
│   │   ├── lyrics_cache.jsonl
│   │   └── chords_cache.jsonl
│   └── output/
│       ├── Lyrics_Document.docx
│       └── Chords_Document.docx
│
├── tests/
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_text_cleaning.py
│   ├── test_load_songs.py
│   ├── test_sort_songs.py
│   └── test_song_info.py
│
├── .github/workflows/ci.yml
├── main.py
├── requirements.txt
└── README.md
```

## Contributing

Feel free to submit issues and pull requests.  For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.