"""Map parser for nparse."""
import re

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QApplication

from nParse.helpers.parser import ParserWindow
from nParse.helpers import config, to_real_xy
from nParse.parsers.maps.mapcanvas import MapCanvas
from nParse.parsers.maps.mapclasses import MapPoint
from nParse.parsers.maps.mapdata import MapData

ZONE_MATCHER = re.compile(r"There (is|are) \d+ players? in (?P<zone>.+)\.")

class MapsSignals(QObject):
    zoning = Signal()
    new_zone = Signal(str)
    location = Signal(str, str)
    death = Signal(str, str)
    start_recording = Signal(str)
    rename_recording = Signal(str)
    stop_recording = Signal()

class Maps(ParserWindow):

    def __init__(self):
        self.name = "maps"
        super().__init__()
        # interface
        self._map = MapCanvas()
        self.content.addWidget(self._map, 1)
        # buttons
        button_layout = QHBoxLayout()
        show_poi = QPushButton('\u272a')
        show_poi.setCheckable(True)
        show_poi.setChecked(config.data['maps']['show_poi'])
        show_poi.setToolTip('Show Points of Interest')
        show_poi.clicked.connect(self._toggle_show_poi)
        button_layout.addWidget(show_poi)
        auto_follow = QPushButton('\u25CE')
        auto_follow.setCheckable(True)
        auto_follow.setChecked(config.data['maps']['auto_follow'])
        auto_follow.setToolTip('Auto Center')
        auto_follow.clicked.connect(self._toggle_auto_follow)
        button_layout.addWidget(auto_follow)
        toggle_z_layers = QPushButton('\u24CF')
        toggle_z_layers.setCheckable(True)
        toggle_z_layers.setChecked(config.data['maps']['use_z_layers'])
        toggle_z_layers.setToolTip('Show Z Layers')
        toggle_z_layers.clicked.connect(self._toggle_z_layers)
        button_layout.addWidget(toggle_z_layers)
        show_grid_lines = QPushButton('#')
        show_grid_lines.setCheckable(True)
        show_grid_lines.setChecked(config.data['maps']['show_grid'])
        show_grid_lines.setToolTip('Show Grid')
        show_grid_lines.clicked.connect(self._toggle_show_grid)
        button_layout.addWidget(show_grid_lines)
        show_mouse_location = QPushButton('\U0001F6C8')
        show_mouse_location.setCheckable(True)
        show_mouse_location.setChecked(config.data['maps']['show_mouse_location'])
        show_mouse_location.setToolTip('Show Loc Under Mouse Pointer')
        show_mouse_location.clicked.connect(self._toggle_show_mouse_location)
        button_layout.addWidget(show_mouse_location)

        self.menu_area.addLayout(button_layout)

        if config.data['maps']['last_zone']:
            self._map.load_map(config.data['maps']['last_zone'])
        else:
            self._map.load_map('west freeport')

    def parse(self, timestamp, text):
        if text[:23] == 'LOADING, PLEASE WAIT...':
            QApplication.instance()._signals["maps"].zoning.emit()
        elif text[:16] == 'You have entered':
            QApplication.instance()._signals["maps"].new_zone.emit(text[17:-1])
            self._map.load_map(text[17:-1])
        elif ZONE_MATCHER.match(text):
            new_zone = ZONE_MATCHER.match(text).groupdict()['zone'].lower()
            new_zone = MapData.translate_who_zone(new_zone)
            if new_zone not in (self._map._data.zone.lower(), 'everquest'):
                QApplication.instance()._signals["maps"].new_zone.emit(new_zone)
                self._map.load_map(new_zone, keep_loc=True)
        elif text[:16] == 'Your Location is':
            QApplication.instance()._signals["maps"].location.emit(timestamp.isoformat(), text[17:])
            x, y, z = [float(value) for value in text[17:].strip().split(',')]
            x, y = to_real_xy(x, y)
            self._map.add_player('__you__', timestamp, MapPoint(x=x, y=y, z=z))
            self._map.record_path_loc((x, y, z))
        elif text[:16] == "start_recording_":
            QApplication.instance()._signals["maps"].start_recording.emit(text.split()[0][16:])
            recording_name = text.split()[0][16:]
            if recording_name:
                recording_name = recording_name.replace('_', ' ')
                self._map.start_path_recording(recording_name)
        elif text[:17] == "rename_recording_":
            QApplication.instance()._signals["maps"].rename_recording.emit(text.split()[0][17:])
            recording_name = text.split()[0][17:]
            if recording_name:
                recording_name = recording_name.replace('_', ' ')
                self._map.rename_path_recording(new_name=recording_name)
        elif text[:14] == "stop_recording":
            QApplication.instance()._signals["maps"].stop_recording.emit()
            self._map.stop_path_recording()
        elif text[:19] == "You have been slain":
            QApplication.instance()._signals["maps"].death.emit(timestamp.isoformat(), text)

    # events
    def _toggle_show_poi(self, _):
        config.data['maps']['show_poi'] = not config.data['maps']['show_poi']
        config.save()
        self._map.update_()

    def _toggle_auto_follow(self, _):
        config.data['maps']['auto_follow'] = not config.data['maps']['auto_follow']
        config.save()
        self._map.center()

    def _toggle_z_layers(self, _):
        config.data['maps']['use_z_layers'] = not config.data['maps']['use_z_layers']
        config.save()
        self._map.update_()

    def _toggle_show_grid(self, _):
        config.data['maps']['show_grid'] = not config.data['maps']['show_grid']
        config.save()
        self._map.update_()

    def _toggle_show_mouse_location(self, ):
        config.data['maps']['show_mouse_location'] = not config.data['maps']['show_mouse_location']
        config.save()
