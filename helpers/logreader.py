import threading
import time
import os
from glob import glob


class ThreadedLogReader(threading.Thread):

    def __init__(self, eq_directory, interval = 1):
        self._interval = interval
        self._eq_directory = eq_directory

        self._log_new_lines = []
        self._log_file = ""
        self._update_log_file()

        self._active = True

        threading.Thread.__init__(self)


    def get_new_lines(self):
        new_lines = [line.strip() for line in self._log_new_lines[:]]
        for num in range(0, len(new_lines)):
            self._log_new_lines.pop(0)
        return new_lines

    def _update_log_file(self):
        log_filter = os.path.join(
            self._eq_directory,
            "eqlog*.*"
        )
        files = glob(log_filter)
        tlog_file = max(files, key=os.path.getmtime)
        if tlog_file != self._log_file:
            with open(tlog_file, 'rb') as tlog:
                tlog.seek(0, os.SEEK_END)
                self._last_read = tlog.tell()
            self._file_size = os.stat(tlog_file).st_size
            self._log_file = tlog_file

    def run(self):
        while self._active:
            self._update_log_file()
            self._check_log()
            time.sleep(self._interval)

    def stop(self):
        self._active = False

    def _check_log(self):
        try:
            new_size = os.stat(self._log_file).st_size
            if type(self._file_size) == int and self._file_size < new_size:
                self._file_size = new_size
                with open(self._log_file, 'r') as file:
                    file.seek(self._last_read, os.SEEK_SET)
                    self._log_new_lines.extend(file.readlines())
                    self._last_read = file.tell()
                return True
            return False
        except Exception as e:
            print("FileReader().check_log():", e, type(e))
