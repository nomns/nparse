from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF
from PyQt5.QtGui import (QPen, QColor, QTransform, QPainterPath, QPainter,
                         QFont)
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem,
                             QGraphicsRectItem, QGraphicsTextItem,
                             QGraphicsEllipseItem)
from maps.mapdata import MapData
import settings
from maps.player import Player


class MapCanvas(QGraphicsView):

    def __init__(self):
        # UI Init
        super(QGraphicsView, self).__init__()
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(
            'QGraphicsView { background-color: rgba(0, 0, 0, 255); }'
        )
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
        self.players = {}

        # Application Settings
        self.settings = settings.Settings('parse99')

    def load_map(self, map_name):
        self._scene.clear()
        self.map_data = MapData(map_name)
        self.create_grid_lines()
        self.create_map_lines()
        self.create_map_points()
        self.update_players()
        self.set_scene_padding(self.map_data.map_grid_geometry.width,
                               self.map_data.map_grid_geometry.height)
        self.draw()
        self.centerOn(0, 0)

    def create_grid_lines(self):
        grid_line_width = self.settings.get_value('maps', 'grid_line_width')
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
        map_line_width = self.settings.get_value('maps', 'map_line_width')
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
        circle_size = max(10, 10 / self.scale_ratio)

        # Draw and/or update all players in players
        for player in player_list_set:
            player_data = self.players[player]
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
        map_line_width = self.settings.get_value('maps', 'map_line_width')
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
        grid_line_width = self.settings.get_value('maps', 'grid_line_width')
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

    def set_scene_padding(self, padding_x, padding_y):
        # Make it so that if you are zoomed out, you can still
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
        if self.settings.get_value('maps', 'center_on') == 'player':
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
        return QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        # Disable drag mode when control button released
        if event.key() == Qt.Key_Control:
            self.setDragMode(self.NoDrag)
        return QGraphicsView.keyPressEvent(self, event)

    def resizeEvent(self, event):
        self.center()
        return QGraphicsView.resizeEvent(self, event)
