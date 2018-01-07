"""https://github.com/nomns."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
                             QPushButton)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
import datetime
from spelltracker.spell import Spell, get_spell_duration, SpellItem
from spelltracker.spellcontainer import SpellContainer


class SpellTracker(QWidget):
    """Tracks buffs and debuffs that you cast."""

    def __init__(self, settings, *args):
        # Settings
        self.settings = settings

        # Class Init
        self._active = True
        self.spell_file = 'spelltracker/data/spells_us.txt'
        self.spellbook = self.create_spellbook()
        self.parse_spell = None
        self.spells = {}
        self.spell_containers = {}

        # UI Init
        super(QWidget, self).__init__()
        self.setWindowTitle("Spell Tracker")
        self.setWindowFlags(Qt.WindowStaysOnTopHint |
                            Qt.WindowCloseButtonHint |
                            Qt.FramelessWindowHint |
                            Qt.WindowMinMaxButtonsHint)
        self.borderless = True
        self.setFocusPolicy(Qt.StrongFocus)
        print(self.settings.get_value('spelltracker', 'geometry'))
        if self.settings.get_value('spelltracker', 'geometry') is not None:
            self.setGeometry(
                self.settings.get_value('spelltracker', 'geometry')
            )
        else:
            self.setGeometry(100, 100, 400, 400)
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.grid.setAlignment(Qt.AlignTop)
        self.tracker = QWidget()
        self.vbox = QVBoxLayout()
        self.tracker.setLayout(self.vbox)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)
        self.setLayout(self.grid)
        self.setWindowOpacity(0.85)

        # Menu
        self.menu_container = QWidget()
        self.menu_container.setObjectName('menu_container')
        self.menu = QHBoxLayout()
        self.menu_container.setLayout(self.menu)
        self.menu.setSpacing(5)
        self.menu.setContentsMargins(0, 0, 0, 0)
        self.create_menu_buttons()

        # Add Gui items
        self.grid.addWidget(self.menu_container, 0, 0, 1, 1)
        self.grid.addWidget(self.tracker, 1, 0, 1, 1)

        # Spell Update Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spells)
        self.timer.start(1000)

        self.show()

    def create_menu_buttons(self):
        button_borderless_toggle = QPushButton(
            QIcon('ui/gfx/map_menu_borderless_toggle.png'),
            ''
        )
        button_borderless_toggle.setToolTip('Toggle Borderless Window')
        button_borderless_toggle.clicked.connect(self.toggle_borderless)
        self.menu.addWidget(
            button_borderless_toggle,
            0,
            Qt.AlignRight
        )

    def is_active(self):
        return self._active

    def create_spellbook(self):
        """Create a dictionary of all possible spells."""
        spells = {}
        for line in open(self.spell_file).readlines():
            l = line.split('^')
            spells[l[1]] = \
                Spell(l[0], l[1], l[3], l[6], l[7], l[8], l[16], l[17], l[83],
                      l[144])
        return spells

    def add_spell(self, target, spell, cast_time):
        level = self.settings.get_value('general', 'current_character_level')
        duration_ticks = get_spell_duration(spell, level)
        spell_duration = datetime.timedelta(
            seconds=duration_ticks * 6
        )
        if duration_ticks <= 0:
            return

        if target in self.spell_containers.keys():
            # add or update within target
            self.spell_containers[target].add_spell(
                SpellItem(
                    spell,
                    target,
                    cast_time,
                    spell_duration,
                    cast_time + spell_duration
                )
            )
        else:
            # add new container
            sc = SpellContainer(target.title())
            sc.setObjectName('container')
            self.vbox.addWidget(sc, 0, Qt.AlignTop)
            sc.add_spell(SpellItem(
                spell,
                target,
                cast_time,
                spell_duration,
                cast_time + spell_duration
                ))
            self.spell_containers[target] = sc

    def update_spells(self):
        to_delete = []
        for container in self.spell_containers.keys():
            sc = self.spell_containers[container]  # SpellContainer
            if sc.get_spell_count() <= 0:
                self.vbox.removeWidget(sc)
                to_delete.append(container)
                sc.deleteLater()
            else:
                sc.update_times()
        for container in to_delete:
            self.spell_containers.pop(container)

    def parse(self, item):
        """Parse, setup, catch casting triggers."""
        # TODO: populate spell list, update timers?, create timer for updating
        item_time, item_text = item[1:25], item[27:]
        if 'You begin casting' in item_text[:17]:
            self.parse_spell = self.spellbook[item_text[18:-2]]
        elif ('Your spell is interrupted.' in item_text[:26] or
              'Your target resisted' in item_text[:20] or
              'Your spell did not take hold.' in item_text[:29]):
            # TODO: test the above
            self.parse_spell = None
        elif self.parse_spell and self.parse_spell.effect_text_you in \
                item_text[:len(self.parse_spell.effect_text_you)]:
            casting_time = datetime.datetime.strptime(
                    item_time,
                    '%a %b %d %H:%M:%S %Y'
                    )
            self.add_spell('you', self.parse_spell, casting_time)
            self.parse_spell = None
        elif self.parse_spell and self.parse_spell.effect_text_other in \
            item_text[
                len(item_text) -
                len(self.parse_spell.effect_text_other) - 1:]:
            casting_time = datetime.datetime.strptime(
                item_time,
                '%a %b %d %H:%M:%S %Y'
                )
            target = \
                item_text[:
                          len(item_text) -
                          len(self.parse_spell.effect_text_other) -
                          1
                          ]
            self.add_spell(target, self.parse_spell, casting_time)

    def toggle_borderless(self, button):
        self.borderless = False if self.borderless else True
        if self.borderless:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.settings.set_value('spelltracker', 'geometry', self.geometry())
        self._active = False
        self.hide()
