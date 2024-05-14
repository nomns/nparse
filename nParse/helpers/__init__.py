from datetime import datetime, timedelta
import math
import os
import sys
import urllib.request
import json

import semver

def get_version():
    version = None
    try:
        response = urllib.request.urlopen("https://api.github.com/repos/nomns/nparse/releases/latest")
        response_json = json.loads(response.read().decode('utf-8'))
        version_text = response_json["tag_name"]
        version = semver.parse_version_info(version_text)
    except Exception as e:
        print(e)
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
