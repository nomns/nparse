import os
import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle')
    qt_prefix = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt').replace("\\", "\\\\")
    with open('qt.conf', 'w') as qtconf:
        qtconf.writelines(['[Paths]\n', 'Prefix = %s\n' % qt_prefix])
else:
    print('running in a normal Python process')
