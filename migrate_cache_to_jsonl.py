#!/usr/bin/env python3
"""Migrate legacy JSON cache files to JSONL format.

Older versions of the application stored cache files in a single JSON
dictionary mapping ``artist - title`` to the lyrics or chords.  This
script converts such files to the JSONL format expected by the current
implementation, where each line is a separate JSON object containing
``artist``, ``title`` and the value (lyrics or chords).

Example usage::

    python migrate_cache_to_jsonl.py chords_cache

This will read ``data/cache/chords_cache.json`` and write
``data/cache/chords_cache.jsonl``, then remove the original JSON file.
"""

import json
import os
import sys


def migrate_cache_to_jsonl(cache_basename: str) -> None:
    """Convert ``cache_basename.json`` to ``cache_basename.jsonl``."""
    json_path = os.path.join('data', 'cache', f'{cache_basename}.json')
    jsonl_path = os.path.join('data', 'cache', f'{cache_basename}.jsonl')
    if not os.path.exists(json_path):
        print(f"No legacy cache found at {json_path}")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for key, value in data.items():
            try:
                artist, title = key.split(' - ', 1)
            except ValueError:
                # If the key does not contain a separator, skip this entry
                continue
            entry = {'artist': artist, 'title': title}
            # Determine field name based on the basename
            if 'lyrics' in cache_basename:
                entry['lyrics'] = value
            else:
                entry['chords'] = value
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    os.remove(json_path)
    print(f"Migrated {json_path} to {jsonl_path}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python migrate_cache_to_jsonl.py <cache_basename>")
        print("For example: python migrate_cache_to_jsonl.py lyrics_cache")
        sys.exit(1)
    migrate_cache_to_jsonl(sys.argv[1])