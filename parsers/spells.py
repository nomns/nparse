import datetime
import math
from collections import namedtuple

from PyQt5.QtCore import QEvent, QObject, QRect, Qt, QTimer
from PyQt5.QtGui import QCursor, QIcon, QPixmap
from PyQt5.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QInputDialog, QLabel, QMenu, QProgressBar,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from helpers import config, resource_path, format_time
from parsers import ParserWindow


class Spells(ParserWindow):
    """Tracks spell casting, duration, and targets by name."""

    def __init__(self):
        super().__init__()
        self.name = 'spells'
        self.setWindowTitle(self.name.title())
        self.set_title(self.name.title())
        self._setup_ui()

        self.spell_book = create_spell_book()
        self._casting = None  # holds Spell when casting

    def _setup_ui(self):
        self.setMinimumWidth(150)
        self._spell_container = SpellContainer()
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._spell_container)
        self._scroll_area.setObjectName('SpellScrollArea')
        self.content.addWidget(self._scroll_area, 1)
        self._settings_button = QPushButton(u'\u2699')
        self._settings_button.setObjectName('ParserButton')
        self.menu_area.addWidget(self._settings_button, 0)
        self._settings_button.clicked.connect(self._settings_context_menu)

    def parse(self, timestamp, text):
        """Parse casting triggers (casting, failure, success."""
        if text[:17] == 'You begin casting':
            self._casting = None
            spell = self.spell_book.get(text[18:-1], None)
            if spell and spell.duration_formula != 0:
                self._casting = spell
                self._casting_time = timestamp
        elif (self._casting and
              text[:26] == 'Your spell is interrupted.' or
              text[:20] == 'Your target resisted' or
              text[:29] == 'Your spell did not take hold.' or
              text[:26] == 'You try to cast a spell on'):
            self._casting = None
        elif (self._casting and
              text[:len(self._casting.effect_text_you)] in self._casting.effect_text_you and
              len(self._casting.effect_text_you) > 0):
            self._spell_container.add_spell(self._casting, timestamp)
            self._casting = None
        elif (self._casting and
              text[len(text) - len(self._casting.effect_text_other):] == self._casting.effect_text_other and
              len(self._casting.effect_text_other) > 0):
            target = text[:len(text) - len(self._casting.effect_text_other)]
            self._spell_container.add_spell(self._casting, timestamp, target)
            self._casting = None

    def _settings_context_menu(self, event):
        menu = QMenu(self._settings_button)
        menu.setAttribute(Qt.WA_DeleteOnClose)
        level_change = menu.addAction(
            'Change Level ({})'.format(config.data['spells']['level']))
        pvp_durations = menu.addAction('Use PvP Formulas (untested)')
        pvp_durations.setCheckable(True)
        if config.data['spells']['use_secondary_all']:
            pvp_durations.setChecked(True)

        action = menu.exec_(QCursor.pos())

        if action == level_change:
            dialog = QInputDialog()
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            level, changed = dialog.getInt(self._settings_button, 'Change Level',
                                           'Enter your current level.', config.data['spells']['level'], 1, 65, 1)
            if changed:
                config.data['spells']['level'] = level
                config.save()

        if action == pvp_durations:
            config.data['spells']['use_secondary_all'] = pvp_durations.isChecked()
            config.save()


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


class SpellTarget(QFrame):

    def __init__(self, target='__you__'):
        super().__init__()
        self.name = target
        self.title = 'you' if target == '__you__' else target
        self._initialized = False  # don't delete until after first spell
        self.setObjectName('SpellContainer')

        self._setup_ui()

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
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
        if self.name == '__you__':
            self.target_label.setProperty('TargetType', 0)  # user
        elif not target_type:  # treat target like enemy
            self.target_label.setProperty('TargetType', 2)  # enemy
        else:
            self.target_label.setProperty('TargetType', 1)  # friendly
        self.target_label.setStyle(self.target_label.style())

        now = datetime.datetime.now()
        for x, widget in enumerate(sorted(self.findChildren(SpellWidget), key=lambda x: (x.end_time - now))):
            self.layout().insertWidget(x + 1, widget)  # + 1 - skip target label


class SpellWidget(QFrame):

    def __init__(self, spell, timestamp):
        super().__init__()
        self.setObjectName('SpellWidget')
        self.spell = spell

        self._setup_ui()
        self._calculate(timestamp)
        self.setProperty('Warning', False)
        self._time_label.setProperty('Warning', False)
        self._update()

    def _calculate(self, timestamp):
        self._ticks = get_spell_duration(
            self.spell, config.data['spells']['level'])
        self._seconds = (int(self._ticks * 6 +
                             config.data['spells']['seconds_offset']))
        self.end_time = timestamp + datetime.timedelta(seconds=self._seconds)
        self.progress.setMaximum(self._seconds)

    def _setup_ui(self):
        # self
        self.setMaximumHeight(17)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(get_spell_icon(self.spell.spell_icon), 0)
        layout.setSpacing(0)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        if self.spell.type:
            self.progress.setObjectName('SpellWidgetProgressBarGood')
        else:
            self.progress.setObjectName('SpellWidgetProgressBarBad')

        # labels
        progress_layout = QHBoxLayout(self.progress)
        progress_layout.setContentsMargins(5, 0, 5, 0)
        self._name_label = QLabel(self.spell.name.title(), self.progress)
        self._name_label.setObjectName('SpellWidgetNameLabel')
        progress_layout.addWidget(self._name_label)
        progress_layout.insertStretch(2, 1)
        self._time_label = QLabel('', self.progress)
        self._time_label.setObjectName('SpellWidgetTimeLabel')
        progress_layout.addWidget(self._time_label)
        layout.addWidget(self.progress, 1)

    def recast(self, timestamp):
        self._calculate(timestamp)
        self.setProperty('Warning', False)
        self.setStyle(self.style())
        self._time_label.setProperty('Warning', False)
        self._time_label.setStyle(self._time_label.style())

    def _update(self):
        remaining = self.end_time - datetime.datetime.now()
        remaining_seconds = remaining.total_seconds()
        self.progress.setValue(remaining.seconds)
        self.progress.update()
        if remaining_seconds <= 30:
            self.setProperty('Warning', True)
            self.setStyle(self.style())
            self._time_label.setProperty('Warning', True)
            self._time_label.setStyle(self._time_label.style())
        if remaining_seconds <= 0:
            self._remove()
        self._time_label.setText(format_time(remaining))
        QTimer.singleShot(1000, self._update)

    def _remove(self):
        self.setParent(None)
        self.deleteLater()

    def mouseDoubleClickEvent(self, _):
        self._remove()


def get_spell_icon(icon_index):
    # Spell Icons are 40x40 pixels
    file_number = math.ceil(icon_index / 36)
    file_name = 'data/spells/spells0' + str(file_number) + '.png'
    spell_number = icon_index % 36
    file_row = math.floor((spell_number + 6) / 6)
    file_col = spell_number % 6 + 1
    x = (file_col - 1) * 40
    y = (file_row - 1) * 40
    icon_image = QPixmap(file_name)
    scaled_icon_image = icon_image.copy(QRect(x, y, 40, 40)).scaled(
        15, 15, transformMode=Qt.SmoothTransformation)
    label = QLabel()
    label.setPixmap(scaled_icon_image)
    label.setFixedSize(15, 15)
    return label


Spell = namedtuple(
    "Spell",
    "id name pet_location effect_text_you effect_text_other \
    effect_text_worn_off cast_time duration_formula pvp_duration_formula duration pvp_duration type spell_icon")


def create_spell_book():
    """ Returns a dictionary of Spell by k, v -> spell_name, Spell() """
    spell_book = {}
    spellnames = []
    with open('data/spells/spells_us.txt') as spell_file:
        for line in spell_file:
            values = line.strip().split('^')
            spell_book[values[1]] = Spell(
                id=int(values[0]),
                name=values[1].lower(),
                pet_location=values[3],
                effect_text_you=values[6],
                effect_text_other=values[7],
                effect_text_worn_off=values[8],
                cast_time=int(values[13]),
                duration_formula=int(values[16]),
                pvp_duration_formula=int(values[181]),
                duration=int(values[17]),
                pvp_duration=int(values[182]),
                type=int(values[83]),
                spell_icon=int(values[144])
            )
            if [value for value in values[104:119] if value != '255']:
                spellnames.append(values[1])
    print(spell_book['Levitate'])
    spells = [spell_book[name] for name in spellnames]
    spells = [spell for spell in spells if (
        spell.duration != spell.pvp_duration) and spell.type == 1]
    print('\n'.join([str((s.name, s.duration, s.pvp_duration))
                     for s in spells]))
    return spell_book


def get_spell_duration(spell, level):
    if config.data['spells']['use_secondary_all'] or spell.name in config.data['spells']['use_secondary']:
        formula, duration = spell.pvp_duration_formula, spell.pvp_duration
    else:
        formula, duration = spell.duration_formula, spell.duration

    spell_ticks = 0
    if formula == 0:
        spell_ticks = 0
    if formula == 1:
        spell_ticks = int(math.ceil(level / float(2.0)))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 2:
        spell_ticks = int(math.ceil(level / float(5.0) * 3))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 3:
        spell_ticks = int(level * 30)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 4:
        if duration == 0:
            spell_ticks = 50
        else:
            spell_ticks = duration
    if formula == 5:
        spell_ticks = duration
        if spell_ticks == 0:
            spell_ticks = 3
    if formula == 6:
        spell_ticks = int(math.ceil(level / float(2.0)))
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 7:
        spell_ticks = level
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 8:
        spell_ticks = level + 10
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 9:
        spell_ticks = int((level * 2) + 10)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 10:
        spell_ticks = int(level * 3 + 10)
        if spell_ticks > duration:
            spell_ticks = duration
    if formula == 11:
        spell_ticks = duration
    if formula == 12:
        spell_ticks = duration
    if formula == 15:
        spell_ticks = duration
    if formula == 50:
        spell_ticks = 72000
    if formula == 3600:
        if duration == 0:
            spell_ticks = 3600
        else:
            spell_ticks = duration
    return spell_ticks
