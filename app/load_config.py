import logging
import json
    
def load_config(config_file_path):
    logging.info(f"Loading configuration from {config_file_path}")
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)