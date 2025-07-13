
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

6. Place your song list in `data/src/CampfireSongs.csv`. The CSV file should have the following columns: `Artist`, `Title`, and optionally `Skip`.

## Usage

Run the application from the command line with various options:

- To get song titles and character lengths of the lyrics:
  ```sh
  python main.py --get-song-info
  ```

- To generate a document with lyrics only:
  ```sh
  python main.py --lyrics-only
  ```

- To generate a document with chords only:
  ```sh
  python main.py --chords-only
  ```

- To generate documents from the cache:
  ```sh
  python main.py --generate-from-cache
  ```

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
