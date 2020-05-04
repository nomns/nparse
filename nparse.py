"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMenu,
                             QSystemTrayIcon)

import parsers
from helpers import config, logreader, resource_path, get_version
from settings import SettingsWindow

config.load()
# validate settings file
config.verify_settings()

os.environ['QT_SCALE_FACTOR'] = str(
    config.data['general']['qt_scale_factor'] / 100)


CURRENT_VERSION = '0.5.1'
if config.data['general']['update_check']:
    ONLINE_VERSION = get_version()
else:
    ONLINE_VERSION = CURRENT_VERSION


class NomnsParse(QApplication):
    """Application Control."""

    def __init__(self, *args):
        super().__init__(*args)

        # Updates
        self._toggled = False
        self._log_reader = None
        self._locked = True

        # Load UI
        self._load_parsers()
        self._settings = SettingsWindow()

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
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

        # TESTING
        # self._settings.set_values()
        # self._settings.exec()

    def _load_parsers(self):
        text_parser  = parsers.Text()
        self._parsers = [
            parsers.Maps(),
            parsers.Spells(),
            parsers.Triggers(text_parser=text_parser),
            text_parser
        ]
        for p in self._parsers:
            p.load()

    def _toggle(self):
        if not self._toggled:
            try:
                config.verify_paths()
            except ValueError as error:
                self._system_tray.showMessage(
                    error.args[0], error.args[1], msecs=3000)

            else:
                self._log_reader = logreader.LogReader(
                    '{}/Logs'.format(config.data['general']['eq_dir']))
                self._log_reader.new_line.connect(self._parse)
                self._toggled = True
        else:
            if self._log_reader:
                self._log_reader.deleteLater()
                self._log_reader = None
            self._toggled = False

    def _parse(self, new_line):
        if new_line:
            timestamp, text = new_line  # (datetime, text)
            #  don't send parse to non toggled items, except maps.  always parse maps
            for parser in [parser for parser in self._parsers if config.data[parser.name]['toggled'] or parser.name == 'maps']:
                parser.parse(timestamp, text)

    def _menu(self, event):
        """Returns a new QMenu for system tray."""
        menu = QMenu()
        menu.setAttribute(Qt.WA_DeleteOnClose)

        # check online for new version
        new_version_text = ""
        if self.new_version_available():
            new_version_text = "Update Available {}".format(ONLINE_VERSION)
        else:
            new_version_text = "Version {}".format(CURRENT_VERSION)

        check_version_action = menu.addAction(new_version_text)
        menu.addSeparator()

        lock_toggle = menu.addAction("Unlock Windows" if self._locked else "Lock Windows")
        menu.addSeparator()

        parser_toggles = set()
        for parser in self._parsers:
            toggle = menu.addAction(parser.name.title())
            toggle.setCheckable(True)
            toggle.setChecked(config.data[parser.name]['toggled'])
            parser_toggles.add(toggle)

        menu.addSeparator()
        settings_action = menu.addAction('Settings')
        menu.addSeparator()
        quit_action = menu.addAction('Quit')

        action = menu.exec_(QCursor.pos())

        if action == check_version_action:
            webbrowser.open('https://github.com/nomns/nparse/releases')

        elif action == settings_action:
            self._settings.set_values()
            if self._settings.exec_():
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
                config.data[parser.name]['geometry'] = [
                    g.x(), g.y(), g.width(), g.height()
                ]
                config.save()

            self._system_tray.setVisible(False)
            self.quit()

        elif action in parser_toggles:
            parser = [
                parser for parser in self._parsers if parser.name == action.text().lower()][0]
            parser.toggle()

        elif action == lock_toggle:
            self._locked = not self._locked
            for parser in self._parsers:
                if self._locked:
                    parser.lock()
                else:
                    parser.unlock()

    def new_version_available(self):
        # this will only work if numbers go up
        try:
            for (o, c) in zip(ONLINE_VERSION.split('.'), CURRENT_VERSION.split('.')):
                if int(o) > int(c):
                    return True
        except:
            return False


if __name__ == "__main__":
    try:
        import ctypes
        APPID = 'nomns.nparse'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    except:
        pass

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    APP = NomnsParse(sys.argv)
    APP.setWindowIcon(QIcon(resource_path('data/ui/icon.png')))
    APP.setQuitOnLastWindowClosed(False)
    QFontDatabase.addApplicationFont(
        resource_path('data/fonts/NotoSans-Regular.ttf'))
    QFontDatabase.addApplicationFont(
        resource_path('data/fonts/NotoSans-Bold.ttf'))

    sys.exit(APP.exec())
