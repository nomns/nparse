import os
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QSystemTrayIcon
import semver

from nParse.helpers import config, logreader, resource_path, get_version
from nParse.helpers.settings import SettingsWindow, SettingsSignals
from nParse.helpers.logreader import LogReaderSignals
from nParse.helpers.location_service import LocationSharingService, LocationSharingSignals
from nParse.parsers.discord import Discord
from nParse.parsers.maps import Maps
from nParse.parsers.maps.window import MapsSignals
from nParse.parsers.spells import Spells

config.load('nparse.config.json')
# validate settings file
config.verify_settings()

CURRENT_VERSION = semver.VersionInfo(
    major=0,
    minor=7,
    patch=0,
    build=""
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

        # Load Signals
        self._signals = {}
        self._signals["logreader"] = LogReaderSignals()
        self._signals["settings"] = SettingsSignals()
        self._signals["maps"] = MapsSignals()
        self._signals["locationsharing"] = LocationSharingSignals()

        # Load Services
        self._services = {}
        self._services["locationsharing"] = LocationSharingService()

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
            "maps": Maps(),
            "spells": Spells(),
            "discord": Discord(),
        }
        self._parsers = [
            self._parsers_dict["maps"],
            self._parsers_dict["spells"],
            self._parsers_dict["discord"],
        ]

    def _toggle(self):
        if not self._toggled:
            try:
                config.verify_paths()
            except ValueError as error:
                self._system_tray.showMessage(
                    error.args[0], error.args[1], msecs=3000)

            else:
                self._log_reader = logreader.LogReader(
                    os.path.abspath(config.data['general']['eq_log_dir']))
                QApplication.instance()._signals["logreader"].new_line.connect(self._parse)
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
            for parser in self._parsers:
                if text.startswith('toggle_clickthrough_%s' % parser.name):
                    config.data[parser.name]['clickthrough'] = (
                        not config.data[parser.name]['clickthrough'])
                    config.save()
                    parser._set_flags()
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
            self._settings.exec()

        elif action == discord_conf_action:
            self._parsers_dict["discord"].show_settings()

        elif action == quit_action:
            if self._toggled:
                self._toggle()

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