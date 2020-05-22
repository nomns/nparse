from PyQt5.QtWidgets import QScrollArea

from config.ui import styles
from widgets import (NWindow, NContainer, NGroup,
                     NTimer, NDirection)
from config import profile_manager
profile = profile_manager.profile

from .spell import (create_spell_book, get_spell_duration,
                    SpellTrigger)


class Spells(NWindow):
    """Tracks spell casting, duration, and targets by name."""

    def __init__(self):
        super().__init__(name='spells')

        # ui
        self.setMinimumWidth(150)
        self._spell_container = NContainer()
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._spell_container)
        self._scroll_area.setObjectName('ScrollArea')
        self.content.addWidget(self._scroll_area, 1)

        self.spell_book = create_spell_book()
        self._casting = None  # holds Spell when casting
        self._zoning = None  # holds time of zone or None
        self._spell_triggers = []  # need a queue because of landing windows
        self._spell_trigger = None

    def _spell_triggered(self):
        """SpellTrigger spell_triggered event handler. """
        if self._spell_trigger:
            if self._spell_trigger.activated:
                s = self._spell_trigger.spell
                for target in self._spell_trigger.targets:
                    group_name = target[1]
                    group = None
                    for g in self._spell_container.groups():
                        if g.name == group_name:
                            group = g
                    if not group:
                        group = NGroup(group_name=group_name)
                        if group_name == '__you__':
                            group.set_title('You')
                            group.setStyleSheet(styles.you_target())
                        else:
                            if s.type:
                                group.setStyleSheet(styles.friendly_target())
                                group.order = 1
                            else:
                                group.setStyleSheet(styles.enemy_target())
                                group.order = 2

                    self._spell_container.add_timer(
                        group,
                        NTimer(
                            name=s.name,
                            timestamp=target[0],
                            duration=get_spell_duration(
                                s,
                                profile.spells.level
                            ) * 6,
                            icon=s.spell_icon,
                            style=(
                                styles.good_spell()
                                if s.type else
                                styles.debuff_spell()
                            ),
                            sound=(
                                profile.spells.sound_file
                                if profile.spells.sound_enabled
                                else None
                            ),
                            direction=NDirection.DOWN
                        ),
                    )
        self._remove_spell_trigger()

    def parse(self, timestamp, text):

        """Parse casting triggers (casting, failure, success)."""
        if self._spell_trigger:
            self._spell_trigger.parse(timestamp, text)

        # Initial Spell Cast and trigger setup
        if text[:17] == 'You begin casting':
            s = self.spell_book.get(text[18:-1].lower(), None)
            if s and s.duration_formula != 0:
                self._spell_triggered()  # in case we cut off the cast window, force trigger
                self._remove_spell_trigger()

                spell_trigger = SpellTrigger(
                    spell=s,
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
            spell_target = self._spell_container.get_group_by_name(
                '__you__')
            if spell_target:
                for spell_widget in spell_target.timers():
                    spell_widget.pause()
        elif self._zoning and text[:16] == 'You have entered':
            delay = (timestamp - self._zoning).total_seconds()
            self._zoning = None
            spell_target = self._spell_container.get_group_by_name(
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

    def settings_updated(self):
        super().settings_updated()

    def toggle_menu(self, on=True):
        pass  # do not use menu
