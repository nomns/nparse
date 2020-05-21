import datetime

from PyQt5.QtCore import pyqtSignal, QObject

from utils import create_regex_from


class Trigger(QObject):

    triggered = pyqtSignal(str, datetime.datetime, dict)

    def __init__(self, trigger_name, trigger_json):
        super().__init__()
        self.name = trigger_name
        self.action = Action(
            sound=trigger_json['action'].get('sound', None),
            text=trigger_json['action'].get('text', None),
            timer=trigger_json['action'].get('timer', None)
        )
        self.trigger = create_regex_from(
            text=trigger_json['trigger'].get('text', None),
            regex=trigger_json['trigger'].get('regex', None)
        )

    def parse(self, timestamp, text):
        results = self.trigger.search(text)
        if results:
            re_groups = results.groupdict({})
            self.triggered.emit(self.name, timestamp, re_groups)


class Action:

    def __init__(self, **kwargs):
        self.sound = {}
        self.timer = {}
        self.text = {}
        self.__dict__.update(kwargs)
