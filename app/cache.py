import json
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def cache_data(filename, data):
    logger.debug(f"Saving cache to {filename}...")
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
        logger.debug("Cache saved successfully.")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def load_cache(filename):
    logger.debug(f"Loading cache from {filename}...")
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                cache = json.load(f)
            logger.debug("Cache loaded successfully.")
            return cache
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}
    else:
        logger.debug("Cache file does not exist.")
        return {}
