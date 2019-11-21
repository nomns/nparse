import datetime
import websocket
import ssl
import json

from threading import Thread
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from helpers import config


class LocationSignals(QObject):
    locs_recieved = pyqtSignal(dict)
    send_loc = pyqtSignal(dict)


class LocationServiceConnection(QRunnable):
    _socket = None

    def __init__(self, window):
        super(LocationServiceConnection, self).__init__()
        self.host = config.data.get('locserver', {}).get('url')
        if self.host:
            self._socket = websocket.WebSocketApp(
                self.host, on_message=self._on_message,
                on_error=self._on_error, on_close=self._on_close)
            self._socket.on_open = self._on_open
            self.signals = LocationSignals()
            self.signals.send_loc.connect(self.send_loc)

    @pyqtSlot()
    def run(self):
        self._socket.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def send_loc(self, loc):
        message = {'type': "location",
                   'location': loc}
        self._socket.send(json.dumps(message))

    def _on_message(self, ws, message):
        message = json.loads(message)
        if message['type'] == "state":
            # self.player_locations = message['locations']
            self.signals.locs_recieved.emit(message['locations'])

    def _on_error(self, ws, error):
        print("Connection error: %s" % error)

    def _on_open(self, ws):
        print("Connection opened.")

    def _on_close(self, ws):
        print("Closed connection.")

