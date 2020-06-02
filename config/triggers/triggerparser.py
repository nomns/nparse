import datetime

from PyQt5.QtCore import pyqtSignal, QObject, QTimer

from .trigger import Trigger, TriggerAction
from utils import create_regex_from, text_time_to_seconds


class TriggerParser(QObject):

    triggered = pyqtSignal(Trigger, TriggerAction, datetime.datetime, dict)

    def __init__(self, trigger: Trigger):
        super().__init__()
        self.trigger = trigger
        self.regex = create_regex_from(text=trigger.text, regex=trigger.regex)
        self.groups = {}

    def parse(self, timestamp, text):
        results = self.regex.search(text)
        if results:
            self.groups = results.groupdict({})
            self.triggered.emit(
                self.trigger, self.trigger.start_action, timestamp, self.groups
            )
            end_action = self.trigger.end_action
            if any(
                [
                    end_action.text.enabled,
                    end_action.timer.enabled,
                    end_action.sound.enabled,
                ]
            ):
                QTimer.singleShot(
                    text_time_to_seconds(self.trigger.duration) * 1000,
                    self.trigger_end_action,
                )

    def trigger_end_action(self):
        self.triggered.emit(
            self.trigger, self.trigger.end_action, datetime.datetime.now(), self.groups
        )
