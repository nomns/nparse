import datetime
import string

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import QTimer

from .helpers import get_spell_duration, get_spell_icon
from helpers import config, format_time


class SpellWidget(QFrame):

    def __init__(self, spell, timestamp):
        super().__init__()
        self.setObjectName('SpellWidget')
        self.spell = spell
        self._active = True

        self._setup_ui()
        self._calculate(timestamp)
        self.setProperty('Warning', False)
        self._time_label.setProperty('Warning', False)
        self._update()

    def _calculate(self, timestamp):
        self._ticks = get_spell_duration(
            self.spell, config.data['spells']['level'])
        self._seconds = (int(self._ticks * 6))
        self.end_time = timestamp + datetime.timedelta(seconds=self._seconds)
        self.progress.setMaximum(self._seconds)

    def _setup_ui(self):
        # self
        self.setMaximumHeight(17)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(get_spell_icon(self.spell.spell_icon), 0)
        layout.setSpacing(0)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        if self.spell.type:
            self.progress.setObjectName('SpellWidgetProgressBarGood')
        else:
            self.progress.setObjectName('SpellWidgetProgressBarBad')

        # labels
        progress_layout = QHBoxLayout(self.progress)
        progress_layout.setContentsMargins(5, 0, 5, 0)
        self._name_label = QLabel(
            string.capwords(self.spell.name), self.progress)
        self._name_label.setObjectName('SpellWidgetNameLabel')
        progress_layout.addWidget(self._name_label)
        progress_layout.insertStretch(2, 1)
        self._time_label = QLabel('', self.progress)
        self._time_label.setObjectName('SpellWidgetTimeLabel')
        progress_layout.addWidget(self._time_label)
        layout.addWidget(self.progress, 1)

    def recast(self, timestamp):
        self._calculate(timestamp)
        self.setProperty('Warning', False)
        self.setStyle(self.style())
        self._time_label.setProperty('Warning', False)
        self._time_label.setStyle(self._time_label.style())

    def _update(self):
        if self._active:
            remaining = self.end_time - datetime.datetime.now()
            remaining_seconds = remaining.total_seconds()
            self.progress.setValue(remaining.seconds)
            self.progress.update()
            if remaining_seconds <= 30:
                self.setProperty('Warning', True)
                self.setStyle(self.style())
                self._time_label.setProperty('Warning', True)
                self._time_label.setStyle(self._time_label.style())
            if remaining_seconds <= 0:
                self._remove()
            self._time_label.setText(format_time(remaining))
        QTimer.singleShot(1000, self._update)

    def pause(self):
        self._active = False

    def resume(self):
        self._active = True

    def elongate(self, seconds):
        self.end_time += datetime.timedelta(seconds=seconds)

    def _remove(self):
        self.setParent(None)
        self.deleteLater()

    def mouseDoubleClickEvent(self, _):
        self._remove()
