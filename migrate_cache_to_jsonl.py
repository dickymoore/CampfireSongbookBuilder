import json
import os

def migrate_json_to_jsonl(json_path, jsonl_path, value_field):
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for key, value in cache.items():
            if ' - ' in key:
                artist, title = key.split(' - ', 1)
            else:
                artist, title = '', key
            entry = {"artist": artist, "title": title, value_field: value}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Migrated {json_path} to {jsonl_path}")

if __name__ == "__main__":
    migrate_json_to_jsonl("data/cache/lyrics_cache.json", "data/cache/lyrics_cache.jsonl", "lyrics")
    migrate_json_to_jsonl("data/cache/chords_cache.json", "data/cache/chords_cache.jsonl", "chords")
    print("Migration complete!") 