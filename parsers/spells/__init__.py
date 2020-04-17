from PyQt5.QtWidgets import QScrollArea, QSpinBox

from helpers import config
from widgets.parser import ParserWindow
from .spellcontainer import SpellContainer
from .spelltrigger import SpellTrigger
from .spell import create_spell_book


class Spells(ParserWindow):
    """Tracks spell casting, duration, and targets by name."""

    def __init__(self):
        super().__init__()
        self.name = 'spells'
        self.set_title(self.name.title())

        self._setup_ui()

        self.spell_book = create_spell_book()
        self._casting = None  # holds Spell when casting
        self._zoning = None  # holds time of zone or None
        self._spell_triggers = []  # need a queue because of landing windows
        self._spell_trigger = None

    def _setup_ui(self):
        self.setMinimumWidth(150)
        self._spell_container = SpellContainer()
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._spell_container)
        self._scroll_area.setObjectName('SpellScrollArea')
        self.content.addWidget(self._scroll_area, 1)
        self._level_widget = QSpinBox()
        self._level_widget.setRange(1, 65)
        self._level_widget.setValue(config.data['spells']['level'])
        self._level_widget.setPrefix('lvl. ')
        self.menu_area.addWidget(self._level_widget, 0)
        self._level_widget.valueChanged.connect(self._level_change)

    def _spell_triggered(self):
        """SpellTrigger spell_triggered event handler. """
        if self._spell_trigger:
            if self._spell_trigger.activated:
                for target in self._spell_trigger.targets:
                    self._spell_container.add_timer(
                        self._spell_trigger.spell, target[0], target[1])
        self._remove_spell_trigger()

    def parse(self, timestamp, text):
        """Parse casting triggers (casting, failure, success)."""
        if self._spell_trigger:
            self._spell_trigger.parse(timestamp, text)

        # Initial Spell Cast and trigger setup
        if text[:17] == 'You begin casting':
            spell = self.spell_book.get(text[18:-1].lower(), None)
            if spell and spell.duration_formula != 0:
                self._spell_triggered()  # in case we cut off the cast window, force trigger
                self._remove_spell_trigger()

                spell_trigger = SpellTrigger(
                    spell=spell,
                    timestamp=timestamp
                )
                spell_trigger.spell_triggered.connect(self._spell_triggered)
                self._spell_trigger = spell_trigger

        # Spell Interrupted
        elif (self._spell_triggers and  # noqa W504
              text[:26] == 'Your spell is interrupted.' or  # noqa W504
              text[:20] == 'Your target resisted' or  # noqa W504
              text[:29] == 'Your spell did not take hold.' or  # noqa W504
              text[:26] == 'You try to cast a spell on'):
            self._remove_spell_trigger()

        # Elongate self buff timers by time zoning
        elif text[:23] == 'LOADING, PLEASE WAIT...':
            self._spell_triggered()
            self._remove_spell_trigger()
            self._zoning = timestamp
            spell_target = self._spell_container.get_spell_target_by_name(
                '__you__')
            if spell_target:
                for spell_widget in spell_target.timers():
                    spell_widget.pause()
        elif self._zoning and text[:16] == 'You have entered':
            delay = (timestamp - self._zoning).total_seconds()
            self._zoning = None
            spell_target = self._spell_container.get_spell_target_by_name(
                '__you__')
            if spell_target:
                for spell_widget in spell_target.timers():
                    spell_widget.elongate(delay)
                    spell_widget.resume()

    def _remove_spell_trigger(self):
        if self._spell_trigger:
            self._spell_trigger.stop()
            self._spell_trigger.deleteLater()
            self._spell_trigger = None

    def _level_change(self, _):
        config.data['spells']['level'] = self._level_widget.value()
        config.save()
