"""Map parser for nparse."""
import traceback
from PyQt5 import QtCore
from os import path
import math
import datetime

from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, pyqtSignal, QLineF, QObject, QTimer
from PyQt5.QtGui import QPen, QColor, QTransform, QPainterPath, QPainter, QFont, QPixmap, QTransform
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem,
                             QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPixmapItem, QLabel, QMenu,
                             QGraphicsLineItem, QInputDialog, QGraphicsItemGroup)

from parsers import ParserWindow
from helpers import config, resource_path, to_range, to_real_xy, to_eq_xy, get_degrees_from_line, format_time, text_time_to_seconds

SPAWN_TEXT_MIN = 0.1
SPAWN_TEXT_SIZE = 10
SPAWN_TEXT_MAX = 50
TEXT_SIZE_MIN = 0.1
TEXT_SIZE = 12
TEXT_SIZE_MAX = 50
POINT_SIZE_MIN = 0.1
POINT_SIZE = 5
POINT_SIZE_MAX = 25


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
                x, y = to_eq_xy(player.location.x, player.location.y)
                self._position_label.setText(
                    'player: ({:.2f}, {:.2f})'.format(-player.location.y, -player.location.x))
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
        directional: 11
        spawn_point 15
        way point: 20 and 21 (line and point)
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
        self.map_user_item = None
        self.map_user_directional = None
        self.map_way_point = None
        self.map_spawn_points = []
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
            self.map_user_directional = None
            self.map_way_point = None
            self.map_spawn_points = []
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
            color = QColor().fromRgb(map_point.color.r, map_point.color.g, map_point.color.b)
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
            text.setFont(QFont('Noto Sans', 8))
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
        # Draw and/or update all players in players
        for player in self.players.values():
            if player.name == '__you__':
                if not self.map_user_item:
                    self.map_user_item = QGraphicsPixmapItem(
                        QPixmap('data/maps/user.png'))
                    self._scene.addItem(self.map_user_item)
                    self.map_user_item.setOffset(-10, -10)
                    self.map_user_item.setZValue(10)
                    self.map_user_item.setPos(
                        player.location.x, player.location.y)
                else:
                    if not self.map_user_directional:
                        self.map_user_directional = QGraphicsPixmapItem(
                            QPixmap('data/maps/directional.png'))
                        self._scene.addItem(self.map_user_directional)
                        self.map_user_directional.setZValue(11)
                        self.map_user_directional.setOffset(-15, -15)
                        self.map_user_item.setScale(1 / self.scale_ratio)
                    self.map_user_directional.setRotation(
                        get_degrees_from_line(
                            player.location.x,
                            player.location.y,
                            player.previous_location.x,
                            player.previous_location.y
                        )
                    )
                    self.map_user_item.setPos(
                        player.location.x, player.location.y
                    )
                    self.map_user_directional.setPos(
                        player.location.x, player.location.y
                    )
        self.center()
        self._update()

    def _update(self, ratio=None):
        if not ratio:
            ratio = self.scale_ratio

        # scene
        self.setTransform(QTransform())  # reset transform object
        self.scale_ratio = to_range(ratio, 0.0006, 5.0)
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
                    x, y, to_range(self._to_scale(POINT_SIZE),
                                   POINT_SIZE_MIN, POINT_SIZE_MAX),
                    to_range(self._to_scale(POINT_SIZE),
                             POINT_SIZE_MIN, POINT_SIZE_MAX))

                text_item.setFont(
                    QFont('Noto Sans', to_range(self._to_scale(TEXT_SIZE), TEXT_SIZE_MIN, TEXT_SIZE_MAX), italic=True))
                text_item.setX(x - text_item.boundingRect().width() / 2)
            else:
                rect_item.setVisible(False)
                text_item.setVisible(False)

        # way point
        if self.map_way_point:
            self.map_way_point.pixmap.setScale(1 / self.scale_ratio)
            if '__you__' in self.players.keys():
                x, y = self.players['__you__'].location.x, self.players['__you__'].location.y
                line = self.map_way_point.line.line()
                line.setP1(QPointF(x, y))
                self.map_way_point.line.setLine(line)
                self.map_way_point.line.setPen(
                    QPen(Qt.green, self._to_scale(1), Qt.DashLine))
                self.map_way_point.line.setVisible(True)

        # user icon
        if self.map_user_item:
            self.map_user_item.setScale(1 / self.scale_ratio)

        # user directional
        if self.map_user_directional:
            self.map_user_directional.setScale(1 / self.scale_ratio)

        #  spawn points
        for spawn in self.map_spawn_points:
            spawn.pixmap.setScale(1 / self.scale_ratio)
            spawn.text.setScale(1 / self.scale_ratio)
            spawn.realign()
            spawn.prepareGeometryChange()

    def _to_scale(self, float_value):
        # return max(float_value, float_value / self.scale_ratio)
        return float_value / self.scale_ratio

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
            if config.data['maps']['auto_follow'] and '__you__' in self.players.keys():
                self.centerOn(
                    self.players['__you__'].location.x, self.players['__you__'].location.y)
        except AttributeError as e:
            print("MapCanvas().center():", e)

    def add_player(self, name, time_stamp, location):
        x, y, z = [float(value) for value in location.strip().split(',')]
        x, y = to_real_xy(x, y)  # eq pos to standard pos
        if name not in self.players.keys():
            r, g, b = (0, 0, 0) if name == '__you__' else (0, 255, 0)
            self.players[name] = Player(
                name=name,
                location=MapPoint(x=x, y=y, z=z, r=r, g=g, b=b),
                time_stamp=time_stamp,
            )
        else:
            self.players[name].previous_location = self.players[name].location
            self.players[name].location = MapPoint(x=x, y=y, z=z)
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
        spawn_point_menu = menu.addMenu('Spawn Point')
        spawn_point_create = spawn_point_menu.addAction('Create on Cursor')
        spawn_point_delete = spawn_point_menu.addAction('Delete on Cursor')
        spawn_point_delete_all = spawn_point_menu.addAction('Delete All')
        way_point_menu = menu.addMenu('Way Point')
        way_point_create = way_point_menu.addAction('Create on Cursor')
        way_point_delete = way_point_menu.addAction('Clear')
        show_menu = menu.addMenu('Show')
        show_poi = show_menu.addAction('Points of Interest')
        show_poi.setCheckable(True)
        auto_follow = menu.addAction('Auto Follow')
        auto_follow.setCheckable(True)
        if config.data['maps']['show_poi']:
            show_poi.setChecked(True)
        if config.data['maps']['auto_follow']:
            auto_follow.setChecked(True)
        load_map = menu.addAction('Load Map')

        # execute
        action = menu.exec_(self.mapToGlobal(event.pos()))

        # parse response

        if action == spawn_point_create:
            spawn_time = text_time_to_seconds('6:40')
            dialog = QInputDialog(self)
            dialog.setWindowTitle('Create Spawn Point')
            dialog.setLabelText('Respawn Time (hh:mm:ss):')
            dialog.setTextValue('6:40')

            if dialog.exec_():
                spawn_time = text_time_to_seconds(dialog.textValue())
            dialog.deleteLater()

            spawn = SpawnPointItem(
                location=MapPoint(x=pos.x(), y=pos.y()),
                length=spawn_time
            )

            self._scene.addItem(spawn)
            self.map_spawn_points.append(spawn)
            spawn.start()

        if action == spawn_point_delete:
            pixmap = self._scene.itemAt(
                pos.x(), pos.y(), QTransform())
            if pixmap:
                group = pixmap.parentItem()
                if group:
                    self.map_spawn_points.remove(group)
                    self._scene.removeItem(group)

        if action == spawn_point_delete_all:
            for spawn_point in self.map_spawn_points:
                self._scene.removeItem(spawn_point)
            self.map_spawn_points = []

        if action == show_poi:
            config.data['maps']['show_poi'] = show_poi.isChecked()
            config.save()

        if action == way_point_create:
            if self.map_way_point:
                self._scene.removeItem(self.map_way_point.line)
                self._scene.removeItem(self.map_way_point.pixmap)
            pixmap = QGraphicsPixmapItem(QPixmap('data/maps/waypoint.png'))
            pixmap.setOffset(-10, -20)
            pixmap.setZValue(21)
            wp_x = pos.x()
            wp_y = pos.y()
            pixmap.setPos(wp_x, wp_y)
            line = QGraphicsLineItem(0.0, 0.0, wp_x, wp_y)
            line.setVisible(False)
            line.setZValue(20)
            self.map_way_point = WayPoint(
                line=line, pixmap=pixmap, x=wp_x, y=wp_y)
            self._scene.addItem(self.map_way_point.line)
            self._scene.addItem(self.map_way_point.pixmap)

        if action == way_point_delete:
            if self.map_way_point:
                self._scene.removeItem(self.map_way_point.line)
                self._scene.removeItem(self.map_way_point.pixmap)
            self.map_way_point = None

        if action == auto_follow:
            config.data['maps']['auto_follow'] = True if action.isChecked(
            ) else False
            config.save()

        if action == load_map:
            dialog = QInputDialog(self)
            dialog.setWindowTitle('Load Map')
            dialog.setLabelText('Select map to load:')
            dialog.setComboBoxItems(
                sorted([map.title() for map in self.map_data.map_zone_keys.keys()]))
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
        self.map_zone_keys = {}
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
                self.map_zone_keys[values[0].strip()] = values[1].strip()

    def load_map_data(self):
        # Get list of all map files for current zone
        base_map_name = self.map_zone_keys[self.map_name.strip().lower()]
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
                                color=Color(r=int(float(data[3])), g=int(
                                    float(data[4])), b=int(float(data[5]))),
                                size=int(float(data[6])),
                                text=str(data[7])
                            )
                        )
                    else:
                        pass  # Do not add to list

        # Setup Grid Size
        lowest_x, highest_x = min(x_list), max(x_list)
        lowest_y, highest_y = min(y_list), max(y_list)
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
        self.name = ''
        self.location = MapPoint()
        self.previous_location = MapPoint()
        self.timestamp = None  # datetime
        self.__dict__.update(kwargs)


class MapPoint:
    def __init__(self, **kwargs):
        self.x = 0
        self.y = 0
        self.z = 0
        self.color = Color()
        self.size = 0
        self.text = ''
        self.__dict__.update(kwargs)


class Color:
    def __init__(self, **kwargs):
        self.r = 255
        self.g = 255
        self.b = 255
        self.a = 255
        self.__dict__.update(kwargs)


class WayPoint:
    def __init__(self, **kwargs):
        self.location = MapPoint()
        self.line = None
        self.pixmap = None
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
        self.lowest_x = 0
        self.highest_x = 0
        self.lowest_y = 0
        self.highest_y = 0
        self.center_x = 0
        self.center_y = 0
        self.width = 0
        self.height = 0
        self.__dict__.update(kwargs)


class SpawnPointItem(QGraphicsItemGroup):

    def __init__(self, name=None, location=MapPoint(), length=None):
        super().__init__()
        self.location = location
        self.length = length if length else 10
        self.name = name if name else 'SPAWN'
        self.setToolTip(name)

        self._setup_ui()

        self.timer = QTimer()

    def _setup_ui(self):
        pixmap = QGraphicsPixmapItem(QPixmap('data/maps/spawn.png'))
        pixmap.setPos(self.location.x, self.location.y)
        pixmap.setOffset(-10, -10)
        text = QGraphicsTextItem('0')

        self.addToGroup(pixmap)
        self.addToGroup(text)

        self.setZValue(15)

        self.pixmap = pixmap
        self.text = text

    def _update(self):
        if self.timer:
            remaining = self._end_time - datetime.datetime.now()
            remaining_seconds = remaining.total_seconds()
            if remaining_seconds < 0:
                self.stop()
            elif remaining_seconds <= 30:
                self.text.setHtml(
                    "<font color='red' size='5'>{}</font>".format(
                        format_time(remaining))
                )
            else:
                self.text.setHtml(
                    "<font color='white'>{}</font>".format(
                        format_time(remaining))
                )
            self.realign()

            if remaining_seconds > 0 and self.timer:
                self.timer.singleShot(1000, self._update)

    def realign(self):
        self.text.setPos(
            self.location.x -
            self.text.boundingRect().width() / 2 *
            self.text.scale(),
            self.location.y + 5 * self.text.scale()
        )

    def start(self, _=None, timestamp=None):
        timestamp = timestamp if timestamp else datetime.datetime.now()
        self._end_time = timestamp + datetime.timedelta(seconds=self.length)
        if self.timer:
            self._update()

    def stop(self):
        self.text.setHtml(
            "<font color='green'>{}</font>".format(self.name.upper()))

    def mouseDoubleClickEvent(self, _):
        self.start()
