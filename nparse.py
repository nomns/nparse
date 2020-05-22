"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys
import webbrowser
import datetime
from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QSystemTrayIcon)

import parsers
from utils import logreader, resource_path, get_version, logger

from config import app_config, profile_manager
from config.ui import SettingsWindow

# create logger
log = logger.get_logger(__name__)

# load profiles
profile = profile_manager.profile

# set custom user defined scale factor
os.environ['QT_SCALE_FACTOR'] = str(
    app_config.qt_scale_factor / 100)

# update check
CURRENT_VERSION = '0.6.0'
if app_config.update_check:
    ONLINE_VERSION = get_version()
else:
    ONLINE_VERSION = CURRENT_VERSION


class NomnsParse(QApplication):
    """Application Control."""

    def __init__(self, *args):
        super().__init__(*args)

        # Updates
        self._toggled: bool = False
        self._log_reader: logreader.LogReader
        self._locked: bool = True

        # Load UI
        self._load_parsers()
        self._settings: SettingsWindow = SettingsWindow()

        # Tray Icon
        self._system_tray: QSystemTrayIcon = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon(resource_path('data/ui/icon.png')))
        self._system_tray.setToolTip("nParse")
        self._system_tray.activated.connect(self._menu)
        self._system_tray.show()

        # Turn On
        self._toggle()

        # Version Check
        if self.new_version_available():
            self._system_tray.showMessage(
                "nParse Update",
                "New version available!\ncurrent: {}\nonline: {}".format(
                    CURRENT_VERSION,
                    ONLINE_VERSION
                ),
                msecs=3000
            )

    def _load_parsers(self) -> None:
        log.info('loading parsers')
        text_parser = parsers.Text()
        self._parsers = [
            parsers.Maps(),
            parsers.Spells(),
            parsers.Triggers(text_parser=text_parser),
            text_parser
        ]
        for p in self._parsers:
            p.load()

    def _toggle(self) -> None:
        if not self._toggled:
            try:
                app_config.verify_paths()
            except ValueError as error:
                log.warning(error, exc_info=True)
                self._system_tray.showMessage(
                    error.args[0], error.args[1], msecs=3000)

            else:
                self._log_reader = logreader.LogReader(
                    '{}/Logs'.format(app_config.eq_dir))
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
            for parser in [parser for parser
                           in self._parsers
                           if profile.__dict__[parser.name].toggled or parser.name == 'maps'
                           ]:
                parser.parse(timestamp, text)

    def _log_file_changed(self, log_file: str) -> None:
        profile_manager.switch(log_file)

    def _menu(self, event) -> None:
        """Returns a new QMenu for system tray."""
        menu = QMenu()
        menu.setAttribute(Qt.WA_DeleteOnClose)

        menu.addSeparator()

        parser_toggles = set()
        parsers = QMenu('Toggles')
        for parser in self._parsers:
            toggle = parsers.addAction(parser.name.title())
            toggle.setCheckable(True)
            toggle.setCheckable(profile.__dict__[parser.name].toggled)
            parser_toggles.add(toggle)
            parsers.addAction(toggle)

        menu.addMenu(parsers)

        menu.addSeparator()
        settings_action = menu.addAction('Settings')

        lock_toggle = menu.addAction(
            "Unlock Windows" if self._locked else "Lock Windows"
        )

        # check online for new version
        new_version_text = ""
        if self.new_version_available():
            new_version_text = "Update Available {}".format(ONLINE_VERSION)
        else:
            new_version_text = "Version {}".format(CURRENT_VERSION)

        check_version_action = menu.addAction(new_version_text)

        menu.addSeparator()
        quit_action = menu.addAction('Quit')

        action = menu.exec(QCursor.pos())
        if action == check_version_action:
            webbrowser.open('https://github.com/nomns/nparse/releases')

        elif action == settings_action:
            self._settings.set_values()
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

        elif action == quit_action:
            if self._toggled:
                self._toggle()

            # save parser geometry
            for parser in self._parsers:
                g = parser.geometry()
                profile_manager.profile.__dict__[parser.name].geometry = [
                    g.x(), g.y(), g.width(), g.height()
                ]
            app_config.save()
            profile_manager.save()
            self._system_tray.setVisible(False)
            self.quit()

        elif action in parser_toggles:
            parser = [
                parser for parser in self._parsers
                if parser.name == action.text().lower()
            ][0]
            parser.toggle()

        elif action == lock_toggle:
            self._locked = not self._locked
            for parser in self._parsers:
                if self._locked:
                    parser.lock()
                else:
                    parser.unlock()

    def new_version_available(self) -> bool:
        # this will only work if numbers go up
        try:
            for (o, c) in zip(ONLINE_VERSION.split('.'), CURRENT_VERSION.split('.')):
                if int(o) > int(c):
                    return True
        except:
            log.warning(
                f'unable to parse version from: online {o}, current {c}',
                exc_info=True
            )
            return False


if __name__ == "__main__":
    try:
        import ctypes
        APPID = 'nomns.nparse'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    except Exception as error:
        log.error(error, exc_info=True)
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        APP = NomnsParse(sys.argv)
        APP.setWindowIcon(QIcon(resource_path('data/ui/icon.png')))
        APP.setQuitOnLastWindowClosed(False)
        QFontDatabase.addApplicationFont(
            resource_path('data/fonts/NotoSans-Regular.ttf'))
        QFontDatabase.addApplicationFont(
            resource_path('data/fonts/NotoSans-Bold.ttf'))

        sys.exit(APP.exec())
    except Exception as error:
        log.error(error, exc_info=True)
