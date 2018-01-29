"""NomnsParse: Parsing tools for Project 1999."""
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QApplication, QMenu, QFileDialog)

from helpers import config, logreader, parse_line, resource_path
import parsers

config.load('nparse.config.yaml')


class NomnsParse(QApplication):
    """Application Control."""

    def __init__(self, *args):
        super().__init__(*args)

        # Updater/Ticks
        self._toggled = False
        self._toggled_menu_item = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._parse)
        self._thread = None

        # Load Parsers
        self._load_parsers()

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon(resource_path('data/ui/icon.png')))
        self._system_tray.setToolTip("Nomns' Parser")
        self._system_tray.setContextMenu(self._create_menu())
        self._system_tray.show()

        # Turn On
        self._toggle(1)

    def _load_parsers(self):
        self._parsers = [
            parsers.Maps()
        ]
        for parser in self._parsers:
            if parser.name in config.data.keys() and 'geometry' in config.data[parser.name].keys():
                g = config.data[parser.name]['geometry']
                parser.setGeometry(g[0], g[1], g[2], g[3])
            if config.data[parser.name]['toggled']:
                parser.show()

    def _toggle(self, toggle=1):
        if toggle and not self._toggled:
            try:
                config.verify_settings()
            except ValueError as error:
                self._system_tray.showMessage(error.args[0], error.args[1], msecs=3000)

            else:
                self._thread = logreader.ThreadedLogReader(
                    config.data['general']['eq_log_dir'],
                    config.data['general']['update_interval']
                )
                self._thread.start()
                self._timer.start(
                    1000 * config.data['general']['update_interval']
                )
                self._toggled = True
                self._toggled_menu_item.setChecked(True)
        else:
            if self._thread:
                self._timer.stop()
                self._thread.stop()
                self._thread.join()
            self._toggled = False
            self._toggled_menu_item.setChecked(False)

    def _parse(self):
        for line in self._thread.get_new_lines():
            if line:
                date, text = parse_line(line)
                for parser in self._parsers:
                    parser.parse(date, text)

    def _create_menu(self):
        """Returns a new QMenu for system tray."""
        menu = QMenu()
        nparse_toggle = menu.addAction('Toggle nParse')
        nparse_toggle.setCheckable(True)
        if self._toggled:
            nparse_toggle.setChecked(True)
        nparse_toggle.triggered.connect(self._toggle)
        self._toggled_menu_item = nparse_toggle
        seperator = menu.addSeparator()
        get_eq_dir = menu.addAction("Select EQ Logs Directory")
        get_eq_dir.triggered.connect(self._get_eq_directory)
        # generate parser specific sub menus
        for parser in self._parsers:
            parser_menu = menu.addMenu(parser.name.title())
            show_action = parser_menu.addAction("Toggle")
            show_action.triggered.connect(parser.toggle)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)
        return menu

    def _get_eq_directory(self, _):
        dir_path = str(QFileDialog.getExistingDirectory(None, 'Select Everquest Logs Directory'))
        if dir_path:
            config.data['general']['eq_log_dir'] = dir_path
            config.save()
            self._toggle(0)
            self._toggle(1)

    def _quit(self):
        for parser in self._parsers:
            g = parser.geometry()
            config.data[parser.name]['geometry'] = [
                g.x(), g.y(), g.width(), g.height()]
        config.save()
        self._toggle(0)
        self._system_tray.setVisible(False)
        self.quit()


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
    QFontDatabase.addApplicationFont(resource_path('data/fonts/NotoSans-Regular.ttf'))
    QFontDatabase.addApplicationFont(resource_path('data/fonts/NotoSans-Bold.ttf'))

    sys.exit(APP.exec())
