#!/usr/bin/env python3
"""Utility script to strip bracketed directives from the chords cache.

Many scraped chord charts contain inline directives enclosed in square brackets
such as ``[ch]``, ``[intro]`` or custom comments.  When creating printable
songbooks these tags should be removed.  This script reads the existing
chords cache JSONL file, removes any content enclosed in brackets and
rewrites the file.

Example usage::

    python clean_chords_cache_brackets.py
"""

import json
import os
import re


def clean_chords_cache_brackets(cache_path: str = 'data/cache/chords_cache.jsonl') -> None:
    """Remove bracketed content from all chord entries in the cache."""
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
            # Remove anything enclosed in [ ] brackets
            cleaned = re.sub(r'\[[^\]]*\]', '', chords)
            entry['chords'] = cleaned
            new_entries.append(entry)
    with open(cache_path, 'w', encoding='utf-8') as f:
        for entry in new_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    clean_chords_cache_brackets()