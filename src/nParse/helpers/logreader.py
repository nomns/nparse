from datetime import datetime
from glob import glob
import os

from PySide6.QtCore import QFileSystemWatcher, Signal, QObject
from PySide6.QtWidgets import QApplication

from nParse.helpers import strip_timestamp

class LogReaderSignals(QObject):
    new_line = Signal(object)
    character_updated = Signal(str)
    server_updated = Signal(str)
    def __init__(self):
        super().__init__()

class LogReader(QFileSystemWatcher):
    character_name = None
    server_name = None

    def __init__(self, eq_directory):
        super().__init__()

        self._eq_directory = eq_directory
        self._files = glob(os.path.join(eq_directory, 'eqlog_*_*.txt'))
        self._watcher = QFileSystemWatcher(self._files)
        self._watcher.fileChanged.connect(self._file_changed_safe_wrap)
        self._dir_watcher = QFileSystemWatcher([eq_directory])
        self._dir_watcher.directoryChanged.connect(self._dir_changed)

        self._stats = {
            'log_file': '',
            'last_read': 0,
        }

    def _dir_changed(self, changed_dir):
        print("Directory '%s' updated, refreshing file list..." % changed_dir)
        new_files = glob(os.path.join(self._eq_directory, 'eqlog_*_*.txt'))
        if new_files != self._files:
            files_to_remove = set(self._files) - set(new_files)
            if files_to_remove:
                self._watcher.removePaths(files_to_remove)
            updated_files = set(new_files) - set(self._files)
            self._watcher.addPaths(updated_files)
            self._files = new_files

    def _file_changed_safe_wrap(self, changed_file):
        try:
            self._file_changed(changed_file)
        except FileNotFoundError:
            print("File not found: %s; did it move?")

    def _file_changed(self, changed_file):
        if changed_file != self._stats['log_file']:
            self._stats['log_file'] = changed_file
            char_name = os.path.basename(changed_file).split("_")[1]
            server_name = os.path.basename(changed_file).split("_")[2][:-4]
            if server_name != self.server_name:
                self.server_name = server_name
                QApplication.instance()._signals["logreader"].server_updated.emit(server_name)
            if char_name != self.character_name:
                self.character_name = char_name
                QApplication.instance()._signals["logreader"].character_updated.emit(char_name)
            with open(self._stats['log_file'], 'rb') as log:
                log.seek(0, os.SEEK_END)
                current_end = log.tell()
                log.seek(max(log.tell() - 1000, 0), os.SEEK_SET)
                for line in log:
                    if line.endswith(b'] Welcome to EverQuest!\r\n'):
                        break
                self._stats['last_read'] = min(log.tell(), current_end)

        with open(self._stats['log_file']) as log:
            try:
                log.seek(self._stats['last_read'], os.SEEK_SET)
                lines = log.readlines()
                self._stats['last_read'] = log.tell()
                for line in lines:
                    QApplication.instance()._signals["logreader"].new_line.emit((
                        datetime.now(),
                        strip_timestamp(line)
                        ))
            except Exception:  # do not read lines if they cause errors
                log.seek(0, os.SEEK_END)
                self._stats['last_read'] = log.tell()
