"""Load application configuration from JSON files or environment variables."""

import logging
import json
import os
from typing import Dict

logger = logging.getLogger(__name__)

def load_config(config_file_path: str) -> Dict:
    """Load a configuration file and ensure required values are present.

    The configuration is a simple JSON object that should contain a ``genius``
    section with a ``client_access_token``.  If the token is missing from the
    file, the loader falls back to the ``GENIUS_CLIENT_ACCESS_TOKEN``
    environment variable.  An exception is raised if the token cannot be
    determined.

    Args:
        config_file_path: Path to the configuration JSON file.

    Returns:
        The configuration dictionary with at least ``genius.client_access_token`` set.
    """
    logger.info(f"Loading configuration from {config_file_path}")
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Config file {config_file_path} does not exist")
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file) or {}
    # Ensure genius section exists
    config.setdefault('genius', {})
    token = config['genius'].get('client_access_token') or os.getenv('GENIUS_CLIENT_ACCESS_TOKEN')
    if not token:
        raise ValueError(
            "Missing 'client_access_token' for Genius. "
            "Set it in config.json or as environment variable 'GENIUS_CLIENT_ACCESS_TOKEN'."
        )
    config['genius']['client_access_token'] = token
    return config