import json
import os

def cache_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_cache(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}
