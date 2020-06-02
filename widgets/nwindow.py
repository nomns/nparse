from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
)

from config import profile

from config.ui import styles

from .nmover import NMover


class NWindow(QFrame):
    def __init__(self, name=None, transparent=True):
        super().__init__()
        self.name = name
        self.setWindowTitle(self.name.title())
        self.transparent = transparent
        self._locked = True
        self._locked_layout = None
        self.setObjectName("NWindow")
        self.setStyleSheet(styles.parser_window())
        if self.transparent:
            self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Base Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        self.setLayout(layout)

        # Mover layout
        self._unlocked_stack = NMover(name=self.name, parent=self)

        # Parser layout in stack
        self._parser_stack = QWidget()
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self._parser_stack.setLayout(self.content)
        self._menu = QWidget()
        self._menu.setObjectName("NWindowMenu")
        self._menu_content = QHBoxLayout()
        self._menu.setLayout(self._menu_content)
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 3, 3, 3)
        self.content.addWidget(self._menu, 0)

        self._title = QLabel()
        self._title.setObjectName("NWindowTitle")

        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        self.menu_area = QHBoxLayout()
        self.menu_area.setContentsMargins(0, 0, 0, 0)
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)
        self._menu.setVisible(False)

        # Add all to stack
        self._stack.addWidget(self._parser_stack)
        self._stack.addWidget(self._unlocked_stack)
        self._stack.setCurrentWidget(self._parser_stack)

    def parse(self, timestamp, text):
        pass

    def set_flags(self):
        self.setFocus()
        self.setWindowFlags(
            Qt.SubWindow
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowCloseButtonHint
            | Qt.WindowMinMaxButtonsHint
        )
        self.show()

    def load(self):
        g = profile.__dict__[self.name].geometry

        if g:
            self.setGeometry(*g)
        # if parser is toggled, make visible and set flags
        if profile.__dict__[self.name].toggled:
            self.set_flags()
            self.show()
        else:
            self.hide()

    def set_title(self, title):
        self._title.setText(title)

    def toggle(self, _=None):
        profile.__dict__[self.name].toggled = not profile.__dict__[self.name].toggled
        if profile.__dict__[self.name].toggled:
            self.set_flags()
            self.show()
        else:
            self.hide()

    def closeEvent(self, _):
        profile.__dict__[self.name].toggled = False

    def enterEvent(self, event):
        if self._locked:
            self.toggle_menu(True)
            self.toggle_transparency(False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._locked:
            self.toggle_menu(False)
            self.toggle_transparency(True)
        super().leaveEvent(event)

    def toggle_transparency(self, on=True):
        if self.transparent:
            if on:
                if self.transparent:
                    self.setAttribute(Qt.WA_NoSystemBackground, True)
                    self.setAttribute(Qt.WA_TranslucentBackground, True)
            else:
                self.setAttribute(Qt.WA_NoSystemBackground, False)
                self.setAutoFillBackground(False)

    def toggle_menu(self, on=True):
        self._menu.setVisible(True) if on else self._menu.setVisible(False)

    def unlock(self):
        self._locked = False
        self.toggle_transparency(False)
        self.set_flags()  # ensure it is ontop
        # swap current layout for move layout
        self._unlocked_stack.show_grip()
        self._stack.setCurrentWidget(self._unlocked_stack)

    def lock(self):
        self._locked = True
        self.toggle_transparency(True)
        self.set_flags()
        # swap to parser stack
        self._unlocked_stack.clear_grip()
        self._stack.setCurrentWidget(self._parser_stack)

    def settings_updated(self):
        self.setStyleSheet(styles.parser_window())
        self.load()
