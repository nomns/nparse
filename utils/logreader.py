import os
import datetime
from glob import glob
from dataclasses import dataclass

from PyQt5.QtCore import QFileSystemWatcher, pyqtSignal

from config import app_config
from utils import strip_timestamp


@dataclass
class LogStats:
    log_file: str = ""
    last_read: int = None


class LogReader(QFileSystemWatcher):

    new_line = pyqtSignal(object)
    log_file_change = pyqtSignal(str)

    def __init__(self, log_dir: str) -> None:
        super().__init__()

        self._files = glob(os.path.join(log_dir, "eqlog*.txt"))
        self._files_last_read = self._get_all_last_read()
        self._watcher = QFileSystemWatcher(self._files)
        self._watcher.fileChanged.connect(self._file_changed)

        self._stats = LogStats()

        if app_config.last_profile:
            self._stats.log_file = os.path.join(log_dir, app_config.last_profile)

    def _get_all_last_read(self) -> dict:
        d = {}
        for file in self._files:
            with open(file) as log:
                log.seek(0, os.SEEK_END)
                d[file] = log.tell()
        return d

    def _file_changed(self, changed_file: str) -> None:
        if changed_file != self._stats.log_file or not self._stats:
            if changed_file != self._stats.log_file:
                self._files_last_read[self._stats.log_file] = self._stats.last_read
                self._stats.log_file = changed_file
                self.log_file_change.emit(os.path.abspath(changed_file))
            if changed_file in self._files_last_read:
                self._stats.last_read = self._files_last_read[changed_file]
            else:
                with open(self._stats.log_file) as log:
                    log.seek(0, os.SEEK_END)
                    self._stats.last_read = log.tell()

        with open(self._stats.log_file) as log:
            try:
                log.seek(self._stats.last_read, os.SEEK_SET)
                lines = log.readlines()
                self._stats.last_read = log.tell()
                for line in lines:
                    self.new_line.emit((datetime.datetime.now(), strip_timestamp(line)))
            except Exception:
                # do not read lines if they cause errors
                # TODO: update this to safely read these lines
                log.seek(0, os.SEEK_END)
                self._stats.last_read = log.tell()
