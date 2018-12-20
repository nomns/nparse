import datetime

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QEvent

from .spellwidget import SpellWidget


class SpellTarget(QFrame):

    def __init__(self, target='__you__'):
        super().__init__()
        self.name = target
        if target == '__you__':
            self.title = 'you'
        elif target == '__custom__':
            self.title = 'custom'
        else:
            self.title = target
        self._initialized = False  # don't delete until after first spell
        self.setObjectName('SpellContainer')

        self._setup_ui()

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
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

    def spell_widgets(self):
        """Returns a list of all SpellWidgets."""
        return self.findChildren(SpellWidget)

    def childEvent(self, event):
        if event.type() == QEvent.ChildRemoved:
            if type(event.child()) == SpellWidget:
                if not self.findChildren(SpellWidget):
                    self._remove()
        event.accept()

    def add_spell(self, spell, timestamp):
        target_type = spell.type  # default incoming spell type
        recast = False
        for sw in self.findChildren(SpellWidget):
            target_type *= sw.spell.type
            if sw.spell.name == spell.name:
                recast = True
                sw.recast(timestamp)
        if not recast:
            self.layout().addWidget(SpellWidget(spell, timestamp))
        if self.name == '__you__' or self.name == '__custom__':
            self.target_label.setProperty('TargetType', 0)  # user
        elif not target_type:  # treat target like enemy
            self.target_label.setProperty('TargetType', 2)  # enemy
        else:
            self.target_label.setProperty('TargetType', 1)  # friendly
        self.target_label.setStyle(self.target_label.style())

        now = datetime.datetime.now()
        for x, widget in enumerate(sorted(self.findChildren(SpellWidget), key=lambda x: (x.end_time - now))):
            self.layout().insertWidget(x + 1, widget)  # + 1 - skip target label
