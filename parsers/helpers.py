from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QBoxLayout, QLabel


class ParserWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.FramelessWindowHint |
            Qt.WindowMinMaxButtonsHint
        )
        self.setWindowOpacity(0.85)

        self._create_widgets()

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

        button = QPushButton(u'\u2630')
        button.setIconSize(QSize(40, 40))
        button.setObjectName('ParserButton')
        self._menu_content.addWidget(button, 0)
        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        self.menu_area = QHBoxLayout()
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)

        button.clicked.connect(self._toggle_frame)

    def _toggle_frame(self):
        if bool(self.windowFlags() & Qt.FramelessWindowHint):
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.show()

    def set_title(self, title):
        self._title.setText(title)
