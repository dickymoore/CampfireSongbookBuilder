import json
import os
import logging
import sys
import shutil
from datetime import datetime

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


def backup_jsonl_file(filename, backups_dir, label):
    source = os.fspath(filename)
    if not os.path.exists(source):
        return None

    target_dir = os.fspath(backups_dir)
    os.makedirs(target_dir, exist_ok=True)

    base_name = os.path.basename(source)
    timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    backup_name = f"{base_name}.{label}-{timestamp}"
    backup_path = os.path.join(target_dir, backup_name)
    shutil.copy2(source, backup_path)
    return backup_path


def jsonl_sync_entries_from_mapping(filename, value_field, mapping):
    updated = 0
    for key, value in mapping.items():
        if not isinstance(key, str) or " - " not in key:
            continue
        if not isinstance(value, str) or not value.strip():
            continue
        artist, title = key.split(" - ", 1)
        jsonl_save_entry(filename, artist.strip(), title.strip(), value, value_field)
        updated += 1
    return updated
