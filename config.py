import json
import logging
import shutil
from pathlib import Path
from typing import Tuple, List

LOG_FILENAME = 'app.log'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILENAME)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

CONFIG_FILENAME = 'credentials.json'
EXAMPLE_CONFIG_FILENAME = 'credentials.example.json'
USER_AGENTS_FILENAME = 'user_agents.json'

def load_credentials(filename: str = CONFIG_FILENAME) -> Tuple[str, str]:
    config_path = Path(filename)
    if not config_path.exists():
        example_config_path = Path(EXAMPLE_CONFIG_FILENAME)
        if example_config_path.exists():
            shutil.copy(example_config_path, config_path)
            logger.info(f"Copied {EXAMPLE_CONFIG_FILENAME} to {filename}.")
        else:
            logger.error(f"Neither {filename} nor {EXAMPLE_CONFIG_FILENAME} found.")
            exit(1)
    try:
        with config_path.open('r') as f:
            credentials = json.load(f)
        return credentials['api_key'], credentials['cx']
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error loading credentials: {e}")
        exit(1)

def load_user_agents(filename: str = USER_AGENTS_FILENAME) -> List[str]:
    user_agents_path = Path(filename)
    try:
        with user_agents_path.open('r') as f:
            user_agents = json.load(f)
        return user_agents
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading user agents: {e}")
        exit(1)
