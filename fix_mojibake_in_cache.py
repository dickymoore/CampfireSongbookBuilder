#!/usr/bin/env python3
"""Fix mojibake (encoding issues) in JSONL cache files.

Some cached entries may be improperly encoded due to upstream source errors or
incorrect decoding when saving.  This utility reads each JSONL file in
``data/cache`` and attempts to reparse entries that fail to decode.  Lines
that still cannot be decoded are skipped.

Example usage::

    python fix_mojibake_in_cache.py
"""

import json
import os


def fix_mojibake_in_cache(cache_file: str) -> None:
    """Attempt to fix JSON decoding errors for a single cache file."""
    new_entries = []
    with open(cache_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                new_entries.append(json.loads(line))
            except json.JSONDecodeError:
                # Attempt a best‑effort fix by ignoring encoding errors
                try:
                    fixed_line = line.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
                    new_entries.append(json.loads(fixed_line))
                except Exception:
                    # Skip irreparable lines
                    continue
    # Rewrite the cache file with cleaned entries
    with open(cache_file, 'w', encoding='utf-8') as f:
        for entry in new_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    cache_dir = 'data/cache'
    for filename in os.listdir(cache_dir):
        if filename.endswith('.jsonl'):
            path = os.path.join(cache_dir, filename)
            fix_mojibake_in_cache(path)