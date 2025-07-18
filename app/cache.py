import json
import os
import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)

# JSONL cache helpers
def jsonl_load_entry(filename, artist, title, value_field):
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('artist') == artist and entry.get('title') == title:
                        return entry.get(value_field)
                except Exception:
                    continue
        return None
    except Exception as e:
        logger.error(f"Error loading JSONL cache: {e}")
        print(f"\nERROR: Failed to load cache file '{filename}'.\nReason: {e}\n")
        input("Press Enter to exit...")
        sys.exit(1)

# Add or update an entry in JSONL file
def jsonl_save_entry(filename, artist, title, value, value_field):
    entries = []
    found = False
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('artist') == artist and entry.get('title') == title:
                        entry[value_field] = value
                        found = True
                    entries.append(entry)
                except Exception:
                    continue
    if not found:
        entries.append({'artist': artist, 'title': title, value_field: value})
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

# For compatibility: load all entries as a dict (for summary/reporting)
def jsonl_load_all(filename, value_field):
    result = {}
    if not os.path.exists(filename):
        return result
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                key = f"{entry.get('artist', '')} - {entry.get('title', '')}"
                result[key] = entry.get(value_field)
            except Exception:
                continue
    return result
