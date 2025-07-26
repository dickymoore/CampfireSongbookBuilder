#!/usr/bin/env python3
"""Utility script to clean markup tags from the chords cache.

This script reads ``data/cache/chords_cache.jsonl``, removes any bracketed
markup tags using the application's ``clean_chords`` function, and writes
the cleaned entries back to disk.  Use it when updating the cache format
or after scraping chords that include unwanted markup.

Example usage::

    python clean_chords_cache.py
"""

import json
import os
from CampfireSongbookBuilder.app.text_cleaning import clean_chords


def clean_chords_cache(cache_path: str = 'data/cache/chords_cache.jsonl') -> None:
    """Clean all chord entries in the given JSONL cache file."""
    if not os.path.exists(cache_path):
        print(f"Cache file {cache_path} does not exist")
        return
    new_entries = []
    with open(cache_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            chords = entry.get('chords', '')
            entry['chords'] = clean_chords(chords)
            new_entries.append(entry)
    with open(cache_path, 'w', encoding='utf-8') as f:
        for entry in new_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    clean_chords_cache()