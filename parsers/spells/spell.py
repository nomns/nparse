"""github.com/nomns."""
from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel,
                             QProgressBar, QToolTip)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRect, Qt
from collections import namedtuple
import math
import datetime
import os.path

Spell = namedtuple(
    "Spell",
    "id name pet_location effect_text_you effect_text_other \
    effect_text_worn_off duration_formula duration type spell_icon"
)


def get_spell_duration(spell, level):
    sp_durationformula = int(spell.duration_formula)
    sp_duration = int(spell.duration)
    sp_ticks = 0
    df = sp_durationformula
    if df == 0:
        sp_ticks = 0
    if df == 1:
        sp_ticks = int(math.ceil(level / float(2.0)))
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 2:
        sp_ticks = int(math.ceil(level / float(5.0) * 3))
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 3:
        sp_ticks = int(level * 30)
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 4:
        if sp_duration == 0:
            sp_ticks = 50
        else:
            sp_ticks = sp_duration
    if df == 5:
        sp_ticks = sp_duration
        if sp_ticks == 0:
            sp_ticks = 3
    if df == 6:
        sp_ticks = int(math.ceil(level / float(2.0)))
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 7:
        sp_ticks = level
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 8:
        sp_ticks = level + 10
    if df == 9:
        sp_ticks = int((level * 2) + 10)
    if df == 10:
        sp_ticks = int(level * 3 + 10)
        if sp_ticks > sp_duration:
            sp_ticks = sp_duration
    if df == 11:
        sp_ticks = sp_duration
    if df == 12:
        sp_ticks = sp_duration
    if df == 15:
        sp_ticks = sp_duration
    if df == 50:
        sp_ticks = 72000
    if df == 3600:
        if sp_duration == 0:
            sp_ticks = 3600
        else:
            sp_ticks = sp_duration
    return sp_ticks


def get_spell_icon(icon_index):
    # Spell Icons are 40x40 pixels
    file_number = math.ceil(icon_index/36)
    file_name = 'ui/gfx/spells0' + str(file_number) + '.png'
    spell_number = (icon_index) % 36
    file_row = math.floor((spell_number+6)/6)
    file_col = spell_number % 6 + 1
    rect = QRect((file_col - 1) * 40, (file_row - 1) * 40, 40, 40)
    return QPixmap(file_name).copy(rect)


class SpellItem(QWidget):

    def __init__(self, spell, target, start_time, duration, end_time, *args):
        QWidget.__init__(self, *args)
        self.setObjectName('spell_item')
        self.spell = spell
        self.start_time = start_time
        self.duration = duration
        self.end_time = end_time
        self.setToolTip(spell.name)
        grid = QGridLayout(self)
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        self.spell_icon = QLabel()
        icon = get_spell_icon(int(self.spell.spell_icon))
        self.spell_icon.setPixmap(icon.scaledToWidth(20))
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(20, 20)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        grid.addWidget(self.spell_icon, 0, 0)
        grid.addWidget(self.progress_bar, 0, 0)
        self.remaining_time = 0
        self.delete_me = False
        self.update_time()

    def recast_time(self, start_time, duration, end_time):
        self.start_time = start_time
        self.duration = duration
        self.end_time = end_time
        self.update_time()

    def update_time(self):
        remaining = self.end_time - datetime.datetime.now()
        remaining = remaining - datetime.timedelta(
            microseconds=remaining.microseconds
        )
        total = self.end_time - self.start_time
        if remaining.total_seconds() < 20:
            self.setStyleSheet("QProgressBar::chunk { background-color: \
                                rgba(255, 0, 0, 100) }")
        else:
            self.setStyleSheet("")
        self.progress_bar.setValue(100 - (100*remaining/total))
        self.setToolTip('{}\n{}'.format(
            self.spell.name,
            str(remaining)
        ))
        self.remaining_time = remaining
        self.progress_bar.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.delete_me = True
            self.setHidden(True)
