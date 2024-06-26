# Campfire Songs Lyrics and Chords

# Create the directory structure
foreach (CampfireSongbookBuilder/data in CampfireSongbookBuilder/app CampfireSongbookBuilder/data) {
    if (-not (Test-Path -Path CampfireSongbookBuilder/data)) {
        New-Item -ItemType Directory -Force -Path CampfireSongbookBuilder/data
    }
}

# Create the files
foreach (CampfireSongbookBuilder/README.md in CampfireSongbookBuilder/app/__init__.py CampfireSongbookBuilder/app/fetch_data.py CampfireSongbookBuilder/app/generate_documents.py CampfireSongbookBuilder/app/cache.py CampfireSongbookBuilder/data/lyrics_cache.json CampfireSongbookBuilder/data/chords_cache.json CampfireSongbookBuilder/main.py CampfireSongbookBuilder/requirements.txt CampfireSongbookBuilder/README.md) {
    if (-not (Test-Path -Path CampfireSongbookBuilder/README.md)) {
        New-Item -ItemType File -Force -Path CampfireSongbookBuilder/README.md
    }
}

# Populate the Python files with boilerplate code
# __init__.py = @"
# __init__.py
