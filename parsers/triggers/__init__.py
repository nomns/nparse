from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtCore import Qt

from settings import styles
from helpers import config, sound, text_time_to_seconds
from widgets import NDirection
from widgets.nwindow import NWindow
from widgets.ntimer import NTimer
from widgets.ncontainers import NContainer, NGroup

from .trigger import Trigger


class Triggers(NWindow):

    def __init__(self):
        super().__init__()
        self.name = "triggers"
        self.set_title(self.name.title())
        self._triggers = {}
        self._set_triggers()

        # ui
        self.container = NContainer()
        self.setMinimumWidth(150)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self.container)
        self._scroll_area.setObjectName('ScrollArea')

        self.content.addWidget(self._scroll_area, 1)

    def _set_triggers(self):
        triggers = {}
        for group_name in config.triggers:
            if config.triggers[group_name]['enabled']:
                for trigger_name in config.triggers[group_name]['triggers']:
                    if config.triggers[group_name]['triggers'][trigger_name]['enabled']:
                        t = Trigger(
                            trigger_name,
                            config.triggers[group_name]['triggers'][trigger_name]
                        )
                        t.triggered.connect(self._triggered)

                        triggers[trigger_name] = t
        self._triggers = triggers

    def _triggered(self, trigger_name, timestamp):
        print('Triggered: {}'.format(trigger_name))

        action = self._triggers[trigger_name].action
        if action.sound:
            sound.play(action.sound)
        if action.timer:
            group_name = trigger_name
            group = None
            for g in self.container.groups():
                if g.name == group_name:
                    group = g
            if not group:
                group = NGroup(
                    group_name=group_name,
                    hide_title=True
                )
            self.container.add_timer(
                group,
                NTimer(
                    trigger_name,
                    style=styles.trigger(
                        action.timer['bar_color'],
                        action.timer['text_color']
                    ),
                    duration=text_time_to_seconds(
                        action.timer['time']
                    ),
                    icon=action.timer['icon'],
                    timestamp=timestamp,
                    direction=NDirection.DOWN
                )
            )

    def parse(self, timestamp, text):
        for t in self._triggers.values():
            t.parse(timestamp, text)

    def settings_updated(self):
        super().settings_updated()
        self._set_triggers()
