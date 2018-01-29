import sys
import os
from datetime import datetime

def parse_line(line: str):
    """
    Parses and then returns an everquest log entry's date and text.
    """
    index = line.find("]") + 1
    sdate = line[1:index-1].strip()
    text = line[index:].strip()
    return datetime.strptime(sdate, '%a %b %d %H:%M:%S %Y'), text

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
