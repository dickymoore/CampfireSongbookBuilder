"""Helper functions for working with JSONL cache files.

The application caches lyrics and chords on disk using the JSONL format.  Each
line of the cache file is a JSON object with at least three keys: ``artist``,
``title`` and either ``lyrics`` or ``chords`` depending on the cache.  These
helpers provide convenient functions to load, save and list entries.
"""

import json
import os
import logging
from typing import Any, Dict, Optional

# Configure module level logger
logger = logging.getLogger(__name__)

def jsonl_load_entry(filename: str, artist: str, title: str, value_field: str) -> Optional[str]:
    """Load a single entry from a JSONL file.

    The JSONL cache is expected to contain entries with the keys ``artist``,
    ``title`` and the given ``value_field``.  The search is case sensitive and
    will return the first matching entry.

    Args:
        filename: Path to the JSONL file.
        artist: Artist name to match exactly.
        title: Song title to match exactly.
        value_field: Key to extract from the entry (e.g. ``"lyrics"`` or ``"chords"``).

    Returns:
        The value associated with ``value_field`` if found, otherwise ``None``.
    """
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
                    # Skip malformed lines
                    continue
        return None
    except Exception as e:
        logger.error("Error loading JSONL cache: %s", e)
        # Re‑raise to allow callers to handle fatal errors
        raise

def jsonl_save_entry(filename: str, artist: str, title: str, value: Any, value_field: str) -> None:
    """Add or update an entry in a JSONL file.

    If an entry for the given artist and title already exists, its value is
    updated.  Otherwise a new entry is appended.  The entire file is rewritten
    to ensure atomic updates.

    Args:
        filename: Path to the JSONL cache file.
        artist: Artist name.
        title: Song title.
        value: Value to store under ``value_field``.
        value_field: Field name to update (``"lyrics"`` or ``"chords"``).
    """
    entries: list[Dict[str, Any]] = []
    found = False
    # Read existing entries if file exists
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
                    # Skip malformed lines
                    continue
    if not found:
        entries.append({'artist': artist, 'title': title, value_field: value})
    # Write back all entries
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def jsonl_load_all(filename: str, value_field: str) -> Dict[str, Any]:
    """Load all entries from a JSONL file and return a mapping.

    The returned dictionary uses the key format ``"artist - title"`` and maps
    to the requested value field for each entry.  Malformed lines are skipped.

    Args:
        filename: Path to the JSONL cache file.
        value_field: Field name to extract.

    Returns:
        A dictionary mapping ``"Artist - Title"`` to the stored value.
    """
    result: Dict[str, Any] = {}
    if not os.path.exists(filename):
        return result
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                key = f"{entry.get('artist', '')} - {entry.get('title', '')}"
                result[key] = entry.get(value_field)
            except Exception:
                # Skip malformed lines
                continue
    return result