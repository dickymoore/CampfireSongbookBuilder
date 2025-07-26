import json
import os
import re

MARKUP_TAGS = [
    'ch', '/ch', 'tab', '/tab', 'verse', '/verse', 'intro', '/intro',
    'outro', '/outro', 'pre-chorus', '/pre-chorus', 'chorus', '/chorus',
    'bridge', '/bridge', 'solo', '/solo', 'instrumental', '/instrumental',
    'repeat', '/repeat', 'end', '/end', 'coda', '/coda', 'refrain', '/refrain'
]

def remove_markup_tags(text):
    if not isinstance(text, str):
        return text
    pattern = r'\[(' + '|'.join(re.escape(tag) for tag in MARKUP_TAGS) + r')\]'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

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
                    entry[value_field] = remove_markup_tags(entry[value_field])
                lines.append(entry)
            except Exception:
                lines.append(line)
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in lines:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

clean_jsonl_file('data/cache/chords_cache.jsonl', 'chords')
print("Markup tags removed from chords cache.") 