import logging
from logging import handlers
import os


def get_logger(name: str = 'general') -> logging.Logger:
    # ensure log directory exists. if not, create it
    if not os.path.exists('./data/logs'):
        os.mkdir('./data/logs')
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    h = logging.handlers.TimedRotatingFileHandler(
        './data/logs/nparse.log', when='d', interval=1, backupCount=3
    )
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    l.addHandler(h)
    return l
