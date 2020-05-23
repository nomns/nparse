from PyQt5.QtWidgets import QScrollArea

from config.ui import styles
from utils import sound, text_time_to_seconds
from widgets import (NDirection, NWindow, NTimer,
                     NContainer, NGroup)


class Triggers(NWindow):

    def __init__(self, text_parser=None):
        super().__init__(name="triggers")
        self._triggers = {}
        self._set_triggers()
        self._text_parser = text_parser

        # ui
        self.container = NContainer()
        self.setMinimumWidth(150)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self.container)
        self._scroll_area.setObjectName('ScrollArea')

        self.content.addWidget(self._scroll_area, 1)

    def _set_triggers(self):
        pass
        # triggers = {}
        # for group_name in config.triggers:
        #     if config.triggers[group_name]['enabled']:
        #         for trigger_name in config.triggers[group_name]['triggers']:
        #             if config.triggers[group_name]['triggers'][trigger_name]['enabled']:
        #                 t = Trigger(
        #                     trigger_name,
        #                     config.triggers[group_name]['triggers'][trigger_name]
        #                 )
        #                 t.triggered.connect(self._triggered)

        #                 triggers[trigger_name] = t
        # self._triggers = triggers

    def _triggered(self, trigger_name, timestamp, re_groups: dict = None) -> None:

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
        if action.text:
            self._text_parser.display(
                text_action=action.text,
                re_groups=re_groups
            )

    def parse(self, timestamp, text):
        for t in self._triggers.values():
            t.parse(timestamp, text)

    def settings_updated(self):
        super().settings_updated()
        self._set_triggers()

    def toggle_menu(self, on=True):
        pass  # do not use menu
