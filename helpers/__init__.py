from datetime import datetime, timedelta
import json
import math
import os
import sys

import requests
import json

import psutil

from datetime import datetime, timedelta

from .parser import Parser  # noqa: F401
from .parser import ParserWindow  # noqa: F401


def get_version():
    version = None
    try:
        r = requests.get('http://sheeplauncher.net/~adam/nparse_version.json')
        version = json.loads(r.text)['version']
    except:
        pass
    return version


def parse_line(line):
    """
    Parses and then returns an everquest log entry's date and text.
    """
    index = line.find("]") + 1
    sdate = line[1:index - 1].strip()
    text = line[index:].strip()
    return datetime.strptime(sdate, '%a %b %d %H:%M:%S %Y'), text


def strip_timestamp(line):
    """
    Strings EQ Timestamp from log entry.
    """
    return line[line.find("]") + 1:].strip()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # pylint: disable=E1101,W0212
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def to_range(number, min_number, max_number):
    """ Returns number of within min/max, else min/max. """
    return min(max_number, max(min_number, number))


def within_range(number, min_number, max_number):
    """ Returns true/false if number is within min/max. """
    return min_number <= number <= max_number


def to_real_xy(x, y):
    """ Convert Everquest 'x, y' to standard 'x, y'. """
    return -y, -x


def to_eq_xy(x, y):
    """ Convert standard x, y to Everquest x, y. """
    return -y, -x


def get_degrees_from_line(x1, y1, x2, y2):
    return -math.degrees(math.atan2((x2 - x1), (y2 - y1)))


def format_time(time_delta):
    """Returns a string from a timedelta '#d #h #m #s', but only 's' if d, h, m are all 0."""
    time_string = ''
    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if sum([days, hours, minutes]):
        time_string += '{}d'.format(days) if days else ''
        time_string += '{}h'.format(hours) if hours else ''
        time_string += '{}m'.format(minutes) if minutes else ''
        time_string += '{}s'.format(seconds) if seconds else ''
        return time_string
    return str(seconds)


def text_time_to_seconds(text_time):
    """ Returns string 'hh:mm:ss' -> seconds """
    parts = text_time.split(':')
    seconds, minutes, hours = 0, 0, 0
    try:
        seconds = int(parts[-1])
        minutes = int(parts[-2])
        hours = int(parts[-3])
    except IndexError:
        pass
    except ValueError:
        pass

    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


def get_eqgame_pid_list() -> list[int]:
    """
    get list of process ID's for eqgame.exe, using psutil module

    Returns:
        object: list of process ID's (in case multiple versions of eqgame.exe are somehow running)
    """

    pid_list = list()
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'eqgame.exe':
            pid_list.append(p.pid)
    return pid_list


def starprint(line: str) -> None:
    """
    utility function to print with leading and trailing ** indicators

    Args:
        line: text to be printed

    Returns:
        None:
    """
    print(f'** {line.rstrip():<100} **')
