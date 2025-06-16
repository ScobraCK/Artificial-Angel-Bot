import logging
import logging.handlers
from pathlib import Path

log_dir = Path("aabot/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "bot.log"

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
        rotating_handler
    ]
)

def get_logger(name: str = __name__):
    return logging.getLogger(name)

# copy paste
# from aabot.utils.logger import get_logger
# logger = get_logger(__name__)