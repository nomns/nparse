from PyQt5.QtCore import Qt

from widgets import NWindow

from config.triggers.trigger import TriggerText
from utils import replace_from_regex_groups

from .textview import TextView
from .textitem import TextItem


class Text(NWindow):
    def __init__(self):
        super().__init__(name="text", transparent=True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.container = TextView()
        self.content.addWidget(self.container, 1)

    def display(self, trigger_text: TriggerText = None, re_groups: dict = None):
        # build and display TextItem
        text = trigger_text.text
        if text and re_groups:
            text = replace_from_regex_groups(text, re_groups)
        if text:
            self.container.add(TextItem(text, trigger_text))

    def unlock(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        super().unlock()

    def lock(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        super().lock()

    def settings_updated(self):
        super().settings_updated()
        self.container.clear()
