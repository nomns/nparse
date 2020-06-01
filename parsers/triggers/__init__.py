from PyQt5.QtWidgets import QScrollArea

from config.ui import styles
from utils import sound, text_time_to_seconds, replace_from_regex_groups
from widgets import NDirection, NWindow, NTimer, NContainer, NGroup

from config import trigger_manager, profile
from config.trigger import Trigger, TriggerAction


class Triggers(NWindow):
    def __init__(self, text_parser=None):
        super().__init__(name="triggers")
        self._triggers = trigger_manager.create_parsers(
            choices=profile.trigger_choices, slot=self._triggered
        )
        self._text_parser = text_parser

        # ui
        self.container = NContainer()
        self.setMinimumWidth(150)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self.container)
        self._scroll_area.setObjectName("ScrollArea")

        self.content.addWidget(self._scroll_area, 1)

    def _triggered(
        self, trigger: Trigger, action: TriggerAction, timestamp, re_groups: dict = None
    ) -> None:
        if action.sound.enabled:
            sound.play(
                trigger.package.audio_data.get(action.sound.name, None),
                action.sound.volume,
            )
        if action.timer.enabled:
            group = None
            for g in self.container.groups():
                if g.name == trigger.name:
                    group = g
            if not group:
                group = NGroup(group_name=trigger.name, hide_title=True)
            text = action.timer.text if action.timer.text else trigger.name
            if action.timer.text and re_groups:
                text = replace_from_regex_groups(action.timer.text, re_groups)
            self.container.add_timer(
                group,
                NTimer(
                    name=text,
                    style=styles.trigger(
                        action.timer.bar_color, action.timer.text_color,
                    ),
                    duration=text_time_to_seconds(action.timer.duration),
                    icon=action.timer.icon,
                    timestamp=timestamp,
                    direction=NDirection.DOWN,
                    persistent=action.timer.persistent,
                ),
            )
        if action.text.enabled:
            self._text_parser.display(trigger_text=action.text, re_groups=re_groups)

    def parse(self, timestamp, text):
        for t in self._triggers:
            t.parse(timestamp, text)

    def settings_updated(self):
        super().settings_updated()
        self._triggers = trigger_manager.create_parsers(
            choices=profile.trigger_choices, slot=self._triggered
        )

    def toggle_menu(self, on=True):
        pass  # do not use menu
