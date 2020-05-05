import logging
from logging import handlers
from helpers import re

def get_logger(name: str = 'general') -> logging.Logger:
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    h = logging.handlers.TimedRotatingFileHandler(
        './logs/nparse.log', when='d', interval=1, backupCount=3
    )
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    l.addHandler(h)
    return l
