import sys
import ctypes
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QSystemTrayIcon, QApplication, QMenu, QAction, QActionGroup)

from helpers import config, logreader, parse_line
import parsers
config.load('data/config.yaml')

import traceback


class NomnsParse(QApplication):

    def __init__(self, *args):
        QApplication.__init__(self, *args)

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon('data/ui/icon.png'))
        self._system_tray.setToolTip("Nomns' Parser")
        self._system_tray.show()
        self._system_tray.setContextMenu(self._create_menu())

        # Updater/Ticks
        self._timer = QTimer()
        self._timer.timeout.connect(self._parse)
        self._thread = None

        # Load Parsers
        self._load_parsers()

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
            parser.show()

    def _toggle(self, toggle):
        if toggle and config.verify_settings():
            self._thread = logreader.ThreadedLogReader(
                config.data['general']['everquest_directory'],
                config.data['general']['update_interval']
            )
            self._thread.start()
            self._timer.start(
                1000 * config.data['general']['update_interval']
            )
        else:
            if self._thread:
                self._timer.stop()
                self._thread.stop()
                self._thread.join()

    def _parse(self):
        for line in self._thread.get_new_lines():
            if len(line) > 0:
                date, text = parse_line(line)
                for parser in self._parsers:
                    parser.parse(date, text)

    def _create_menu(self):
        # main menu
        menu = QMenu()
        main_menu_action_group = QActionGroup(menu)
        main_menu_action_group.setObjectName('system_menu')
        quit_action = QAction(menu)
        quit_action.setText("Quit")
        main_menu_action_group.addAction(quit_action)
        menu.addActions(main_menu_action_group.actions())
        menu.triggered[QAction].connect(self._menu_actions)
        return menu

    def _menu_actions(self, action):
        ag = action.actionGroup().objectName()
        at = action.text().lower()
        if ag == 'system_menu':
            if at == 'quit':
                self._quit()

    def _quit(self):
        for parser in self._parsers:
            print(parser.geometry(), dir(parser.geometry()))
            g = parser.geometry()
            config.data[parser.name]['geometry'] = [g.x(), g.y(), g.width(), g.height()]
        config.save()
        self._toggle(0)
        self._system_tray.setVisible(False)
        self.quit()

if __name__ == "__main__":
    try:
        appid = 'nomns.nparse'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except Exception as e:
        traceback.print_exc()
    app = NomnsParse(sys.argv)
    app.setStyleSheet(open('data/ui/_.css').read())
    app.setWindowIcon(QIcon('data/ui/icon.png'))
    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec())
