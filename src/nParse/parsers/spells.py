import datetime
import math
import string
import re

from PySide6.QtCore import QEvent, QObject, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QProgressBar,
                             QScrollArea, QSpinBox, QVBoxLayout, QPushButton)

from nParse.helpers.parser import ParserWindow
from nParse.helpers import config, format_time, text_time_to_seconds


class Spells(ParserWindow):
    """Tracks spell casting, duration, and targets by name."""

    def __init__(self):
        self.name = "spells"
        super().__init__()
        QApplication.instance()._signals['settings'].spell_triggers_updated.connect(self.load_custom_timers)
        self._setup_ui()
        self.spell_book, self.text_you, self.text_other = create_spell_book()
        self._custom_timers = {}  # regex : CustomTimer
        self.load_custom_timers()
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
        self._custom_timer_toggle = QPushButton('\u26A1')
        self._custom_timer_toggle.setCheckable(True)
        self._custom_timer_toggle.setToolTip('Parse Custom Timers')
        self._custom_timer_toggle.setChecked(config.data['spells']['use_custom_triggers'])
        self._custom_timer_toggle.clicked.connect(self._toggle_custom_timers)
        self.menu_area.addWidget(self._custom_timer_toggle)
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
                    self._spell_container.add_spell(
                        self._spell_trigger.spell, target[0], target[1])
        self._remove_spell_trigger()

    def parse(self, timestamp, text):
        """Parse casting triggers (casting, failure, success)."""

        # custom timers
        if config.data['spells']['use_custom_triggers']:
            for rx, ct in self._custom_timers.items():
                if rx.match(text):
                    spell = Spell(
                        name=ct.name,
                        duration=int(text_time_to_seconds(ct.time)/6),
                        duration_formula=11,  # honour duration ticks
                        spell_icon=14
                    )
                    self._spell_container.add_spell(
                        spell,
                        timestamp,
                        '__custom__'
                    )

        # There are three main cases:
        # 1) Items that have cast messages like "<item> begins to glow."
        # 2) Items that have no cast message, cast on you (mostly insta-clickies)
        # 3) Items that have no cast message, cast on others
        # Case 1 may require either compiling a list of these items and detecting
        # them as triggers, or else opening it up entirely like this does.
        # Case 2 requires completely opening up detection, but will also detect
        # any other buff cast on you, which may include things you wouldn't expect
        # but can also NOT include many spells (when text is shared with an AoE
        # version). It would also not properly detect level of spell when cast
        # by other people.
        # Case 3 is essentially impossible to deal with.
        if config.data['spells']['use_item_triggers'] and not self._spell_trigger:
            if text in self.text_you:
                spell = self.text_you[text]
                spell_trigger = SpellTrigger(
                    spell=spell,
                    timestamp=timestamp
                )
                spell_trigger.spell_triggered.connect(self._spell_triggered)
                self._spell_trigger = spell_trigger

        if self._spell_trigger:
            self._spell_trigger.parse(timestamp, text)

        # Initial Spell Cast and trigger setup
        if text[:17] == 'You begin casting':
            spell = self.spell_book.get(text[18:-1], None)
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
        elif (self._spell_triggers and
              text[:26] == 'Your spell is interrupted.' or
              text[:20] == 'Your target resisted' or
              text[:29] == 'Your spell did not take hold.' or
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
                for spell_widget in spell_target.spell_widgets():
                    spell_widget.pause()
        elif self._zoning and text[:16] == 'You have entered':
            delay = (timestamp - self._zoning).total_seconds()
            # If zoning took longer than like two minutes, likely false alarm
            if delay > 120:
                self._zoning = None
            else:
                spell_target = self._spell_container.get_spell_target_by_name(
                    '__you__')
                if spell_target:
                    for spell_widget in spell_target.spell_widgets():
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

    def load_custom_timers(self):
        self._custom_timers = {}
        for item in config.data['spells']['custom_timers']:
            ct = CustomTrigger(*item)
            rx = re.compile(
                "^{}$".format(ct.text.replace('*', '.*')),
                re.RegexFlag.IGNORECASE
                )
            self._custom_timers[rx] = ct

    def _toggle_custom_timers(self, _):
        config.data['spells']['use_custom_triggers'] = \
            self._custom_timer_toggle.isChecked()
        config.save()


class SpellContainer(QFrame):

    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self.setObjectName('SpellContainer')
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addStretch(1)

    def add_spell(self, spell, timestamp, target='__you__'):
        spell_target = None
        new = False
        for st in self.findChildren(SpellTarget):
            if st.name == target:
                spell_target = st
        if not spell_target:
            new = True
            spell_target = SpellTarget(target=target)
            self._layout.addWidget(spell_target, 0)

        spell_target.add_spell(spell, timestamp)

        if new:
            for x, widget in enumerate(sorted(self.findChildren(SpellTarget),
                                              key=lambda x: (int(x.target_label.property('TargetType')), x.name))):
                self._layout.insertWidget(x, widget, 0)  # + 1 - skip target label

    def spell_targets(self):
        """Returns a list of all SpellTargets."""
        return self.findChildren(SpellTarget)

    def get_spell_target_by_name(self, name):
        spell_targets = [
            target for target in self.spell_targets() if target.name == name]
        if spell_targets:
            return spell_targets[0]
        return None


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
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.target_label = QLabel(self.title.title())
        self.target_label.setObjectName('SpellTargetLabel')
        self.target_label.setMaximumHeight(20)
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.target_label.mouseDoubleClickEvent = self._remove
        self._layout.addWidget(self.target_label, 0)
        self._layout.addStretch()

    def _remove(self, event=None):
        self.setParent(None)
        self.deleteLater()

    def spell_widgets(self):
        """Returns a list of all SpellWidgets."""
        return self.findChildren(SpellWidget)

    def childEvent(self, event):
        if event.type() == QEvent.Type.ChildRemoved:
            if isinstance(event.child(), SpellWidget):
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
            self._layout.addWidget(SpellWidget(spell, timestamp))
        if self.name in ('__you__', '__custom__'):
            self.target_label.setProperty('TargetType', 0)  # user
        elif not target_type:  # treat target like enemy
            self.target_label.setProperty('TargetType', 2)  # enemy
        else:
            self.target_label.setProperty('TargetType', 1)  # friendly
        self.target_label.setStyle(self.target_label.style())

        now = datetime.datetime.now()
        for x, widget in enumerate(sorted(self.findChildren(SpellWidget), key=lambda x: (x.end_time - now))):
            self._layout.insertWidget(x + 1, widget)  # + 1 - skip target label


class SpellWidget(QFrame):

    def __init__(self, spell, timestamp):
        super().__init__()
        self.setObjectName('SpellWidget')
        self.spell = spell
        self._active = True

        self._setup_ui()
        self._calculate(timestamp)
        self.setProperty('Warning', False)
        self._time_label.setProperty('Warning', False)
        self._update()

    def _calculate(self, timestamp):
        self._ticks = get_spell_duration(
            self.spell, config.data['spells']['level'])
        self._seconds = (int(self._ticks * 6))
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
        self._name_label = QLabel(
            string.capwords(self.spell.name), self.progress)
        self._name_label.setObjectName('SpellWidgetNameLabel')
        progress_layout.addWidget(self._name_label)
        progress_layout.insertStretch(1, 1)
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
        if self._active:
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

    def pause(self):
        self._active = False

    def resume(self):
        self._active = True

    def elongate(self, seconds):
        self.end_time += datetime.timedelta(seconds=seconds)

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
        15, 15, mode=Qt.TransformationMode.SmoothTransformation)
    label = QLabel()
    label.setPixmap(scaled_icon_image)
    label.setFixedSize(15, 15)
    return label


class Spell:

    def __init__(self, **kwargs):
        self.id = 0
        self.name = ''
        self.effect_text_you = ''
        self.effect_text_other = ''
        self.effect_text_worn_off = ''
        self.aoe_range = 0
        self.max_targets = 1
        self.cast_time = 0
        self.resist_type = 0
        self.duration_formula = 0
        self.pvp_duration_formula = 0
        self.duration = 0
        self.pvp_duration = 0
        self.type = 0
        self.spell_icon = 0
        self.__dict__.update(kwargs)


class SpellTrigger(QObject):

    spell_triggered = Signal()

    def __init__(self, **kwargs):
        super().__init__()
        self.timestamp = None  # datetime
        self.spell = None  # Spell
        self.__dict__.update(kwargs)

        self.targets = []  # [(timestamp, target)]
        self.activated = False

        # create casting trigger window
        self._times_up_timer = QTimer()
        self._times_up_timer.setSingleShot(True)
        self._times_up_timer.timeout.connect(self._times_up)
        self._activate_timer = QTimer()
        self._activate_timer.setSingleShot(True)
        self._activate_timer.timeout.connect(self._activate)

        if config.data['spells']['use_casting_window']:
            #  just in case user set casting window buffer super low, create offset for more accuracy.
            msec_offset = (datetime.datetime.now() -
                           self.timestamp).total_seconds() * 1000
            self._times_up_timer.start(
                int(self.spell.cast_time + config.data['spells']['casting_window_buffer'] - msec_offset))
            self._activate_timer.start(
                int(self.spell.cast_time - config.data['spells']['casting_window_buffer'] - msec_offset))
        else:
            self.activated = True

    def parse(self, timestamp, text):
        if self.activated:
            if self.spell.effect_text_you and text[:len(self.spell.effect_text_you)] == self.spell.effect_text_you:
                # cast self
                self.targets.append((timestamp, '__you__'))
            elif text[len(text) - len(self.spell.effect_text_other):] == self.spell.effect_text_other and \
                    len(self.spell.effect_text_other) > 0:
                # cast other
                target = text[:len(text) -
                              len(self.spell.effect_text_other)].strip()
                self.targets.append((timestamp, target))
            if self.targets and self.spell.max_targets == 1:
                self.stop()  # make sure you don't get two triggers
                self.spell_triggered.emit()

    def _times_up(self):
        self.spell_triggered.emit()

    def _activate(self):
        self.activated = True

    def stop(self):
        self._times_up_timer.stop()
        self._activate_timer.stop()


def create_spell_book():
    """ Returns a dictionary of Spell by k, v -> spell_name, Spell() """
    spell_book = {}
    text_lookup_self = {}
    text_lookup_other = {}
    with open('data/spells/spells_us.txt') as spell_file:
        for line in spell_file:
            values = line.strip().split('^')
            spell = Spell(
                id=int(values[0]),
                name=values[1].lower(),
                effect_text_you=values[6],
                effect_text_other=values[7],
                effect_text_worn_off=values[8],
                aoe_range=int(values[10]),
                max_targets=(6 if int(values[10]) > 0 else 1),
                cast_time=int(values[13]),
                resist_type=int(values[85]),
                duration_formula=int(values[16]),
                pvp_duration_formula=int(values[181]),
                duration=int(values[17]),
                pvp_duration=int(values[182]),
                type=int(values[83]),
                spell_icon=int(values[144])
            )
            spell_book[values[1]] = spell
            text_lookup_self[spell.effect_text_you] = spell
            text_lookup_other[spell.effect_text_other] = spell
    return spell_book, text_lookup_self, text_lookup_other


def get_spell_duration(spell, level):
    if spell.name in config.data['spells']['use_secondary']:
        formula, duration = spell.pvp_duration_formula, spell.pvp_duration
    elif config.data['spells']['use_secondary_all'] and spell.type == 0:
        formula, duration = spell.pvp_duration_formula, spell.pvp_duration
    else:
        formula, duration = spell.duration_formula, spell.duration

    spell_ticks = 0
    if formula == 0:
        spell_ticks = 0
    if formula == 1:
        spell_ticks = int(math.ceil(level / float(2.0)))
        spell_ticks = min(spell_ticks, duration)
    if formula == 2:
        spell_ticks = int(math.ceil(level / float(5.0) * 3))
        spell_ticks = min(spell_ticks, duration)
    if formula == 3:
        spell_ticks = int(level * 30)
        spell_ticks = min(spell_ticks, duration)
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
        spell_ticks = min(spell_ticks, duration)
    if formula == 7:
        spell_ticks = level
        spell_ticks = min(spell_ticks, duration)
    if formula == 8:
        spell_ticks = level + 10
        spell_ticks = min(spell_ticks, duration)
    if formula == 9:
        spell_ticks = int((level * 2) + 10)
        spell_ticks = min(spell_ticks, duration)
    if formula == 10:
        spell_ticks = int(level * 3 + 10)
        spell_ticks = min(spell_ticks, duration)
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


class CustomTrigger:

    def __init__(self, name='', text='', time='', **_):
        self.name, self.text, self.time = name, text, time

    def to_list(self):
        return [self.name, self.text, self.time]

    def __str__(self):
        return '{},{},{}'.format(
            self.name, self.text, self.time
        )
