"""NomnsParse: Parsing tools for Project 1999."""
import os
import sys

from PySide6.QtGui import QFontDatabase, QIcon

from helpers import resource_path
from helpers.application import NomnsParse

if __name__ == "__main__":
    try:
        import ctypes
        APPID = 'nomns.nparse'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    except:
        pass

    APP = NomnsParse(sys.argv)
    APP.setStyleSheet(open(resource_path(os.path.join('data', 'ui', '_.css'))).read())
    APP.setWindowIcon(QIcon(resource_path(os.path.join('data', 'ui', 'icon.png'))))
    APP.setQuitOnLastWindowClosed(False)
    QFontDatabase.addApplicationFont(
        resource_path(os.path.join('data', 'fonts', 'NotoSans-Regular.ttf')))
    QFontDatabase.addApplicationFont(
        resource_path(os.path.join('data', 'fonts', 'NotoSans-Bold.ttf')))

    sys.exit(APP.exec())
