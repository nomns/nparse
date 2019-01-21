from helpers import config
from widgets.parser import ParserWindow
from widgets.ntimer import NTimer


class Triggers(ParserWindow):

    def __init__(self):
        super().__init__()
        self.name = "triggers"

    def parse(self, timestamp, text):
        pass

    # pass on regular parser procedures
    def set_flags(self):
        pass

    def set_geometry(self, *args):
        pass

    def set_title(self):
        pass

    def settings_updated(self):
        pass
