import json
import logging
import logging.handlers
import sys
from pathlib import Path

log_dir = Path("api/logs")
log_dir.mkdir(exist_ok=True)

text_dir = log_dir / "text"
text_dir.mkdir(exist_ok=True)

log_file = log_dir / "app.log"

rotating_handler = logging.handlers.RotatingFileHandler(
    log_file,
    mode='a',
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        rotating_handler
    ]
)

def get_logger(name: str = __name__):
    return logging.getLogger(name)

# copy paste
# from api.utils.logger import get_logger
# logger = get_logger(__name__)

def log_text_changes(old_list, new_list, version):
    '''Logs all text changes'''
    old_dict = dict(old_list)
    new_dict = dict(new_list)

    differences = {}

    all_keys = old_dict.keys() | new_dict.keys()

    for key in all_keys:
        old_value = old_dict.get(key)
        new_value = new_dict.get(key)
        if old_value != new_value:
            differences[key] = (old_value, new_value)
            
    if differences:
        log_filename = f"{version}.json"
        log_path = text_dir / log_filename  # Store logs in "api/logs/text/"

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(differences, f, indent=4, ensure_ascii=False)

    return bool(differences)