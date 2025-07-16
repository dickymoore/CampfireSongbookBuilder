import json
from app.text_cleaning import clean_chords

cache_path = "data/cache/chords_cache.json"

with open(cache_path, "r", encoding="utf-8") as f:
    chords_cache = json.load(f)

cleaned_cache = {}
for key, value in chords_cache.items():
    if isinstance(value, str):
        cleaned_cache[key] = clean_chords(value)
    else:
        cleaned_cache[key] = value

with open(cache_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_cache, f, indent=4, ensure_ascii=False)

print("Chords cache cleaned!") 