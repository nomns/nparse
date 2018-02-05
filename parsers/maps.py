"""Map parser for nparse."""
import traceback
from PyQt5 import QtCore
from os import path
import math

from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, pyqtSignal, QLineF, QObject
from PyQt5.QtGui import QPen, QColor, QTransform, QPainterPath, QPainter, QFont, QPixmap
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
                             QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPixmapItem, QLabel, QMenu,
                             QGraphicsLineItem, QInputDialog)

from parsers import ParserWindow
from helpers import config, resource_path


class Maps(ParserWindow):

    def __init__(self):
        super().__init__()
        self.name = 'maps'
        self.setWindowTitle(self.name.title())
        self.set_title(self.name.title())

        self._setup_ui()

        if config.data['maps']['last_zone']:
            self._map_canvas.load_map(config.data['maps']['last_zone'])
        else:
            self._map_canvas.load_map('west freeport')

    def _setup_ui(self):
        self._map_canvas = MapCanvas()
        self.content.addWidget(self._map_canvas, 1)

        self._position_label = QLabel()
        self._position_label.setObjectName('MapAreaLabel')
        self.menu_area.addWidget(self._position_label)

        self._map_canvas.position_update.connect(self._update_position_label)

    def parse(self, time, text):
        if text[:23] == 'LOADING, PLEASE WAIT...':
            pass
        if text[:16] == 'You have entered':
            self._map_canvas.load_map(text[17:-1])
        if text[:16] == 'Your Location is':
            try:
                self._map_canvas.add_player('__you__', time, text[17:])
                self._map_canvas.update_players()
            except:
                traceback.print_exc()

    def _update_position_label(self):
        mp = self._map_canvas.mouse_point
        if not mp:
            player = self._map_canvas.players.get('__you__', None)
            if player:
                self._position_label.setText(
                    'player: ({:.2f}, {:.2f})'.format(-player.y, -player.x))
        else:
            self._position_label.setText(
                'mouse: ({:.2f}, {:.2f})'.format(mp.x(), mp.y()))


class MapCanvas(QGraphicsView):
    """Map Widget for Everquest Map Files

    Z Values for graphics items:
        grid: 0
        map: 1
        points/poi text: 2
        players: 9
        user: 10
        way point: 11
    """

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
        self.scale_ratio = config.data['maps']['scale']
        self.map_data = None
        self.map_line_path_items = {}
        self.map_points_items = []
        self.map_points_text_items = []
        self.map_grid_path_item = QGraphicsPathItem()
        self.map_points_player_items = {}
        self.map_user_item = None
        self.map_way_point = None
        self.mouse_point = None
        self.players = {}

    def load_map(self, map_name):
        try:
            map_data = MapData(str(map_name))
        except:
            traceback.print_exc()
        else:
            self.map_data = map_data
            self._scene.clear()
            self._create_map_items()
            self.map_user_item = None
            self.map_way_point = None
            self.update_players()
            self.set_scene_padding(self.map_data.map_grid_geometry.width,
                                   self.map_data.map_grid_geometry.height)
            self.draw()
            self.centerOn(0, 0)
            config.data['maps']['last_zone'] = self.map_data.map_name
            config.save()

    def _create_map_items(self):

        # Create grid lines
        grid_line_width = 3
        self.map_grid_path_item = QGraphicsPathItem()
        self.map_grid_path_item.setZValue(0)
        line_path = QPainterPath()
        for map_line in self.map_data.grid_lines:
            line_path.moveTo(map_line.x1, map_line.y1)
            line_path.lineTo(map_line.x2, map_line.y2)
        self.map_grid_path_item = QGraphicsPathItem(line_path)
        color = QColor().fromRgb(255, 255, 255, 25)
        self.map_grid_path_item.setPen(
            QPen(
                color,
                grid_line_width
            )
        )

        # Create map lines
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
                    map_line_width
                )
            )
            self.map_line_path_items[key].setZValue(1)

        # Create points of interest
        self.map_points_text_items = []
        self.map_points_items = []
        for map_point in self.map_data.map_points:
            color = QColor().fromRgb(map_point.r, map_point.g, map_point.b)
            rect = QGraphicsRectItem(
                QRectF(
                    QPointF(map_point.x, map_point.y),
                    QSizeF(5, 5)
                )
            )
            rect.setPen(QPen(Qt.white, 1))
            rect.setBrush(color)
            rect.setZValue(2)
            self.map_points_items.append(rect)
            text_string = map_point.text.replace('_', ' ')
            text = QGraphicsTextItem(text_string)
            text.setDefaultTextColor(color)
            text.setPos(map_point.x, map_point.y)
            text.setFont(QFont('Noto Sans', 8, 2))
            text.setZValue(2)
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

        self._update()

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
                    self.map_user_item = QGraphicsPixmapItem(
                        QPixmap('data/maps/user.png'))
                    self._scene.addItem(self.map_user_item)
                    self.map_user_item.setOffset(-10, -10)
                    self.map_user_item.setZValue(10)
                self.map_user_item.setPos(player_data.x, player_data.y)
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
        self._update()

    def _update(self, ratio=None):
        if not ratio:
            ratio = self.scale_ratio

        # scene
        self.setTransform(QTransform())  # reset transform object
        self.scale_ratio = min(5.0, max(0.006, ratio))
        config.data['maps']['scale'] = self.scale_ratio
        self.scale(self.scale_ratio, self.scale_ratio)

        # map lines
        map_line_width = config.data['maps']['line_width']
        for key in self.map_line_path_items.keys():
            pen = self.map_line_path_items[key].pen()
            pen.setWidth(
                max(map_line_width, map_line_width / self.scale_ratio))
            self.map_line_path_items[key].setPen(pen)

        # map grid
        grid_line_width = config.data['maps']['grid_line_width']
        pen = self.map_grid_path_item.pen()
        pen.setWidth(max(grid_line_width, grid_line_width / self.scale_ratio))
        self.map_grid_path_item.setPen(pen)

        # map points and text points for points of interest
        for rect_item, text_item in zip(self.map_points_items, self.map_points_text_items):
            if config.data['maps']['show_poi']:
                if not rect_item.isVisible():
                    rect_item.setVisible(True)
                    text_item.setVisible(True)
                rect = rect_item.rect()
                x, y = rect.x(), rect.y()
                rect_item.setRect(
                    x, y, max(5.0, 5.0 / self.scale_ratio), max(5.0, 5.0 / self.scale_ratio))
                text_item.setFont(
                    QFont('Noto Sans', max(8.0, 8.0 / self.scale_ratio)))
                text_x = x - text_item.boundingRect().width() / 2
                text_item.setX(int(text_x + self._to_scale(5.0)))
            else:
                rect_item.setVisible(False)
                text_item.setVisible(False)

        # player points
        circle_size = max(10.0, 10.0 / self.scale_ratio)
        for player in self.map_points_player_items.keys():
            self.map_points_player_items[player].setRect(
                self.players[player].x - circle_size / 2,
                self.players[player].y - circle_size / 2,
                circle_size,
                circle_size
            )

        # way point
        if self.map_way_point:
            rect = self.map_way_point.rect.rect()
            x, y = rect.x(), rect.y()
            self.map_way_point.rect.setRect(
                x, y, self._to_scale(8.0), self._to_scale(8.0))
            if '__you__' in self.players.keys():
                x, y = self.players['__you__'].x, self.players['__you__'].y
                self.map_way_point.line.setVisible(True)
                line = self.map_way_point.line.line()
                line.setP1(QPointF(x, y))
                line.setP2(rect.center())
                self.map_way_point.line.setLine(line)
                self.map_way_point.line.setPen(
                    QPen(Qt.green, self._to_scale(1), Qt.DashLine))

        # user icon
        if self.map_user_item:
            self.map_user_item.setScale(1 / self.scale_ratio)

    def _to_scale(self, float_value):
        return max(float_value, float_value / self.scale_ratio)

    def set_scene_padding(self, padding_x, padding_y):
        """Create an empty padding around used coordinates to allow more movement when dragging map."""
        rect = self._scene.sceneRect()
        rect.adjust(
            -padding_x * 2, -padding_y * 2, padding_x * 2, padding_y * 2
        )
        self.setSceneRect(rect)

    def center(self):
        # Center on Player for now by default
        # Added try/except because self.__init__ causes resize event
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

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.mouse_point = QPointF(-pos.y(), -pos.x())
        self.position_update.emit()
        QGraphicsView.mouseMoveEvent(self, event)

    def wheelEvent(self, event):
        # Scale based on scroll wheel direction
        movement = event.angleDelta().y()
        if movement > 0:
            self._update(self.scale_ratio + self.scale_ratio * 0.1)
        else:
            self._update(self.scale_ratio - self.scale_ratio * 0.1)

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

    def contextMenuEvent(self, event):
        # create menu
        pos = self.mapToScene(event.pos())
        menu = QMenu(self)
        # remove from memory after usage
        menu.setAttribute(Qt.WA_DeleteOnClose)
        way_point_menu = menu.addMenu("Way Point")
        way_point_create = way_point_menu.addAction("Create on Cursor")
        way_point_delete = way_point_menu.addAction("Clear")
        show_menu = menu.addMenu("Show")
        show_poi = show_menu.addAction("Points of Interest")
        show_poi.setCheckable(True)
        if config.data['maps']['show_poi']:
            show_poi.setChecked(True)
        load_map = menu.addAction("Load Map")

        # execute
        action = menu.exec_(self.mapToGlobal(event.pos()))

        # parse response
        if action == show_poi:
            config.data['maps']['show_poi'] = show_poi.isChecked()
            config.save()

        if action == way_point_create:
            if self.map_way_point:
                self._scene.removeItem(self.map_way_point.line)
                self._scene.removeItem(self.map_way_point.rect)
            rect = QGraphicsRectItem(
                QRectF(QPointF(pos.x(), pos.y()), QSizeF(8.0, 8.0)))
            rect.setBrush(Qt.green)
            rect.setZValue(11)
            x, y = 0.0, 0.0
            if '__you__' in self.players.keys():
                x, y = self.players['__you__'].x, self.players['__you__'].y
            q_line = QLineF(x, y, 0.0, 0.0)
            q_line.setP2(rect.rect().center())
            line = QGraphicsLineItem(q_line)
            line.setVisible(False)
            line.setPen(QPen(Qt.green, 1, Qt.DashLine))
            line.setZValue(11)
            self.map_way_point = WayPoint(line=line, rect=rect)
            self._scene.addItem(self.map_way_point.line)
            self._scene.addItem(self.map_way_point.rect)
        if action == way_point_delete:
            if self.map_way_point:
                self._scene.removeItem(self.map_way_point.line)
                self._scene.removeItem(self.map_way_point.rect)
            self.map_way_point = None

        if action == load_map:
            dialog = QInputDialog(self)
            dialog.setWindowTitle('Load Map')
            dialog.setLabelText('Select map to load:')
            dialog.setComboBoxItems(sorted([map.title()
                                            for map in self.map_data.map_pairs.keys()]))
            if dialog.exec_():
                self.load_map(dialog.textValue().lower())
            dialog.deleteLater()

        self._update()

    def resizeEvent(self, event):
        self.center()
        QGraphicsView.resizeEvent(self, event)


class MapData:

    def __init__(self, map_name):
        self.map_name = map_name
        self.map_keys_file = 'data/maps/map_keys.ini'
        self.map_file_location = 'data/maps/map_files'
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
            center_x=int(highest_x - (highest_x - lowest_x) / 2),
            center_y=int(highest_y - (highest_y - lowest_y) / 2),
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


class WayPoint:
    def __init__(self, **kwargs):
        self.line = None
        self.rect = None
        self.__dict__.update(kwargs)


class MapLine:
    def __init__(self, **kwargs):
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.z1 = 0
        self.r = 0
        self.g = 0
        self.b = 0
        self.__dict__.update(kwargs)


class MapGridGeometry:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
