"""Map parser for nparse."""
import datetime
import re

from PyQt6.QtWidgets import QHBoxLayout, QPushButton

from helpers import config, to_real_xy, ParserWindow, location_service

from .mapcanvas import MapCanvas
from .mapclasses import MapPoint
from .mapdata import MapData

ZONE_MATCHER = re.compile(r"There (is|are) \d+ players? in (?P<zone>.+)\.")


class Maps(ParserWindow):

    def __init__(self):
        super().__init__()
        self.name = 'maps'
        self.setWindowTitle(self.name.title())
        self.set_title(self.name.title())

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
        location_service.start_location_service(self.update_locs)

    def parse(self, timestamp, text):
        if text[:23] == 'LOADING, PLEASE WAIT...':
            pass
        elif text[:16] == 'You have entered':
            self._map.load_map(text[17:-1])
        elif ZONE_MATCHER.match(text):
            new_zone = ZONE_MATCHER.match(text).groupdict()['zone'].lower()
            new_zone = MapData.translate_who_zone(new_zone)
            if new_zone != self._map._data.zone.lower():
                self._map.load_map(new_zone)
        elif text[:16] == 'Your Location is':
            x, y, z = [float(value) for value in text[17:].strip().split(',')]
            x, y = to_real_xy(x, y)
            self._map.add_player('__you__', timestamp, MapPoint(x=x, y=y, z=z))
            self._map.record_path_loc((x, y, z))

            if location_service.get_location_service_connection().enabled:
                share_payload = {
                    'x': x,
                    'y': y,
                    'z': z,
                    'zone': self._map._data.zone,
                    'player': config.data['sharing']['player_name'],
                    'timestamp': timestamp.isoformat()
                }
                location_service.SIGNALS.send_loc.emit(share_payload)
        elif text[:16] == "start_recording_":
            recording_name = text.split()[0][16:]
            if recording_name:
                recording_name = recording_name.replace('_', ' ')
                self._map.start_path_recording(recording_name)
        elif text[:17] == "rename_recording_":
            recording_name = text.split()[0][17:]
            if recording_name:
                recording_name = recording_name.replace('_', ' ')
                self._map.rename_path_recording(new_name=recording_name)
        elif text[:14] == "stop_recording":
            self._map.stop_path_recording()
        elif text[:19] == "You have been slain":
            if (location_service.get_location_service_connection().enabled and
                    '__you__' in self._map._data.players):
                share_payload = {
                    'x': self._map._data.players['__you__'].location.x,
                    'y': self._map._data.players['__you__'].location.y,
                    'z': self._map._data.players['__you__'].location.z,
                    'zone': self._map._data.zone,
                    'player': config.data['sharing']['player_name'],
                    'timestamp': timestamp.isoformat(),
                    'timeout': 60,
                    'icon': 'corpse'
                }
                location_service.SIGNALS.death.emit(share_payload)

    def update_locs(self, locations, waypoints):
        print(f"Locations: {locations}")
        print(f"Waypoints: {waypoints}")
        for zone in locations:
            # Check which *map is loaded*, not character zone
            if zone != self._map._data.zone.lower():
                continue
            # Add players in the zone
            for player in locations[zone]:
                if player == config.data['sharing']['player_name']:
                    print(f"player found: {player} (self)")
                    continue
                print(f"player found: {player}")
                p_data = locations[zone][player]
                p_timestamp = datetime.datetime.fromisoformat(
                    p_data.get('timestamp'))
                p_point = MapPoint(
                    x=p_data['x'], y=p_data['y'], z=p_data['z'])
                self._map.add_player(player, p_timestamp, p_point)
            # Remove players that aren't in the zone
            players_to_remove = []
            for player in self._map._data.players:
                if player not in locations[zone] and player != '__you__':
                    players_to_remove.append(player)
            for player in players_to_remove:
                self._map.remove_player(player)
        for zone in waypoints:
            # Check which *map is loaded*, not character zone
            if zone != self._map._data.zone.lower():
                continue
            for waypoint in waypoints[zone]:
                print("waypoint found: %s" % waypoint)
                w_data = waypoints[zone][waypoint]
                w_point = MapPoint(
                    x=w_data['x'], y=w_data['y'], z=w_data['z'])
                w_icon = w_data.get('icon')
                self._map.add_waypoint(waypoint, w_point, w_icon)

            # Remove waypoints that aren't in the zone
            waypoints_to_remove = []
            for waypoint in self._map._data.waypoints:
                if waypoint not in waypoints[zone]:
                    waypoints_to_remove.append(waypoint)
            for waypoint in waypoints_to_remove:
                self._map.remove_waypoint(waypoint)

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
