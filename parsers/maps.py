from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, pyqtSignal
from PyQt5.QtGui import QPen, QColor, QTransform, QPainterPath, QPainter, QFont, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPixmapItem, QLabel

import traceback

from os import path
import math

from helpers.qtclasses import ParserWindow
from helpers import config


class Maps(ParserWindow):

    def __init__(self):
        self.name = 'maps'
        super().__init__()
        self.setWindowTitle('Maps')
        self.set_title('MAPS')

        try:
            self._map_canvas = MapCanvas()
        except Exception as e:
            traceback.print_exc()


        self.content.addWidget(self._map_canvas, 1)

        try:
            self._map_canvas.load_map(config.data['maps']['last_zone'])
        except Exception as e:
            traceback.print_exc()

        self._position_label = QLabel()
        self._position_label.setObjectName('MapAreaLabel')
        self.menu_area.addWidget(self._position_label)

        self._map_canvas.position_update.connect(self._update_position_label)

        self.show()

    def parse(self, date, text):
        if text[:23] == 'LOADING, PLEASE WAIT...':
            pass
        if text[:16] == 'You have entered':
            self._map_canvas.load_map(text[17:-1])
        if text[:16] == 'Your Location is':
            try:
                self._map_canvas.add_player('__you__', date, text[17:])
                self._map_canvas.update_players()
            except Exception as e:
                traceback.print_exc()

    def _update_position_label(self):
        mp = self._map_canvas.mouse_point
        if not mp:
            player = self._map_canvas.players.get('__you__', None)
            if player:
                self._position_label.setText('player: ({:.2f}, {:.2f})'.format(-player.y, -player.x))
        else:
            self._position_label.setText('mouse: ({:.2f}, {:.2f})'.format(mp.x(), mp.y()))





class MapCanvas(QGraphicsView):

    position_update = pyqtSignal()

    def __init__(self):
        # UI Init
        super().__init__()
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName('MapCanvas')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setContentsMargins(0, 0, 0, 0)
        self.setTransformationAnchor(self.AnchorViewCenter)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRenderHint(QPainter.Antialiasing)

        # Class Init
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.scale_ratio = 1
        self.map_data = None
        self.map_line_path_items = {}
        self.map_points_items = []
        self.map_points_text_items = []
        self.map_grid_path_item = QGraphicsPathItem()
        self.map_points_player_items = {}
        self.map_user_item = None
        self.mouse_point = None
        self.players = {}

    def load_map(self, map_name):
        try:
            self._scene.clear()
            self.map_data = MapData(map_name)
            self.create_grid_lines()
            self.create_map_lines()
            self.create_map_points()
            self.map_user_item = None
            self.update_players()
            self.set_scene_padding(self.map_data.map_grid_geometry.width,
                                   self.map_data.map_grid_geometry.height)
            self.draw()
            self.centerOn(0, 0)
            config.data['maps']['last_zone'] = self.map_data.map_name
            config.save()
        except Exception as e:
            traceback.print_exc()

    def create_grid_lines(self):
        grid_line_width = 3
        self.map_grid_path_item = QGraphicsPathItem()
        line_path = QPainterPath()
        for map_line in self.map_data.grid_lines:
            line_path.moveTo(map_line.x1, map_line.y1)
            line_path.lineTo(map_line.x2, map_line.y2)
        self.map_grid_path_item = QGraphicsPathItem(line_path)
        color = QColor().fromRgb(255, 255, 255, 25)
        self.map_grid_path_item.setPen(
            QPen(
                color,
                grid_line_width / self.scale_ratio
            )
        )

    def create_map_lines(self):
        map_line_width = config.data['maps']['line_width']
        # use color as string for dictionary keys to preserve line colours
        self.map_line_path_items = {}
        line_path = {}
        colors = {}
        for map_line in self.map_data.map_lines:
            key = str(map_line.r) + ',' \
                  + str(map_line.g) + ',' \
                  + str(map_line.b)
            if key not in line_path.keys():
                line_path[key] = QPainterPath()
                colors[key] = QColor().fromRgb(
                    map_line.r,
                    map_line.g,
                    map_line.b
                )
            line_path[key].moveTo(QPointF(map_line.x1, map_line.y1))
            line_path[key].lineTo(QPointF(map_line.x2, map_line.y2))
        for key in line_path.keys():
            self.map_line_path_items[key] = QGraphicsPathItem(line_path[key])
            self.map_line_path_items[key].setPen(
                QPen(
                    colors[key],
                    map_line_width / self.scale_ratio
                )
            )

    def create_map_points(self):
        self.map_points_text_items = []
        self.map_points_items = []
        for map_point in self.map_data.map_points:
            color = QColor().fromRgb(map_point.r, map_point.g, map_point.b)
            rect = QGraphicsRectItem(
                QRectF(
                    QPointF(map_point.x, map_point.y),
                    QSizeF(5 / self.scale_ratio, 5 / self.scale_ratio)
                )
            )
            rect.setPen(QPen(Qt.black, 1 / self.scale_ratio))
            rect.setBrush(color)
            self.map_points_items.append(rect)
            text = QGraphicsTextItem(map_point.text)
            text.setDefaultTextColor(color)
            text.setPos(map_point.x, map_point.y)
            text.setFont(QFont('Times New Roman', 8 / self.scale_ratio, 2))
            self.map_points_text_items.append(text)

    def draw(self):
        # Draw map grid
        self._scene.addItem(self.map_grid_path_item)

        # Draw map lines
        for key in self.map_line_path_items.keys():
            self._scene.addItem(self.map_line_path_items[key])

        # Draw map points
        for item in self.map_points_items:
            self._scene.addItem(item)

        # Draw map point's text
        for item in self.map_points_text_items:
            self._scene.addItem(item)

    def update_players(self):
        # Convert lists to sets
        player_list_set = set(self.players.keys())

        # Player points and text should be the same so only use one
        player_items_set = set(self.map_points_player_items.keys())

        # calculate size of player circles
        circle_size = max(10.0, 10 / self.scale_ratio)

        # Draw and/or update all players in players
        for player in player_list_set:
            player_data = self.players[player]
            if player_data.name == '__you__':
                if not self.map_user_item:
                    self.map_user_item = QGraphicsPixmapItem(QPixmap('data/maps/player_icon.png'))
                    self._scene.addItem(self.map_user_item)
                    self.map_user_item.setOffset(-10, -20)
                self.map_user_item.setPos(player_data.x , player_data.y)
                self.map_user_item.setScale(1 / self.scale_ratio)
            else:
                if player in player_items_set and \
                        self.map_points_player_items[player] in self._scene.items():
                    # Update
                    self.map_points_player_items[player_data.name].setRect(
                        player_data.x - circle_size / 2,
                        player_data.y - circle_size / 2,
                        circle_size,
                        circle_size
                    )
                else:
                    # Create New Point
                    color = QColor().fromRgb(
                        player_data.r,
                        player_data.g,
                        player_data.b
                    )
                    circle = QGraphicsEllipseItem(
                        player_data.x - circle_size / 2,
                        player_data.y - circle_size / 2,
                        circle_size,
                        circle_size
                    )
                    circle.setBrush(color)
                    self.map_points_player_items[player_data.name] = circle
                    self._scene.addItem(
                        self.map_points_player_items[player_data.name]
                    )

        # Find/remove players who aren't in players list from the map
        for key in [player for player in player_items_set
                    if player not in player_list_set]:
            self._scene.removeItem(self.map_points_player_items[key])

        # Center map
        self.center()

    def set_scale(self, ratio):
        # Scale scene
        self.setTransform(QTransform())
        self.scale_ratio = ratio
        self.scale(self.scale_ratio, self.scale_ratio)

        # Scale map lines
        map_line_width = config.data['maps']['line_width']
        for key in self.map_line_path_items.keys():
            pen = self.map_line_path_items[key].pen()
            pen.setWidth(
                max(
                    map_line_width,
                    map_line_width / self.scale_ratio
                )
            )
            self.map_line_path_items[key].setPen(pen)

        # Scale map grid
        grid_line_width = config.data['maps']['grid_line_width']
        pen = self.map_grid_path_item.pen()
        pen.setWidth(
            max(
                grid_line_width,
                grid_line_width / self.scale_ratio
            )
        )
        self.map_grid_path_item.setPen(pen)

        # Scale map points
        for i, rect in enumerate(self.map_points_items):
            rect.setRect(
                self.map_data.map_points[i].x,
                self.map_data.map_points[i].y,
                max(5, 5 / self.scale_ratio),
                max(5, 5 / self.scale_ratio)
            )

        # Scale map point's text
        for i, text in enumerate(self.map_points_text_items):
            text.setFont(
                QFont(
                    'Times New Roman',
                    max(8, 8 / self.scale_ratio)
                )
            )
            text.setX(
                self.map_data.map_points[i].x + max(5, 5 / self.scale_ratio)
            )

        # Scale player point
        circle_size = max(10, 10 / self.scale_ratio)
        for player in self.map_points_player_items.keys():
            self.map_points_player_items[player].setRect(
                self.players[player].x - circle_size / 2,
                self.players[player].y - circle_size / 2,
                circle_size,
                circle_size
            )

        if self.map_user_item:
            self.map_user_item.setScale(1 / self.scale_ratio)

    def set_scene_padding(self, padding_x, padding_y):
        # Make it so that if you are zoomed in, you can still
        # drag the map around (not that smooth)
        rect = self._scene.sceneRect()
        rect.adjust(
            -padding_x * 2, -padding_y * 2, padding_x * 2, padding_y * 2
        )
        self.setSceneRect(rect)

    def draw_loading_screen(self):
        pass

    def fit_to_window(self):
        pass

    def center(self):
        # Center on Player for now by default
        # Added try/except because initialization causes resize event
        try:
            if '__you__' in self.players.keys():
                self.centerOn(
                    self.players['__you__'].x,
                    self.players['__you__'].y
                )
        except AttributeError as e:
            print("MapCanvas().center():", e)


    def add_player(self, name, time_stamp, location):
        y, x, z = [float(value) for value in location.strip().split(',')]
        y = -y
        x = -x
        if name not in self.players.keys():
            r, g, b = (0, 255, 0)
            flag = '__other__'
            user_level = None
            if name == '__you__':
                r, g, b = (0, 255, 0)
                flag = '__you__'
                user_level = None
            self.players[name] = Player(
                name=name,
                x=x,
                y=y,
                z=z,
                r=r,
                g=g,
                b=b,
                flag=flag,
                user_level=user_level,
                time_stamp=time_stamp
            )
        else:
            self.players[name].x = x
            self.players[name].y = y
            self.players[name].z = z
            self.players[name].time_stamp = time_stamp

        self.mouse_point = None
        self.position_update.emit()

    def mouseMoveEvent(self, QMouseEvent):
        e = QMouseEvent
        pos = self.mapToScene(e.pos())
        self.mouse_point = QPointF(-pos.y(), -pos.x())
        self.position_update.emit()
        QGraphicsView.mouseMoveEvent(self, QMouseEvent)



    def wheelEvent(self, event):
        # Scale based on scroll wheel direction
        movement = event.angleDelta().y()
        if movement > 0:
            self.set_scale(self.scale_ratio + self.scale_ratio * 0.1)
        else:
            self.set_scale(self.scale_ratio - self.scale_ratio * 0.1)

    def keyPressEvent(self, event):
        # Enable drag mode while control button is being held down
        if event.modifiers() == Qt.ControlModifier:
            self.setDragMode(self.ScrollHandDrag)
        QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        # Disable drag mode when control button released
        if event.key() == Qt.Key_Control:
            self.setDragMode(self.NoDrag)
        QGraphicsView.keyPressEvent(self, event)

    def resizeEvent(self, event):
        self.center()
        QGraphicsView.resizeEvent(self, event)


class MapData:

    def __init__(self, map_name):
        self.map_name = map_name
        self.map_keys_file = 'data/maps/map_keys.ini'
        self.map_file_location = "data/maps"
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
        left = int(math.floor(lowest_x / 1000) * 1000)
        right = int(math.ceil(highest_x / 1000) * 1000)
        top = int(math.floor(lowest_y / 1000) * 1000)
        bottom = int(math.ceil(highest_y / 1000) * 1000)
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


class Player:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MapPoint:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MapLine:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MapGridGeometry:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
