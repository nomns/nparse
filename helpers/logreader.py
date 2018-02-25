import os
import datetime
from glob import glob

from PyQt5.QtCore import QFileSystemWatcher, pyqtSignal

from helpers import strip_timestamp


class LogReader(QFileSystemWatcher):

    new_line = pyqtSignal(object)

    def __init__(self, eq_directory):
        super().__init__()

        self._files = glob(os.path.join(eq_directory, 'eqlog*.txt'))
        self._watcher = QFileSystemWatcher(self._files)
        self._watcher.fileChanged.connect(self._file_changed)

        self._stats = {
            'log_file': '',
            'last_read': 0,
        }

    def _file_changed(self, changed_file):
        if changed_file != self._stats['log_file']:
            self._stats['log_file'] = changed_file
            with open(self._stats['log_file']) as log:
                log.seek(0, os.SEEK_END)
                self._stats['last_read'] = log.tell()
        with open(self._stats['log_file']) as log:
            log.seek(self._stats['last_read'], os.SEEK_SET)
            lines = log.readlines()
            self._stats['last_read'] = log.tell()
            for line in lines:
                self.new_line.emit((datetime.datetime.now(), strip_timestamp(line)))
