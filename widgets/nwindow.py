from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)
from PyQt5.QtGui import QPainter, QPixmap, QBrush, QPen

from helpers import config
from settings import styles


class NWindow(QFrame):

    def __init__(self, transparent=True):
        super().__init__()
        self.name = ''
        self.transparent = transparent
        self.setObjectName('NWindow')
        self.setStyleSheet(styles.parser_window())
        if self.transparent:
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self.setLayout(self.content)
        self._menu = QWidget()
        self._menu.setObjectName('NWindowMenu')
        self._menu_content = QHBoxLayout()
        self._menu.setLayout(self._menu_content)
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 3, 3, 3)
        self.content.addWidget(self._menu, 0)

        self._title = QLabel()
        self._title.setObjectName('NWindowTitle')

        button = QPushButton(u'\u2637')
        button.setObjectName('NWindowMoveButton')
        self._menu_content.addWidget(button, 0)
        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        self.menu_area = QHBoxLayout()
        self.menu_area.setContentsMargins(0, 0, 0, 0)
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)
        self._menu.setVisible(False)

        button.clicked.connect(self._toggle_frame)

    def set_flags(self):
        self.setFocus()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        self.show()

    def load(self):
        g = config.data.get(self.name, {}).get('geometry', None)

        if g:
            self.setGeometry(g[0], g[1], g[2], g[3])
        # if parser is toggled, make visible and set flags
        if config.data.get(self.name, {}).get('toggled', False):
            self.set_flags()
            self.show()
        else:
            self.hide()

    def _toggle_frame(self):
        current_geometry = self.geometry()
        if bool(self.windowFlags() & Qt.FramelessWindowHint):
            self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
            self.setGeometry(current_geometry)
            self.show()
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setGeometry(current_geometry)
            self.show()

    def set_title(self, title):
        self.setWindowTitle(title)
        self._title.setText(title)

    def toggle(self, _=None):
        toggled = not config.data[self.name]['toggled']
        config.data[self.name]['toggled'] = toggled
        config.save()
        if toggled:
            self.set_flags()
            self.show()
        else:
            self.hide()

    def closeEvent(self, _):
        config.data[self.name]['toggled'] = False
        config.save()

    def enterEvent(self, event):
        self._menu.setVisible(True)
        if self.transparent:
            self.setAttribute(Qt.WA_NoSystemBackground, False)
            self.setAutoFillBackground(False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._menu.setVisible(False)
        if self.transparent:
            self.setAttribute(Qt.WA_NoSystemBackground, True)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        super().leaveEvent(event)

    def settings_updated(self):
        self.setStyleSheet(styles.parser_window())
