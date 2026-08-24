import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("scraper_logger")
logger.setLevel(logging.INFO)

# Guard: only attach handlers once, no matter how many times / paths this is imported through
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

logger.propagate = False
