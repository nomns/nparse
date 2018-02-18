from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QBoxLayout, QLabel, QFrame

from helpers import config


class ParserWindow(QFrame):

    def __init__(self):
        super().__init__()
        self.name = ''
        self.setObjectName('ParserWindow')
        self.setWindowOpacity(config.data['general']['parser_opacity'] / 100)

        self._create_widgets()
    def set_flags(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinMaxButtonsHint
        )
        # Ensure Qt.WindowStaysOnTopHint works.
        # For some reason it doesn't work all the time when set above.
        # Maybe the below will help as manually toggling the window frame fixes it.
        # 3 times is for toggling frameless on, off, then on.
        self._toggle_frame
        self._toggle_frame
        self._toggle_frame

    def _create_widgets(self):
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self.setLayout(self.content)
        self._menu = QWidget()
        self._menu.setObjectName('ParserWindowMenu')
        self._menu_content = QHBoxLayout()
        self._menu.setLayout(self._menu_content)
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 0, 0, 0)
        self.content.addWidget(self._menu, 0)

        self._title = QLabel()
        self._title.setObjectName("ParserWindowTitle")

        # button = QPushButton(u'\u21F1')
        button = QPushButton(u'\u2637')
        button.setObjectName('ParserButton')
        self._menu_content.addWidget(button, 0)
        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        self.menu_area = QHBoxLayout()
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)

        button.clicked.connect(self._toggle_frame)

    def _toggle_frame(self):
        current_geometry = self.geometry()
        if bool(self.windowFlags() & Qt.FramelessWindowHint):
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            self.setGeometry(current_geometry)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setGeometry(current_geometry)
        self.show()
        g = self.geometry()
        config.data[self.name]['geometry'] = [
            g.x(), g.y(), g.width(), g.height()]
        config.save()

    def set_title(self, title):
        self._title.setText(title)

    def toggle(self, _=None):
        if self.isVisible():
            self.hide()
            config.data[self.name]['toggled'] = False
        else:
            self.show()
            config.data[self.name]['toggled'] = True
        config.save()
    
    def closeEvent(self, _):
        config.data[self.name]['toggled'] = False
        config.save()
