"""github.com/nyhex."""
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel,
                             QHBoxLayout)
from PyQt5.QtCore import Qt
from spelltracker.spell import SpellItem


class SpellContainer(QFrame):

    def __init__(self, target, *args):
        QFrame.__init__(self, *args)
        self.setObjectName('container')
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        self.target = target
        target_label = QLabel()
        target_label.setObjectName('container_label')
        target_label.setText(self.target)
        grid.addWidget(target_label, 0, 0, 1, 1,
                       Qt.AlignLeft | Qt.AlignVCenter)
        self.spell_box = QFrame()
        self.spell_box.setObjectName('container_spell_box')
        grid.addWidget(self.spell_box, 0, 1, 1, 1,
                       Qt.AlignLeft)
        grid.setAlignment(Qt.AlignLeft)
        self.spell_box_hbox = QHBoxLayout(self.spell_box)
        self.spell_box_hbox.setSpacing(0)
        self.spell_box_hbox.setContentsMargins(0, 0, 0, 0)
        self.spell_box.setLayout(self.spell_box_hbox)
        self.spells = {}
        self.spell_count = 0

    def add_spell(self, spell_item):
        if spell_item.spell.name in self.spells.keys():
            self.spells[spell_item.spell.name].recast_time(
                spell_item.start_time,
                spell_item.duration,
                spell_item.end_time
            )
        else:
            self.spells[spell_item.spell.name] = spell_item
            self.spell_box_hbox.addWidget(spell_item, 0, Qt.AlignLeft)

    def update_times(self):
        to_delete = []
        for widget in self.spell_box.children():
            if type(widget) == SpellItem:
                widget.update_time()
                if widget.remaining_time.total_seconds() < 0 or \
                        widget.delete_me:
                    self.spell_box_hbox.removeWidget(widget)
                    widget.deleteLater()
                    to_delete.append(widget.spell.name)
        for spell_item in to_delete:
            self.spells.pop(spell_item)

    def get_spell_count(self):
        return len(self.spells)
