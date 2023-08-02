"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMenu, QMessageBox,
                             QSystemTrayIcon)
import semver

import parsers
from helpers import config, logreader, resource_path, get_version, location_service
from helpers.settings import SettingsWindow

try:
    import pyi_splash  # noqa

    pyi_splash.update_text('Done!')
    pyi_splash.close()
except:  # noqa
    pass

config.load('nparse.config.json')
# validate settings file
config.verify_settings()

os.environ['QT_SCALE_FACTOR'] = str(
    config.data['general']['qt_scale_factor'] / 100)


CURRENT_VERSION = semver.VersionInfo(
    major=0,
    minor=6,
    patch=7,
)
if config.data['general']['update_check']:
    ONLINE_VERSION = get_version()
else:
    ONLINE_VERSION = CURRENT_VERSION


class NomnsParse(QApplication):
    """Application Control."""

    def __init__(self, *args):
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        super().__init__(*args)

        # Updates
        self._toggled = False
        self._log_reader = None

        # Load Parsers
        self._load_parsers()
        self._settings = SettingsWindow()

        # Menu
        menu = QMenu()
        menu.setAttribute(Qt.WA_DeleteOnClose)

        if self.new_version_available():
            new_version_text = "Update Available: {}".format(ONLINE_VERSION)
        else:
            new_version_text = "Version: {}".format(CURRENT_VERSION)

        check_version_action = menu.addAction(new_version_text)
        check_version_action.triggered.connect(self._do_check_version_action)
        menu.addSeparator()
        get_eq_dir_action = menu.addAction('Select EQ Logs Directory')
        get_eq_dir_action.triggered.connect(self._do_get_eq_dir_action)
        menu.addSeparator()

        parser_toggles = set()
        for parser in self._parsers:
            toggle_action = menu.addAction(parser.name.title())
            toggle_action.setCheckable(True)
            toggle_action.setChecked(config.data[parser.name]['toggled'])
            toggle_action.triggered.connect(parser.toggle)
            parser_toggles.add(toggle_action)

        menu.addSeparator()
        settings_action = menu.addAction('Settings')
        settings_action.triggered.connect(self._do_settings_action)
        discord_conf_action = menu.addAction('Configure Discord')
        discord_conf_action.triggered.connect(self._do_discord_conf_action)
        menu.addSeparator()
        quit_action = menu.addAction('Quit')
        quit_action.triggered.connect(self._do_quit_action)

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon(resource_path('data/ui/icon.png')))
        self._system_tray.setToolTip("nParse")
        self._system_tray.setContextMenu(menu)
        self._system_tray.show()

        # Turn On
        self._toggle()

        if self.new_version_available():
            self._system_tray.showMessage(
                "nParse Update",
                "New version available!\n"
                "Current: {}\n"
                "Online: {}".format(
                    CURRENT_VERSION,
                    ONLINE_VERSION
                ),
                msecs=3000
            )

    def _load_parsers(self):
        self._parsers_dict = {
            "maps": parsers.Maps(),
            "spells": parsers.Spells(),
            "discord": parsers.Discord(),
        }
        self._parsers = [
            self._parsers_dict["maps"],
            self._parsers_dict["spells"],
            self._parsers_dict["discord"],
        ]
        for parser in self._parsers:
            if parser.name in config.data.keys() and 'geometry' in config.data[parser.name].keys():
                g = config.data[parser.name]['geometry']
                parser.setGeometry(g[0], g[1], g[2], g[3])
            if config.data[parser.name]['toggled']:
                parser.toggle()

    def _toggle(self):
        if not self._toggled:
            try:
                config.verify_paths()
            except ValueError as error:
                self._system_tray.showMessage(
                    error.args[0], error.args[1], msecs=3000)

            else:
                self._log_reader = logreader.LogReader(
                    config.data['general']['eq_log_dir'])
                self._log_reader.new_line.connect(self._parse)
                self._toggled = True
        else:
            if self._log_reader:
                self._log_reader.deleteLater()
                self._log_reader = None
            location_service.stop_location_service()
            for parser in self._parsers:
                try:
                    parser.shutdown()
                except:
                    print("Failed to shutdown parser: %s" % parser.name)
            self._toggled = False

    def _parse(self, new_line):
        if new_line:
            timestamp, text = new_line  # (datetime, text)
            #  don't send parse to non toggled items, except maps.  always parse maps
            for parser in self._parsers:
                if text.startswith('toggle_clickthrough_%s' % parser.name):
                    config.data[parser.name]['clickthrough'] = (
                        not config.data[parser.name]['clickthrough'])
                    config.save()
                    parser.set_flags()
                elif text.startswith('toggle_%s' % parser.name):
                    parser.toggle()
                elif config.data[parser.name]['toggled'] or parser.name == 'maps':
                    parser.parse(timestamp, text)

    def _do_check_version_action(self):
        webbrowser.open('https://github.com/nomns/nparse/releases')

    def _do_get_eq_dir_action(self):
        dir_path = str(QFileDialog.getExistingDirectory(
            None, 'Select Everquest Logs Directory'))
        if dir_path:
            config.data['general']['eq_log_dir'] = dir_path
            config.save()
            self._toggle()

    def _do_settings_action(self):
        self._settings._set_values()
        if self._settings.exec_():
            # Update required settings
            for parser in self._parsers:
                parser.set_flags()
                parser.settings_updated()
        # some settings are saved within other settings automatically
        # force update
        for parser in self._parsers:
            if parser.name == "spells":
                parser.load_custom_timers()

    def _do_discord_conf_action(self):
        self._parsers_dict["discord"].show_settings()

    def _do_quit_action(self):
        if self._toggled:
            self._toggle()
        else:
            location_service.stop_location_service()

        # save parser geometry
        for parser in self._parsers:
            g = parser.geometry()
            config.data[parser.name]['geometry'] = [
                g.x(), g.y(), g.width(), g.height()
            ]
            config.save()

        self._system_tray.setVisible(False)
        self.quit()

    def new_version_available(self):
        try:
            return ONLINE_VERSION > CURRENT_VERSION
        except:
            return False


if __name__ == "__main__":
    try:
        import ctypes
        APPID = 'nomns.nparse'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    except:
        pass

    APP = NomnsParse(sys.argv)
    APP.setStyleSheet(open(resource_path('data/ui/_.css')).read())
    APP.setWindowIcon(QIcon(resource_path('data/ui/icon.png')))
    APP.setQuitOnLastWindowClosed(False)
    QFontDatabase.addApplicationFont(
        resource_path('data/fonts/NotoSans-Regular.ttf'))
    QFontDatabase.addApplicationFont(
        resource_path('data/fonts/NotoSans-Bold.ttf'))

    sys.exit(APP.exec())
