import logging
import json
    
def load_config(config_file_path):
    logging.info(f"Loading configuration from {config_file_path}")
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        error_msg = f"Configuration file not found at '{config_file_path}'. Please ensure the file exists."
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in configuration file '{config_file_path}': {e}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error loading configuration from '{config_file_path}': {e}"
        logging.error(error_msg)
        raise