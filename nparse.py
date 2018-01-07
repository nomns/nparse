import sys
import ctypes

import traceback

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QSystemTrayIcon, QApplication, QMenu, QAction,
                             QActionGroup)

from helpers import config, logreader, parse_line
config.load('data/config.yaml')


class NomnsParse(QApplication):

    def __init__(self, *args):
        QApplication.__init__(self, *args)

        # Tray Icon
        self._system_tray = QSystemTrayIcon()
        self._system_tray.setIcon(QIcon('data/ui/icon.png'))
        self._system_tray.setToolTip("Parse99")
        self._system_tray.show()

        # Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._parse)

        # Thread
        self._thread = None

        # Menu
        self._system_tray.setContextMenu(self._get_menu())

        # Turn On
        self._toggle(1)

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
                print(parse_line(line))

    def _get_menu(self):
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
