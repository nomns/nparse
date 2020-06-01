
import datetime
import string

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import QTimer

from utils import format_time, get_spell_icon, sound
from config.ui import styles


from .common import NDirection


class NTimer(QFrame):

    def __init__(
        self,
        name="base",
        timestamp=None,
        duration=6,
        icon=1,
        style=None,
        sound=None,
        direction=NDirection.DOWN,
        persistent=False
    ):
        super().__init__()
        self.name = name
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
        self._duration = duration
        self._icon = icon
        self._style = style
        self._active = True
        self._sound = sound
        self._alert = False
        self._direction = direction
        self.persistent = persistent
        self.progress = QProgressBar()

        # ui
        self.setMaximumHeight(18)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(get_spell_icon(self._icon), 0)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setAutoFillBackground(True)

        # labels
        progress_layout = QHBoxLayout(self.progress)
        progress_layout.setContentsMargins(5, 0, 5, 0)
        self._name_label = QLabel(
            string.capwords(self.name), self.progress)
        progress_layout.addWidget(self._name_label)
        progress_layout.insertStretch(2, 1)
        self._time_label = QLabel('', self.progress)
        progress_layout.addWidget(self._time_label)
        layout.addWidget(self.progress, 1)

        # init
        self._calculate(self.timestamp)
        self.setStyleSheet(self._style)
        self._update()

    def _calculate(self, timestamp):
        self.end_time = timestamp + datetime.timedelta(seconds=self._duration)
        self.progress.setMaximum(self._duration)

    def recalculate(self, timestamp):
        self._calculate(timestamp)
        self.setStyleSheet(self._style)

    def _update(self):
        if self._active:
            remaining = self.end_time - datetime.datetime.now()
            remaining_seconds = max(remaining.total_seconds(), 0)
            self.progress.setValue(
                remaining.seconds
                if self._direction == NDirection.DOWN else
                self.progress.maximum() - remaining_seconds
            )
            if remaining_seconds <= 30:
                self.setStyleSheet(self.styleSheet() + styles.spell_warning())
                if not self._alert:
                    self._alert = True
                    if self._sound:
                        sound.play(self._sound)
            else:
                self._alert = False
            if remaining_seconds <= 0:
                if self.persistent:
                    self._time_label.setText("")
                else:
                    self._remove()
            else:
                self._time_label.setText(format_time(remaining))
            self.progress.update()
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
