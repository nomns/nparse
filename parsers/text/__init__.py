from PyQt5.QtCore import Qt

from widgets import NWindow

from .common import TextAction
from .textview import TextView
from .textitem import TextItem


class Text(NWindow):

    def __init__(self):
        super().__init__(name='text', transparent=True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.container = TextView()
        self.content.addWidget(self.container, 1)

    def display(self, text_action: dict = None, re_groups: dict = None):
        # build and display TextItem
        text = text_action.get('text', None)
        if text:
            if re_groups:
                for k in re_groups:
                    v = re_groups.get(k, '')
                    v = v if v else ''
                    text = text.replace('<{}>'.format(k), v)
            action = TextAction(
                color=text_action.get('color', [0, 0, 0, 255]),
                text=text,
                text_size=text_action.get('text_size', 15)
            )
            self.container.add(TextItem(action))

    def unlock(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        super().unlock()

    def lock(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        super().lock()

    def settings_updated(self):
        self.container.clear()
