import logging
from logging import handlers
import os

from helpers import re

def get_logger(name: str = 'general') -> logging.Logger:
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    h = logging.handlers.TimedRotatingFileHandler(
        './logs/nparse.log', when='d', interval=1, backupCount=3
    )
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    l.addHandler(h)
    return l
