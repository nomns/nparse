import datetime

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QEvent

from .ntimer import NTimer
from . import NGrow


class NContainer(QFrame):

    def __init__(self):
        super().__init__()
        self.setObjectName('Container')
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addStretch(1)

    def add_timer(self, group, timer):
        # handle group
        if group not in self.groups():
            self.layout().addWidget(group, 0)
            self.sort()

        # handle timer
        for n_timer in group.findChildren(NTimer):
            if n_timer.name == timer.name:
                n_timer.recalculate(timer.timestamp)
        else:
            group.add_timer(timer)

    def sort(self):
        for x, group in enumerate(sorted(self.groups(), key=lambda x: (x.order, x.name))):
            self.layout().insertWidget(x, group, 0)

    def groups(self):
        """Returns a list of all NGroup."""
        return self.findChildren(NGroup)

    def get_group_by_name(self, name):
        groups = [
            group for group in self.groups() if group.name == name]
        if groups:
            return groups[0]
        return None


class NGroup(QFrame):

    def __init__(
            self,
            group_name=None,
            order=0,
            hide_title=False,
            grow=NGrow.DOWN
    ):
        super().__init__()
        self.setObjectName('Container')
        self.name = group_name
        self.order = order
        self._hide_title = hide_title
        self.name_label = None

        # ui
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        if self.name and not self._hide_title:
            self.name_label = QLabel(self.name.title())
            self.name_label.setObjectName('GroupLabel')
            self.name_label.setMaximumHeight(20)
            self.name_label.setAlignment(Qt.AlignCenter)
            self.name_label.mouseDoubleClickEvent = self._remove
            self.layout().addWidget(self.name_label, 0)
            self.layout().addStretch()

    def set_title(self, title):
        if self.name_label:
            self.name_label.setText(title)

    def _remove(self, event=None):
        self.setParent(None)
        self.deleteLater()

    def childEvent(self, event):
        if event.type() == QEvent.ChildRemoved:
            if type(event.child()) == NTimer:
                if not self.findChildren(NTimer):
                    self._remove()
        event.accept()

    def sort(self):
        for x, widget in enumerate(sorted(
                self.findChildren(NTimer),
                key=lambda x: (x.end_time - datetime.datetime.now())
        )):
            self.layout().insertWidget(
                x + (0 if self._hide_title else 1),
                widget)  # +- 1  skip target label if hidden

    def add_timer(self, n_timer):
        for nt in self.findChildren(NTimer):
            if nt.name == n_timer.name:
                nt.recalculate(n_timer.timestamp)
                return
        self.layout().addWidget(n_timer)
        self.sort()

    def timers(self):
        return self.findChildren(NTimer)
