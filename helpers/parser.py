from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QStyle,
                             QPushButton, QVBoxLayout, QWidget)

from helpers import config


class ParserWindow(QFrame):
    autohide = True
    always_on_top = True

    def __init__(self):
        super().__init__()
        self.name = ''
        self.setObjectName('ParserWindow')
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self.setLayout(self.content)
        self._menu = QWidget()
        self._menu_content = QHBoxLayout()
        self._menu.setObjectName('ParserWindowMenuReal')
        self._menu.setLayout(self._menu_content)
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 0, 0, 0)
        self.content.addWidget(self._menu, 0)

        self._title = QLabel()
        self._title.setObjectName('ParserWindowTitle')

        button = QPushButton('\u2637')
        button.setObjectName('ParserWindowMoveButton')
        self._menu_content.addWidget(button, 0)
        self._menu_content.addWidget(self._title, 1)

        menu_area = QWidget()
        menu_area.setObjectName('ParserWindowMenu')
        self.menu_area = QHBoxLayout()
        menu_area.setLayout(self.menu_area)
        self._menu_content.addWidget(menu_area, 0)
        self._menu.setVisible(False)

        button.clicked.connect(self._toggle_frame)

    def update_background_color(self):
        pass

    def update_window_opacity(self):
        self.setWindowOpacity(config.data[self.name]['opacity'] / 100)

    def set_flags(self):
        flags = Qt.WindowType.FramelessWindowHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        flags |= Qt.WindowType.WindowMinMaxButtonsHint
        if config.data[self.name]['always_on_top']:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        if config.data[self.name]['clickthrough']:
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)

    def _toggle_frame(self):
        current_geometry = self.geometry()
        window_flush = config.data['general']['window_flush']
        titlebar_height = self.style().pixelMetric(QStyle.PixelMetric.PM_TitleBarHeight)
        titlebar_margin = self.style().pixelMetric(QStyle.PixelMetric.PM_DockWidgetTitleMargin)
        tb_total_height = titlebar_height + titlebar_margin
        if bool(self.windowFlags() & Qt.WindowType.FramelessWindowHint):
            if window_flush:
                current_geometry.setTop(current_geometry.top() + tb_total_height)
            flags = Qt.WindowType.WindowCloseButtonHint
            flags |= Qt.WindowType.WindowMinMaxButtonsHint
            self.setWindowFlags(flags)
            self.setGeometry(current_geometry)
            self.show()
        else:
            if window_flush:
                current_geometry.setTop(current_geometry.top() - tb_total_height)
            flags = Qt.WindowType.FramelessWindowHint
            if config.data[self.name]['always_on_top']:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.setGeometry(current_geometry)
            self.show()
            config.data[self.name]['geometry'] = [
                current_geometry.x(), current_geometry.y(),
                current_geometry.width(), current_geometry.height()
            ]
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
        if config.APP_EXIT:
            return
        if not bool(self.windowFlags() & Qt.WindowType.FramelessWindowHint):
            # Preserve correct position/height when closing
            titlebar_height = self.style().pixelMetric(QStyle.PixelMetric.PM_TitleBarHeight)
            titlebar_margin = self.style().pixelMetric(QStyle.PixelMetric.PM_DockWidgetTitleMargin)
            tb_total_height = titlebar_height + titlebar_margin
            current_geometry = self.geometry()
            current_geometry.setTop(max(current_geometry.top() - tb_total_height, 0))
            config.data[self.name]['geometry'] = [
                current_geometry.x(), current_geometry.y(),
                current_geometry.width(), current_geometry.height()]
            self.setGeometry(current_geometry)
        config.data[self.name]['toggled'] = False
        config.save()

    def enterEvent(self, event):
        if config.data.get(self.name, ()).get('auto_hide_menu', False):
            self._menu.setVisible(True)
            QFrame.enterEvent(self, event)

    def leaveEvent(self, event):
        if config.data.get(self.name, ()).get('auto_hide_menu', False):
            self._menu.setVisible(False)
            QFrame.leaveEvent(self, event)

    def shutdown(self):
        pass

    def settings_updated(self):
        pass
