import datetime

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QEvent

from widgets.ntimer import NTimer


class SpellTarget(QFrame):

    def __init__(self, target='__you__', order=0):
        super().__init__()
        self.setObjectName('Container')
        self.name = target
        self.order = order
        if target == '__you__':
            self.title = 'you'
        elif target == '_':
            self.title = ''
        else:
            self.title = target

        self._setup_ui()

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        if self.title:
            self.target_label = QLabel(self.title.title())
            self.target_label.setObjectName('SpellTargetLabel')
            self.target_label.setMaximumHeight(20)
            self.target_label.setAlignment(Qt.AlignCenter)
            self.target_label.mouseDoubleClickEvent = self._remove
            self.layout().addWidget(self.target_label, 0)
        self.layout().addStretch()

    def _remove(self, event=None):
        self.setParent(None)
        self.deleteLater()

    def childEvent(self, event):
        if event.type() == QEvent.ChildRemoved:
            if type(event.child()) == NTimer:
                if not self.findChildren(NTimer):
                    self._remove()
        event.accept()

    def _sort(self):
        for x, widget in enumerate(sorted(
            self.findChildren(NTimer),
            key=lambda x: (x.end_time - datetime.datetime.now())
        )):
            self.layout().insertWidget(x + 1, widget)  # + 1 - skip target label

    def add_timer(self, ntimer):
        recast = False
        for nt in self.findChildren(NTimer):
            if nt.title == ntimer.title:
                recast = True
                nt.recalculate(ntimer.timestamp)
        if not recast:
            self.layout().addWidget(ntimer)

        self._sort()
