import logging


def get_logger(name: str = 'general') -> logging.Logger:
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    h = logging.FileHandler('nparse.log')
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h.setFormatter(f)
    l.addHandler(h)
    return l



