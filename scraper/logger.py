import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: str) -> logging.Logger:
    """
    Configures and returns a logger that prefixes messages with DEBUG:
    and includes timestamps.
    """
    base_folder = Path(__name__).resolve().parent
    log_file = f'{base_folder}/scraper/scraper.log'

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter("DEBUG: %(asctime)s %(levelname)s: %(message)s")
    handler = logging.FileHandler(log_file)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger
