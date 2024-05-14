from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QStyle,
    QPushButton, QVBoxLayout, QWidget)

from nParse.helpers import config


class ParserWindow(QWidget):
    content = None
    menu_area = None
    name = None

    _always_on_top = True
    _auto_hide_menu = True
    _button = None
    _clickthrough = False
    _frameless = True
    _geometry = None
    _menu = None
    _menu_content = None
    _parser_menu_area = None
    _title = None
    _toggled = False
    _window_flush = None
    _window_opacity = 80

    def __init__(self, **kwargs):
        if not self.name:
            self.name = kwargs.get("name", None)
            if not self.name:
                raise AttributeError(
                    "'name' is a required attribute that must be set via **kwargs or in the partent class."
                )
        super().__init__()

        # Set vars from config
        self._always_on_top = config.data.get(self.name, {}).get("always_on_top", True)
        self._auto_hide_menu = config.data.get(self.name, {}).get("auto_hide_menu", True)
        self._clickthrough = config.data.get(self.name, {}).get("clickthrough", True)
        self._frameless = config.data.get(self.name, {}).get("frameless", True)
        self._geometry = config.data.get(self.name, {}).get("geometry", [0,0,200,400])
        self._toggled = config.data.get(self.name, {}).get("toggled", True)
        self._window_flush = config.data.get("general", {}).get("window_flush", True)
        self._window_opacity = config.data.get(self.name, {}).get("opacity", 80)

        # Setup UI
        self._button = QPushButton("\u2637")
        self._button.setObjectName("ParserWindowMoveButton")
        self._button.clicked.connect(self._toggle_frame)

        self._title = QLabel()
        self._title.setText(self.name.title())
        self._title.setObjectName("ParserWindowTitle")

        self.menu_area = QHBoxLayout()

        self._parser_menu_area = QWidget()
        self._parser_menu_area.setObjectName("ParserWindowMenu")
        self._parser_menu_area.setLayout(self.menu_area)

        self._menu_content = QHBoxLayout()
        self._menu_content.setSpacing(5)
        self._menu_content.setContentsMargins(3, 0, 0, 0)
        self._menu_content.addWidget(self._button, 0)
        self._menu_content.addWidget(self._title, 1)
        self._menu_content.addWidget(self._parser_menu_area, 0)

        self._menu = QWidget()
        self._menu.setObjectName("ParserWindowMenuReal")
        self._menu.setLayout(self._menu_content)
        self._menu.setVisible(False)

        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)
        self.content.addWidget(self._menu, 0)

        if self._auto_hide_menu == False:
            self._menu.setVisible(True)

        self.setGeometry(self._geometry[0], self._geometry[1], self._geometry[2], self._geometry[3])
        self.setLayout(self.content)
        self.setObjectName("ParserWindow")
        self.setWindowOpacity(self._window_opacity / 100)
        self.setWindowTitle(self.name.title())

        self._set_flags()

        QApplication.instance()._signals["settings"].config_updated.connect(
            self._parser_settings_config_update_watcher
        )
        QApplication.instance().aboutToQuit.connect(self._save_geometry)
        if self._toggled:
            self.show()

    def _parser_settings_config_update_watcher(self):
        requies_redraw = False

        settings_always_on_top = config.data.get(self.name, {}).get("always_on_top", True)
        settings_auto_hide_menu = config.data.get(self.name, {}).get("auto_hide_menu", True)
        settings_clickthrough = config.data.get(self.name, {}).get("clickthrough", True)
        settings_window_flush = config.data.get("general", {}).get("window_flush", True)
        settings_window_opacity = config.data.get(self.name, {}).get("opacity", 80)

        self._window_flush = settings_window_flush

        if self._clickthrough != settings_clickthrough:
            if self.isVisible():
                requies_redraw = True
            self._clickthrough = settings_clickthrough
            self._set_flags()

        if self._window_opacity != settings_window_opacity:
            self._window_opacity = settings_window_opacity
            self.setWindowOpacity(self._window_opacity / 100)

        if self._always_on_top != settings_always_on_top:
            if self.isVisible():
                requies_redraw = True
            self._always_on_top = settings_always_on_top
            self._set_flags()

        if self._auto_hide_menu != settings_auto_hide_menu:
            self._auto_hide_menu = settings_auto_hide_menu
            self._menu.setVisible(not settings_auto_hide_menu)

        if requies_redraw:
            self.show()

    def _save_geometry(self):
        config.data[self.name]['geometry'] = [
            self.geometry().x(), self.geometry().y(),
            self.geometry().width(), self.geometry().height()
        ]
        config.save()

    def _set_flags(self):
        if self._frameless:
            flags = Qt.WindowType.FramelessWindowHint
        else:
            flags = Qt.WindowType.WindowCloseButtonHint
            flags |= Qt.WindowType.WindowMinMaxButtonsHint
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        if self._clickthrough:
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)

    def _toggle_frame(self):
        current_geometry = self.geometry()
        titlebar_height = self.style().pixelMetric(QStyle.PixelMetric.PM_TitleBarHeight)
        titlebar_margin = self.style().pixelMetric(QStyle.PixelMetric.PM_DockWidgetTitleMargin)
        tb_total_height = titlebar_height + titlebar_margin
        if self._frameless:
            if self._window_flush:
                current_geometry.setTop(current_geometry.top() + tb_total_height)
            self.setGeometry(current_geometry)
            self._frameless = False
            self._set_flags()
            self.show()
            config.data[self.name]["frameless"] = False
            config.data[self.name]['geometry'] = [
                current_geometry.x(), current_geometry.y(),
                current_geometry.width(), current_geometry.height()
            ]
            config.save()
        else:
            if self._window_flush:
                current_geometry.setTop(current_geometry.top() - tb_total_height)
            self.setGeometry(current_geometry)
            self._frameless = True
            self._set_flags()
            self.show()
            config.data[self.name]["frameless"] = True
            config.data[self.name]['geometry'] = [
                current_geometry.x(), current_geometry.y(),
                current_geometry.width(), current_geometry.height()
            ]
            config.save()

    def toggle(self):
        if self.isVisible():
            self.hide()
            config.data[self.name]['toggled'] = False
        else:
            self.show()
            config.data[self.name]['toggled'] = True
        config.save()

    # Overrides QWidget to handle this event
    def closeEvent(self, _):
        if config.APP_EXIT:
            return
        # This is triggered if the user closes from the taskbar or from the X if the window is framed
        config.data[self.name]['toggled'] = False
        config.save()

    # Overrides QWidget to handle this event
    def enterEvent(self, _):
        if self._auto_hide_menu:
            self._menu.setVisible(True)

    # Overrides QWidget to handle this event
    def leaveEvent(self, _):
        if self._auto_hide_menu:
            self._menu.setVisible(False)