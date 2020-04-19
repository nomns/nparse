from PyQt5.QtWidgets import QFrame, QVBoxLayout

from .spelltarget import SpellTarget
from widgets.ntimer import NTimer
from .spell import get_spell_duration
from helpers import config
from settings import styles


class SpellContainer(QFrame):

    def __init__(self):
        super().__init__()
        self.setObjectName('Container')
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addStretch(1)

    def add_timer(self, spell, timestamp, target):
        spell_target = None
        new_target = False
        for st in self.findChildren(SpellTarget):
            if st.name == target:
                spell_target = st
        if not spell_target:
            new_target = True
            spell_target = SpellTarget(
                target=target,
                order=0 if target[0] == '_' else (
                    1 if spell.type else 2
                )
            )
            if target[0] != '_':
                spell_target.setStyleSheet(
                    styles.friendly_target() if spell.type else styles.enemy_target()
                )
            else:
                spell_target.setStyleSheet(styles.you_target())
            self.layout().addWidget(spell_target, 0)

        if new_target:
            self._sort()

        # Add or update timer within SpellTarget
        ntimers = spell_target.findChildren(NTimer)
        for nt in ntimers:
            if nt.title == spell.name:
                nt.recalculate(timestamp)
        else:
            # Create timer
            nt = NTimer(
                name=spell.name,
                timestamp=timestamp,
                duration=get_spell_duration(spell, config.data['spells']['level']) * 6,
                icon=spell.spell_icon,
                style=(styles.good_spell() if spell.type else styles.debuff_spell()),
                sound=config.data['spells']['sound_file'] if config.data['spells']['sound_enabled'] else None
            )
            spell_target.add_timer(nt)

    def _sort(self):
        for x, st in enumerate(sorted(self.findChildren(SpellTarget), key=lambda x: (x.order, x.name))):
            self.layout().insertWidget(x, st, 0)

    def spell_targets(self):
        """Returns a list of all SpellTargets."""
        return self.findChildren(SpellTarget)

    def get_spell_target_by_name(self, name):
        spell_targets = [
            target for target in self.spell_targets() if target.name == name]
        if spell_targets:
            return spell_targets[0]
        return None
