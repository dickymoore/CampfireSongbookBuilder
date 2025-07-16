import json
import os
import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)

def cache_data(filename, data):
    logger.debug(f"Saving cache to {filename}...")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  # Use indent=4 to prettify JSON
        logger.debug("Cache saved successfully.")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def load_cache(filename):
    logger.debug(f"Loading cache from {filename}...")
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            logger.debug("Cache loaded successfully.")
            return cache
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            print(f"\nERROR: Failed to load cache file '{filename}'.\nReason: {e}\n")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        logger.debug("Cache file does not exist.")
        return {}
