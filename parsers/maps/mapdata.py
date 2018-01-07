from os import path
import math

from maps.mapgridgeometry import MapGridGeometry
from maps.mapline import MapLine
from maps.mappoint import MapPoint


class MapData:

    def __init__(self, map_name):
        self.map_name = map_name
        self.map_keys_file = 'maps/data/map_keys.ini'
        self.map_file_location = "maps/data/"
        self.map_pairs = {}
        self.map_lines = []
        self.map_points = []
        self.grid_lines = []
        self.map_grid_geometry = None
        self.load_map_pairs()
        # Allow for loading of map_keys without loading full map data
        if self.map_name is not None:
            self.load_map_data()

    def load_map_pairs(self):
        # Load Map Pairs from map_keys.ini
        with open(self.map_keys_file, 'r') as file:
            for line in file.readlines():
                values = line.split('=')
                self.map_pairs[values[0].strip()] = values[1].strip()

    def load_map_data(self):
        # Get list of all map files for current zone
        base_map_name = self.map_pairs[self.map_name.strip().lower()]
        extensions = ['.txt', '_1.txt', '_2.txt', '_3.txt']
        map_files = []
        for extension in extensions:
            file = path.join(self.map_file_location, base_map_name + extension)
            if path.exists(file):
                map_files.append(file)

        # Open each file and fill map_lines and map_points
        x_list = []  # holds all x values to find min/max/center
        y_list = []  # holds all y values to find min/max/center
        for map_file in map_files:
            with open(map_file, 'r') as file:
                for line in file.readlines():
                    line_type = line.lower()[0:1]
                    data = [value.strip() for value in line[1:].split(',')]
                    if line_type == 'l':
                        if int(float(data[6])) < 30 and int(float(data[7])) < 30 and int(float(data[8])) < 30:
                            data[6] = 200
                            data[7] = 200
                            data[8] = 200
                        self.map_lines.append(
                            MapLine(
                                x1=int(float(data[0])),
                                y1=int(float(data[1])),
                                z1=int(float(data[2])),
                                x2=int(float(data[3])),
                                y2=int(float(data[4])),
                                z2=int(float(data[5])),
                                r=int(float(data[6])),
                                g=int(float(data[7])),
                                b=int(float(data[8]))
                            )
                        )
                        x_list.append(int(float(data[0])))
                        x_list.append(int(float(data[3])))
                        y_list.append(int(float(data[1])))
                        y_list.append(int(float(data[4])))
                    elif line_type == 'p':
                        if int(float(data[3])) < 30 and int(float(data[4])) < 30 and int(float(data[5])) < 30:
                            data[3] = 200
                            data[4] = 200
                            data[5] = 200
                        self.map_points.append(
                            MapPoint(
                                x=int(float(data[0])),
                                y=int(float(data[1])),
                                z=int(float(data[2])),
                                r=int(float(data[3])),
                                g=int(float(data[4])),
                                b=int(float(data[5])),
                                size=int(float(data[6])),
                                text=str(data[7])
                            )
                        )
                    else:
                        pass  # Do not add to list

        # Setup Grid Size
        lowest_x = min(x_list)
        highest_x = max(x_list)
        lowest_y = min(y_list)
        highest_y = max(y_list)
        self.map_grid_geometry = MapGridGeometry(
            lowest_x=lowest_x,
            highest_x=highest_x,
            lowest_y=lowest_y,
            highest_y=highest_y,
            center_x=int(highest_x - (highest_x - lowest_x)/2),
            center_y=int(highest_y - (highest_y - lowest_y)/2),
            width=int(highest_x - lowest_x),
            height=int(highest_y - lowest_y)
        )

        # Create Grid Lines
        left = math.floor(lowest_x / 1000) * 1000
        right = math.ceil(highest_x / 1000) * 1000
        top = math.floor(lowest_y / 1000) * 1000
        bottom = math.ceil(highest_y / 1000) * 1000
        for number in range(left, right + 1000, 1000):
            self.grid_lines.append(
                MapLine(
                    x1=number,
                    x2=number,
                    y1=top,
                    y2=bottom,
                    z1=0,
                    z2=0,
                    r=255,
                    g=255,
                    b=255
                )
            )
        for number in range(top, bottom + 1000, 1000):
            self.grid_lines.append(
                MapLine(
                    y1=number,
                    y2=number,
                    x1=left,
                    x2=right,
                    z1=0,
                    z2=0,
                    r=255,
                    g=255,
                    b=255
                )
            )
