import csv
import math
import pathlib
from collections import Counter

from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItemGroup

from nParse.helpers import config
from nParse.parsers.maps.mapclasses import MapPoint, MapGeometry, MapLine, PointOfInterest

MAP_KEY_FILE = 'data/maps/map_keys.ini'
MAP_KEY_FILE_WHO = 'data/maps/map_keys_who.ini'
MAP_SPAWNTIMES_FILE = 'data/maps/map_timers.csv'
MAP_FILES_LOCATION = 'data/maps/map_files'
MAP_FILES_PATHLIB = pathlib.Path(MAP_FILES_LOCATION)
ICON_MAP = {'corpse': 'data/maps/spawn.png'}


class MapData(dict):

    def __init__(self, zone=None):
        super().__init__()
        self.zone = zone
        self.raw = {'lines': [], 'poi': [], 'grid': []}
        self.geometry = None  # MapGeometry
        self.players = {}
        self.spawns = []
        self.waypoints = {}
        self.way_point = None
        self.grid = None

        if self.zone is not None:
            self._load()

    def _load(self):
        # Get list of all map files for current zone
        map_file_name = MapData.get_zone_dict()[self.zone.strip().lower()]
        maps = MAP_FILES_PATHLIB.glob(
            '**/{zone}*.txt'.format(zone=map_file_name))

        all_x, all_y, all_z = [], [], []

        # TODO: Remove the references to raw
        # Create Lines and Points
        for map_file in maps:
            print("Loading: %s" % map_file)
            with open(map_file, 'r') as f:
                for line in f.readlines():
                    line_type = line.lower()[0:1]
                    data = [value.strip() for value in line[1:].split(',')]
                    if line_type == 'l':  # line
                        x1, y1, z1, x2, y2, z2 = list(map(float, data[0:6]))
                        self.raw['lines'].append(MapLine(
                            x1=x1,
                            y1=y1,
                            z1=z1,
                            x2=x2,
                            y2=y2,
                            z2=z2,
                            color=self.color_transform(QColor(
                                int(data[6]),
                                int(data[7]),
                                int(data[8])
                            ))
                        ))
                        all_x.extend((x1, x2))
                        all_y.extend((y1, y2))
                        all_z.append(min(z1, z2))
                        # if abs(z1 - z2) < 2:
                        # if z1 == z2:
                        # all_z.extend((z1, z2))

                    elif line_type == 'p':  # point
                        x, y, z = map(float, data[0:3])
                        self.raw['poi'].append(MapPoint(
                            x=x,
                            y=y,
                            z=z,
                            size=int(data[6]),
                            text=str(data[7]),
                            color=self.color_transform(QColor(
                                int(data[3]),
                                int(data[4]),
                                int(data[5])
                            ))
                        ))

        # Create Grid Lines
        lowest_x, highest_x, lowest_y, highest_y, lowest_z, highest_z = min(all_x), max(all_x), min(all_y), max(
            all_y), min(all_z), max(all_z)

        left, right = int(math.floor(lowest_x / 1000) *
                          1000), int(math.ceil(highest_x / 1000) * 1000)
        top, bottom = int(math.floor(lowest_y / 1000) *
                          1000), int(math.ceil(highest_y / 1000) * 1000)

        for number in range(left, right + 1000, 1000):
            self.raw['grid'].append(MapLine(
                x1=number, x2=number, y1=top, y2=bottom, z1=0, z2=0, color=QColor(255, 255, 255, 25)))

        for number in range(top, bottom + 1000, 1000):
            self.raw['grid'].append(MapLine(
                y1=number, y2=number, x1=left, x2=right, z1=0, z2=0, color=QColor(255, 255, 255, 25)))

        self.grid = QGraphicsPathItem()
        line_path = QPainterPath()
        for line in self.raw['grid']:
            line_path.moveTo(line.x1, line.y1)
            line_path.lineTo(line.x2, line.y2)
        self.grid.setPath(line_path)
        self.grid.setPen(QPen(
            line.color,
            config.data['maps']['grid_line_width']
        ))
        self.grid.setZValue(0)

        # Get z levels
        counter = Counter(all_z)

        # bunch together zgroups based on peaks with floor being low point before rise
        z_groups = []
        last_value = None
        first_run = True
        for z in sorted(counter.items(), key=lambda x: x[0]):
            if last_value is None:
                last_value = z
                continue
            if (abs(last_value[0] - z[0]) < 20) or z[1] < 8:
                last_value = (last_value[0], last_value[1] + z[1])
            else:
                if first_run:
                    first_run = False
                    if last_value[1] < 40 or abs(last_value[0] - z[0]) < 18:
                        last_value = z
                        continue
                z_groups.append(last_value[0])
                last_value = z

        # get last iteration
        if last_value[1] > 50:
            z_groups.append(last_value[0])

        self._z_groups = z_groups

        # Create QGraphicsPathItem for lines seperately to retain colors
        temp_dict = {}
        for l in self.raw['lines']:
            lz = min(l.z1, l.z2)
            lz = self.get_closest_z_group(lz)
            if not temp_dict.get(lz, None):
                temp_dict[lz] = {'paths': {}}
            lc = l.color.getRgb()
            if not temp_dict[lz]['paths'].get(lc, None):
                path_item = QGraphicsPathItem()
                path_item.setPen(
                    QPen(l.color, config.data['maps']['line_width']))
                temp_dict[lz]['paths'][lc] = path_item
            path = temp_dict[lz]['paths'][lc].path()
            path.moveTo(l.x1, l.y1)
            path.lineTo(l.x2, l.y2)
            temp_dict[lz]['paths'][lc].setPath(path)

        # Group QGraphicsPathItems into QGraphicsItemGroups and update self
        for z in temp_dict:
            item_group = QGraphicsItemGroup()
            for (_, path) in temp_dict[z]['paths'].items():
                item_group.addToGroup(path)
            self[z] = {'paths': None, 'poi': []}
            self[z]['paths'] = item_group

        # Create Points of Interest
        for p in self.raw['poi']:
            z = self.get_closest_z_group(p.z)
            self[z]['poi'].append(
                PointOfInterest(location=p)
            )

        self.geometry = MapGeometry(
            lowest_x=lowest_x,
            highest_x=highest_x,
            lowest_y=lowest_y,
            highest_y=highest_y,
            lowest_z=lowest_z,
            highest_z=highest_z,
            center_x=int(highest_x - (highest_x - lowest_x) / 2),
            center_y=int(highest_y - (highest_y - lowest_y) / 2),
            width=int(highest_x - lowest_x),
            height=int(highest_y - lowest_y),
            z_groups=z_groups
        )

        # Load Spawn Timer Pairs from map_timers.csv
        with open(MAP_SPAWNTIMES_FILE, 'r') as file:
            reader = csv.reader(file)
            self.spawn_timer_dict = dict(reader)

    def get_closest_z_group(self, z):
        closest = min(self._z_groups, key=lambda x: abs(x - z))
        if z < closest:
            lower_index = self._z_groups.index(closest) - 1
            if lower_index > -1:
                closest = self._z_groups[lower_index]
        return closest

    @staticmethod
    def get_zone_dict():
        # Load Map Pairs from map_keys.ini
        zone_dict = {}
        with open(MAP_KEY_FILE, 'r') as file:
            for line in file.readlines():
                values = line.split('=')
                zone_dict[values[0].strip()] = values[1].strip()
        return zone_dict

    @staticmethod
    def translate_who_zone(zone_name):
        # Load Map Pairs from map_keys.ini
        zone_dict = {}
        with open(MAP_KEY_FILE_WHO, 'r') as file:
            for line in file.readlines():
                values = line.split('=')
                zone_dict[values[0].strip()] = values[1].strip()
        return zone_dict.get(zone_name, zone_name)

    def get_default_spawn_timer(self):
        try:
            short_zone = MapData.get_zone_dict().get(self.zone.strip().lower())
        except KeyError:
            short_zone = None
        return self.spawn_timer_dict.get(short_zone, '6:40')

    @staticmethod
    def color_transform(color):
        lightness = color.lightness()
        if lightness == 0:
            return QColor(255, 255, 255)
        if color.red == color.green == color.blue:
            return QColor(255, 255, 255)
        if lightness < 150:
            return color.lighter(150)
        return color
