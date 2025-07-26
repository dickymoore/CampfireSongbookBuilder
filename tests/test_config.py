import unittest
from app.load_config import load_config

class TestConfig(unittest.TestCase):
    def test_load_config(self):
        config = load_config('data/config/config.example.json')
        self.assertIn('genius', config)
        self.assertIn('client_access_token', config['genius'])

if __name__ == '__main__':
    unittest.main() 