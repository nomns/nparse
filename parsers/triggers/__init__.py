from PyQt5.QtCore import Qt

from helpers import config
from widgets.parser import ParserWindow
from widgets.ntimer import NTimer
from parsers import Spells


class Triggers(ParserWindow):

    def __init__(self, spells_parser: Spells):
        super().__init__()
        self.name = "triggers"
        self.set_title(self.name.title())
        self.setVisible(False)  # do not show Window
        self._triggers = self._get_triggers()

    def _get_triggers(self):
        print(config.triggers)
        triggers = {}
        for group_name in config.triggers.keys():
            group = {
                'enabled': config.triggers[group_name]['enabled'],
                'triggers': []
            }





        return triggers



    def parse(self, timestamp, text):
        print(timestamp, text)

    # pass on regular parser procedures

    def settings_updated(self):
        self._get_triggers()
