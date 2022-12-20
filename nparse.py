"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFontDatabase, QIcon
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMenu, QMessageBox,
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
    patch=6,
    build="rc2"
)
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

        # Load Parsers
        self._load_parsers()
        self._settings = SettingsWindow()

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon(resource_path('data/ui/icon.png')))
        self._system_tray.setToolTip("nParse")
        # self._system_tray.setContextMenu(self._create_menu())
        self._system_tray.activated.connect(self._menu)
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

    def _menu(self, event):
        """Returns a new QMenu for system tray."""
        menu = QMenu()
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # check online for new version
        if self.new_version_available():
            new_version_text = "Update Available: {}".format(ONLINE_VERSION)
        else:
            new_version_text = "Version: {}".format(CURRENT_VERSION)

        check_version_action = menu.addAction(new_version_text)
        menu.addSeparator()
        get_eq_dir_action = menu.addAction('Select EQ Logs Directory')
        menu.addSeparator()

        parser_toggles = set()
        for parser in self._parsers:
            toggle = menu.addAction(parser.name.title())
            toggle.setCheckable(True)
            toggle.setChecked(config.data[parser.name]['toggled'])
            parser_toggles.add(toggle)

        menu.addSeparator()
        settings_action = menu.addAction('Settings')
        discord_conf_action = menu.addAction('Configure Discord')
        menu.addSeparator()
        quit_action = menu.addAction('Quit')

        action = menu.exec(QCursor.pos())

        if action == check_version_action:
            webbrowser.open('https://github.com/nomns/nparse/releases')

        elif action == get_eq_dir_action:
            dir_path = str(QFileDialog.getExistingDirectory(
                None, 'Select Everquest Logs Directory'))
            if dir_path:
                config.data['general']['eq_log_dir'] = dir_path
                config.save()
                self._toggle()

        elif action == settings_action:
            self._settings._set_values()
            if self._settings.exec():
                # Update required settings
                for parser in self._parsers:
                    parser.set_flags()
                    parser.settings_updated()
            # some settings are saved within other settings automatically
            # force update
            for parser in self._parsers:
                if parser.name == "spells":
                    parser.load_custom_timers()

        elif action == discord_conf_action:
            self._parsers_dict["discord"].show_settings()

        elif action == quit_action:
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
            config.APP_EXIT = True
            self.quit()

        elif action in parser_toggles:
            parser = [
                parser for parser in self._parsers if parser.name == action.text().lower()][0]
            parser.toggle()

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
