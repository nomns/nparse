import logging
import logging.handlers
from concurrent_log_handler import ConcurrentRotatingFileHandler

import os


def get_logger(name: str = "general") -> logging.Logger:
    # ensure log directory exists. if not, create it
    if not os.path.exists("./data/logs"):
        os.mkdir("./data/logs")
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    h = ConcurrentRotatingFileHandler(
        os.path.abspath("data/logs/nparse.log"), "a", 512 * 1000, 3
    )
    f = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    h.setFormatter(f)
    log.addHandler(h)
    return log
