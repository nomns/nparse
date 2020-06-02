"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys
import webbrowser
import datetime
from typing import Tuple, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFontDatabase, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
    QSpinBox,
    QWidgetAction,
    QLabel,
    QHBoxLayout,
    QWidget,
    QAction,
)

from config import profile, app_config

if app_config.last_profile and os.path.exists(
    os.path.join("data/profiles", f"{app_config.last_profile}.json")
):
    profile.load(app_config.last_profile)
else:
    app_config.last_profile = ""

import parsers
from utils import (
    logreader,
    resource_path,
    get_version,
    logger,
    is_new_version_available,
)

log = logger.get_logger(__name__)

from config.ui import SettingsWindow


# set custom user defined scale factor
os.environ["QT_SCALE_FACTOR"] = str(app_config.qt_scale_factor / 100)

# update check
CURRENT_VERSION: str = "0.6.0"
if app_config.update_check:
    ONLINE_VERSION: str = get_version()
else:
    ONLINE_VERSION = CURRENT_VERSION


class NomnsParse(QApplication):
    """Application Control."""

    def __init__(self, *arg: List[str]) -> None:
        super().__init__(*arg)

        # Updates
        self._toggled: bool = False
        self._log_reader: logreader.LogReader
        self._locked: bool = True

        # Load UI
        self._load_parsers()
        self._settings: SettingsWindow = SettingsWindow()

        # Tray Icon
        self._system_tray: QSystemTrayIcon = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon(resource_path("data/ui/icon.png")))
        self._system_tray.setToolTip("nParse")
        self._system_tray.activated.connect(self._menu)
        self._system_tray.show()

        # Turn On
        self._toggle()

        # Version Check
        if is_new_version_available(ONLINE_VERSION, CURRENT_VERSION):
            self._system_tray.showMessage(
                "nParse Update",
                f"New version available!\ncurrent: {CURRENT_VERSION}\nonline: {ONLINE_VERSION}",
                msecs=3000,
            )

    def _load_parsers(self) -> None:
        text_parser = parsers.Text()
        self._parsers = [
            parsers.Maps(),
            parsers.Spells(),
            parsers.Triggers(text_parser=text_parser),
            text_parser,
        ]
        for p in self._parsers:
            p.load()

    def _toggle(self) -> None:
        if not self._toggled:
            try:
                app_config.verify_paths()
            except ValueError as error:
                log.warning(error, exc_info=True)
                self._system_tray.showMessage(error.args[0], error.args[1], msecs=3000)
            else:
                self._log_reader = logreader.LogReader(
                    "{}/Logs".format(app_config.eq_dir)
                )
                self._log_reader.new_line.connect(self._parse)
                self._log_reader.log_file_change.connect(self._log_file_changed)
                self._toggled = True
        else:
            if self._log_reader:
                self._log_reader.deleteLater()
                self._log_reader = None
            self._toggled = False

    def _parse(self, new_line: Tuple[datetime.datetime, str]) -> None:
        if new_line:
            timestamp, text = new_line  # (datetime, text)
            #  don't send parse to non toggled items, except maps.  always parse maps
            profile.parse(timestamp, text)
            for parser in [
                parser
                for parser in self._parsers
                if profile.__dict__[parser.name].toggled or parser.name == "maps"
            ]:
                parser.parse(timestamp, text)

    def _log_file_changed(self, log_file: str) -> None:
        self._settings.reject()
        profile.switch(os.path.basename(log_file))
        app_config.last_profile = os.path.basename(log_file)
        self.update()

    def update(self):
        for parser in self._parsers:
            parser.settings_updated()

    def lock_toggle(self):
        self.save_geometry()
        self._locked = not self._locked
        for parser in self._parsers:
            if profile.__dict__[parser.name].toggled:
                if self._locked:
                    parser.lock()
                else:
                    parser.unlock()
        profile.save()

    def save_geometry(self):
        for parser in self._parsers:
            g = parser.geometry()
            profile.__dict__[parser.name].geometry = [
                g.x(),
                g.y(),
                g.width(),
                g.height(),
            ]

    def _menu(self, event) -> None:
        """Returns a new QMenu for system tray."""
        menu = QMenu()
        menu.setAttribute(Qt.WA_DeleteOnClose)

        menu.addSeparator()

        parser_toggles = set()
        parsers = QMenu("Toggles")
        for parser in self._parsers:
            toggle: QAction = parsers.addAction(parser.name.title())
            toggle.setCheckable(True)
            toggle.setChecked(profile.__dict__[parser.name].toggled)
            parser_toggles.add(toggle)
            parsers.addAction(toggle)

        menu.addMenu(parsers)

        menu.addSeparator()

        profiles = QMenu(profile.name if profile.name else "Profile")

        level_select = QWidgetAction(profiles)
        w = QWidget()
        layout = QHBoxLayout()
        spinbox = QSpinBox()
        spinbox.setMaximum(65)
        spinbox.setMinimum(1)
        spinbox.setMaximumWidth(100)
        spinbox.setValue(profile.spells.level)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Level"), stretch=1)
        layout.addWidget(spinbox, stretch=0)
        w.setLayout(layout)
        level_select.setDefaultWidget(w)
        profiles.addAction(level_select)

        menu.addMenu(profiles)

        menu.addSeparator()
        settings_action = menu.addAction("Settings")

        lock_toggle = menu.addAction(
            "Unlock Windows" if self._locked else "Lock Windows"
        )

        # check online for new version
        new_version_text = ""
        if is_new_version_available(ONLINE_VERSION, CURRENT_VERSION):
            new_version_text = "Update Available {}".format(ONLINE_VERSION)
        else:
            new_version_text = "Version {}".format(CURRENT_VERSION)

        check_version_action = menu.addAction(new_version_text)

        menu.addSeparator()
        quit_action = menu.addAction("Quit")

        action = menu.exec(QCursor.pos())

        # change level if it was changed
        if spinbox.value() != profile.spells.level:
            profile.spells.level = spinbox.value()

        if action == check_version_action:
            webbrowser.open("https://github.com/nomns/nparse/releases")

        elif action == settings_action:
            if not self._settings.isVisible():
                self._settings.set_values()
                self._settings.setWindowTitle(f"Settings (Profile: {profile.name})")
                if self._settings.exec():
                    self._settings.save_settings()
                    # Update required settings
                    for parser in self._parsers:
                        parser.settings_updated()
                    if self._toggled:
                        self._toggle()
                    self._toggle()
                else:
                    self._settings.set_values()  # revert values
            else:
                self._settings.activateWindow()

        elif action == quit_action:
            if self._toggled:
                self._toggle()

            # save parser geometry
            self.save_geometry()
            app_config.save()
            profile.save()
            self._system_tray.setVisible(False)
            self.quit()

        elif action in parser_toggles:
            if not self._locked:
                self.lock_toggle()
            parser = [
                parser
                for parser in self._parsers
                if parser.name == action.text().lower()
            ][0]
            parser.toggle()

        elif action == lock_toggle:
            self.lock_toggle()


if __name__ == "__main__":
    try:
        import ctypes

        APPID = "nomns.nparse"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    except Exception as error:
        log.error(error, exc_info=True)
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        APP = NomnsParse(sys.argv)
        APP.setWindowIcon(QIcon(resource_path("data/ui/icon.png")))
        APP.setQuitOnLastWindowClosed(False)
        QFontDatabase.addApplicationFont(
            resource_path("data/fonts/NotoSans-Regular.ttf")
        )
        QFontDatabase.addApplicationFont(resource_path("data/fonts/NotoSans-Bold.ttf"))
        sys.exit(APP.exec())
    except Exception as error:
        log.error(error, exc_info=True)
