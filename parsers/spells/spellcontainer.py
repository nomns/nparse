from PyQt5.QtWidgets import QFrame, QVBoxLayout

from .spelltarget import SpellTarget


class SpellContainer(QFrame):

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.setObjectName('SpellContainer')
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addStretch(1)

    def add_spell(self, spell, timestamp, target='__you__'):
        spell_target = None
        new = False
        for st in self.findChildren(SpellTarget):
            if st.name == target:
                spell_target = st
        if not spell_target:
            new = True
            spell_target = SpellTarget(target=target)
            self.layout().addWidget(spell_target, 0)

        spell_target.add_spell(spell, timestamp)

        if new:
            for x, widget in enumerate(sorted(self.findChildren(SpellTarget),
                                              key=lambda x: (int(x.target_label.property('TargetType')), x.name))):
                self.layout().insertWidget(x, widget, 0)  # + 1 - skip target label

    def spell_targets(self):
        """Returns a list of all SpellTargets."""
        return self.findChildren(SpellTarget)

    def get_spell_target_by_name(self, name):
        spell_targets = [
            target for target in self.spell_targets() if target.name == name]
        if spell_targets:
            return spell_targets[0]
        return None
