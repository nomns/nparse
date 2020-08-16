import json
import logging
import ssl
import time

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThreadPool
import websocket

from helpers import config

logger = logging.getLogger(__name__)
hdlr = logging.FileHandler('nparse_loc.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)


class LocationSignals(QObject):
    locs_recieved = pyqtSignal(dict)
    send_loc = pyqtSignal(dict)
    config_updated = pyqtSignal()


RUN = True
SIGNALS = LocationSignals()
THREADPOOL = QThreadPool()
_LSC = None


def get_location_service_connection():
    global _LSC
    if _LSC is None:
        _LSC = LocationServiceConnection()
    return _LSC


def start_location_service(update_func):
    try:
        SIGNALS.locs_recieved.disconnect()
    except TypeError:
        pass
    SIGNALS.locs_recieved.connect(update_func)
    SIGNALS.config_updated.connect(config_updated)
    config_updated()
    lsc = get_location_service_connection()
    THREADPOOL.start(lsc)


def stop_location_service():
    global RUN
    RUN = False
    lsc = get_location_service_connection()
    lsc.enabled = False
    lsc.configure_socket()


def config_updated():
    lsc = get_location_service_connection()
    lsc.enabled = config.data.get('sharing', {}).get('enabled', False)
    lsc.host = config.data.get('sharing', {}).get('url')
    lsc.reconnect_delay = config.data.get('sharing', {}).get('reconnect_delay', 5)
    lsc.configure_socket()


class LocationServiceConnection(QRunnable):
    _socket = None
    enabled = False
    host = None
    reconnect_delay = 5

    def __init__(self):
        super(LocationServiceConnection, self).__init__()
        try:
            SIGNALS.send_loc.disconnect()
        except TypeError:
            pass
        SIGNALS.send_loc.connect(self.send_loc)

    def configure_socket(self):
        if self._socket:
            print("Resetting socket, killing any open connection...")
            try:
                self._socket.close()
            except AttributeError:
                pass
            self._socket = None
        if self.host and self.enabled:
            print("Host set and sharing enabled, connecting...")
            self._socket = websocket.WebSocketApp(
                self.host, on_message=self._on_message,
                on_error=self._on_error, on_close=self._on_close,
                on_open=self._on_open)
        else:
            print("Sharing disabled.")

    @pyqtSlot()
    def run(self):
        while RUN:
            self.configure_socket()
            if self.enabled:
                print("Starting connection to sharing host...")
                self._socket.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            if RUN:
                time.sleep(self.reconnect_delay)

    def send_loc(self, loc):
        if not self.enabled:
            return
        message = {'type': "location",
                   'group_key': config.data['sharing']['group_key'],
                   'location': loc}
        try:
            self._socket.send(json.dumps(message))
        except:
            print("Unable to send location to server.")

    def _on_message(self, ws, message):
        message = json.loads(message)
        if message['type'] == "state":
            print("Message received: %s" % message)
            SIGNALS.locs_recieved.emit(message['locations'])

    def _on_error(self, ws, error):
        print("Connection error: %s" % error)

    def _on_open(self, ws):
        print("Connection opened.")

    def _on_close(self, ws):
        print("Connection closed.")
