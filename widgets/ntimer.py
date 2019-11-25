
import datetime
import string

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QProgressBar, QLabel
from PyQt5.QtCore import QTimer

from helpers import format_time, get_spell_icon, sound
from settings import styles


class NTimer(QFrame):

    def __init__(
        self,
        title="Test",
        timestamp=None,
        duration=6,
        icon=1,
        style=None,
        sound=None
    ):
        super().__init__()
        self.title = title
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
        self._duration = duration
        self._icon = icon
        self._style = style
        self._active = True
        self._sound = sound
        self._alert = False
        self.progress = QProgressBar()
        self._setup_ui()
        self._calculate(self.timestamp)
        self.setStyleSheet(self._style)
        self._update()

    def _calculate(self, timestamp):
        self.end_time = timestamp + datetime.timedelta(seconds=self._duration)
        self.progress.setMaximum(self._duration)

    def _setup_ui(self):
        # self
        self.setMaximumHeight(17)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.setLayout(layout)
        layout.addWidget(get_spell_icon(self._icon), 0)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)

        # labels
        progress_layout = QHBoxLayout(self.progress)
        progress_layout.setContentsMargins(5, 0, 5, 0)
        self._name_label = QLabel(
            string.capwords(self.title), self.progress)
        progress_layout.addWidget(self._name_label)
        progress_layout.insertStretch(2, 1)
        self._time_label = QLabel('', self.progress)
        progress_layout.addWidget(self._time_label)
        layout.addWidget(self.progress, 1)

    def recalculate(self, timestamp):
        self._calculate(timestamp)
        self.setStyleSheet(self._style)

    def _update(self):
        if self._active:
            remaining = self.end_time - datetime.datetime.now()
            remaining_seconds = remaining.total_seconds()
            self.progress.setValue(remaining.seconds)
            if remaining_seconds <= 30:
                self.setStyleSheet(self.styleSheet() + styles.spell_warning())
                if not self._alert:
                    self._alert = True
                    sound.play(self._sound)
            else:
                self._alert = False
            if remaining_seconds <= 0:
                self._remove()
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
