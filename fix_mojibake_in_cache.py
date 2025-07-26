import json
import os

def fix_mojibake(text):
    if not isinstance(text, str):
        return text
    return (text
        .replace('â€™', '’')
        .replace('â€œ', '“')
        .replace('â€�', '”')
        .replace('â€“', '–')
        .replace('â€”', '—')
        .replace('â€¦', '…')
        .replace('Ã©', 'é')
        .replace('Ã¨', 'è')
        .replace('Ã', 'à')
        # Add more replacements as needed
    )

def clean_jsonl_file(filename, value_field):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    lines = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if value_field in entry and entry[value_field]:
                    entry[value_field] = fix_mojibake(entry[value_field])
                lines.append(entry)
            except Exception:
                lines.append(line)
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in lines:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

clean_jsonl_file('data/cache/lyrics_cache.jsonl', 'lyrics')
clean_jsonl_file('data/cache/chords_cache.jsonl', 'chords')
print("Cache files cleaned.") 