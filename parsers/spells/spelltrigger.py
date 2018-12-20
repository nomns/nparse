import datetime

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from helpers import config


class SpellTrigger(QObject):

    spell_triggered = pyqtSignal()

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
                self.spell.cast_time + config.data['spells']['casting_window_buffer'] - msec_offset)
            self._activate_timer.start(
                self.spell.cast_time - config.data['spells']['casting_window_buffer'] - msec_offset)
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
