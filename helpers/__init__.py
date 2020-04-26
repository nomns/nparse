import sys
import os
import math
import requests
import json
import re
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import QRect, Qt

from gtts import gTTS


def create_tts_mp3(text):
    try:
        tts = gTTS(text)
        if not os.path.exists('data/tts'):
            os.mkdir('data/tts')
        filename = "data/tts/{}.mp3".format(text)
        tts.save(filename)
        return filename
    except:
        return None


def get_version():
    version = None
    try:
        r = requests.get('http://nparse.nomns.com/info/version')
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

def get_line_length(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # pylint: disable=E1101
    except:
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
    else:
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
        return

    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


def set_qcolor(widget, foreground=None, background=None):
    p = widget.palette()
    if foreground:
        p.setColor(widget.foregroundRole(), QColor.fromRgb(*foreground))
    if background:
        p.setColor(widget.backgroundRole(), QColor.fromRgb(*background))
    widget.setPalette(p)


def get_rgb(widget, role):
    p = widget.palette()
    return p.color(role).getRgb()


def get_spell_icon(icon_index):
    # Spell Icons are 40x40 pixels
    file_number = math.ceil(icon_index / 36)
    file_name = 'data/spells/spells0' + str(file_number) + '.png'
    spell_number = icon_index % 36
    file_row = math.floor((spell_number + 6) / 6)
    file_col = spell_number % 6 + 1
    x = (file_col - 1) * 40
    y = (file_row - 1) * 40
    icon_image = QPixmap(file_name)
    scaled_icon_image = icon_image.copy(QRect(x, y, 40, 40)).scaled(
        18, 18, transformMode=Qt.SmoothTransformation)
    label = QLabel()
    label.setPixmap(scaled_icon_image)
    label.setFixedSize(18, 18)
    return label

def create_regex_from(text=None, regex=None):
    if text:
        return re.compile('^{}$'.format(text), re.IGNORECASE)
    else:
        return re.compile(regex)

