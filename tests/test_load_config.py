"""Tests for the ``load_config`` helper.

The configuration loader should read tokens from a JSON file and fall back
to environment variables when the token is not present.  It should raise
informative exceptions when neither source is available.
"""

import json
import os
import tempfile
import unittest

from CampfireSongbookBuilder.app.load_config import load_config


class TestLoadConfig(unittest.TestCase):
    """Unit tests for ``load_config``."""

    def test_load_token_from_file(self):
        """The token should be loaded from the JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump({'genius': {'client_access_token': 'ABC123'}}, tmp)
            tmp_path = tmp.name
        try:
            config = load_config(tmp_path)
            self.assertEqual(config['genius']['client_access_token'], 'ABC123')
        finally:
            os.remove(tmp_path)

    def test_load_token_from_environment(self):
        """When the config lacks a token, the environment variable should be used."""
        # Clear environment to a known state
        prev_token = os.environ.get('GENIUS_CLIENT_ACCESS_TOKEN')
        os.environ['GENIUS_CLIENT_ACCESS_TOKEN'] = 'ENV_TOKEN'
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump({}, tmp)
            tmp_path = tmp.name
        try:
            config = load_config(tmp_path)
            self.assertEqual(config['genius']['client_access_token'], 'ENV_TOKEN')
        finally:
            os.remove(tmp_path)
            # Restore previous environment variable
            if prev_token is not None:
                os.environ['GENIUS_CLIENT_ACCESS_TOKEN'] = prev_token
            else:
                os.environ.pop('GENIUS_CLIENT_ACCESS_TOKEN', None)

    def test_missing_token_raises_error(self):
        """If neither the file nor the environment provide a token, an error should be raised."""
        prev_token = os.environ.pop('GENIUS_CLIENT_ACCESS_TOKEN', None)
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            json.dump({}, tmp)
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValueError):
                load_config(tmp_path)
        finally:
            os.remove(tmp_path)
            # Restore previous token if it existed
            if prev_token is not None:
                os.environ['GENIUS_CLIENT_ACCESS_TOKEN'] = prev_token


if __name__ == '__main__':
    unittest.main()