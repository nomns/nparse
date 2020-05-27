from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QTransform
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QInputDialog, QMenu

from utils import to_range, text_time_to_seconds, get_line_length
from config import profile

from .mapclasses import MapPoint, WayPoint, Player, SpawnPoint, MouseLocation
from .mapdata import MapData


class MapCanvas(QGraphicsView):
    """Map Widget for Everquest Map Files."""

    def __init__(self):

        self._data = None
        # UI Init
        super().__init__()
        self.setObjectName("MapCanvas")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setContentsMargins(0, 0, 0, 0)
        self.setTransformationAnchor(self.AnchorViewCenter)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRenderHint(QPainter.Antialiasing)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._scale = profile.maps.scale
        self._mouse_location = MouseLocation()
        self._z_index = 0

    def load_map(self, map_name):

        try:
            map_data = MapData(str(map_name))

        except:
            pass

        else:
            # compare size of both maps and adjust ratio appropriately
            if self._data:  # if _data exists, a zone has already been loaded
                g = self._data.geometry
                new_g = map_data.geometry
                ratio_adjustment = get_line_length(
                    g.lowest_x, g.lowest_y, g.highest_x, g.highest_y
                ) / get_line_length(
                    new_g.lowest_x, new_g.lowest_y, new_g.highest_x, new_g.highest_y
                )
                self._scale *= ratio_adjustment

            self._data = map_data
            self._scene.clear()
            self._z_index = 0
            self._draw()
            rect = self._scene.sceneRect()
            rect.adjust(
                -self._data.geometry.width * 2,
                -self._data.geometry.height * 2,
                self._data.geometry.width * 2,
                self._data.geometry.height * 2,
            )
            self.setSceneRect(rect)
            self.update()
            self.update_()

            self.centerOn(self._data.geometry.center_x, self._data.geometry.center_y)
            self._mouse_location = MouseLocation()
            self._scene.addItem(self._mouse_location)
            profile.maps.last_zone = self._data.zone

    def _draw(self):
        for z in self._data.keys():
            self._scene.addItem(self._data[z]["paths"])
            for p in self._data[z]["poi"]:
                self._scene.addItem(p.text)

        self._scene.addItem(self._data.grid)

    def update_(self, ratio=None):
        if not ratio:
            ratio = self._scale

        current_alpha = profile.maps.current_z_alpha / 100
        other_alpha = profile.maps.other_z_alpha / 100
        closest_alpha = profile.maps.closest_z_alpha / 100

        # scene
        self.setTransform(QTransform())  # reset transform object
        self._scale = to_range(ratio, 0.0006, 5.0)
        profile.maps.scale = self._scale
        self.scale(self._scale, self._scale)

        # lines and points of interest
        current_z_level = self._data.geometry.z_groups[self._z_index]
        closest_z_levels = set()
        for x in [i for i in [self._z_index - 1, self._z_index + 1] if i > -1]:
            try:
                closest_z_levels.add(self._data.geometry.z_groups[x])
            except:
                pass

        for z in self._data.keys():
            alpha = current_alpha
            if profile.maps.use_z_layers:
                if z == current_z_level:
                    alpha = current_alpha
                elif z in closest_z_levels:
                    alpha = closest_alpha
                else:
                    alpha = other_alpha
            # lines
            bolded = 0.5 if profile.maps.use_z_layers else 0.0
            for path in self._data[z]["paths"].childItems():
                if z == current_z_level or not profile.maps.use_z_layers:
                    pen = path.pen()
                    pen.setWidth(
                        max(
                            profile.maps.line_width + bolded,
                            (profile.maps.line_width + bolded) / self._scale,
                        )
                    )
                    path.setPen(pen)
                else:
                    pen = path.pen()
                    pen.setWidth(
                        max(
                            profile.maps.line_width - 0.8,
                            (profile.maps.line_width - 0.8) / self._scale,
                        )
                    )
                    path.setPen(pen)

            self._data[z]["paths"].setOpacity(alpha)

            # points of interest
            for p in self._data[z]["poi"]:
                p.update_(min(5, self.to_scale()))
                if not profile.maps.show_poi:
                    p.text.setOpacity(0)
                elif profile.maps.use_z_layers:
                    if z == current_z_level:
                        p.text.setOpacity(current_alpha)
                    else:
                        p.text.setOpacity(other_alpha)
                else:
                    p.text.setOpacity(current_alpha)

        # players
        for player in self._data.players.values():
            player.update_(self.to_scale())
            if profile.maps.use_z_layers:
                if player.z_level == current_z_level:
                    player.setOpacity(current_alpha)
                else:
                    player.setOpacity(other_alpha)
            else:
                player.setOpacity(current_alpha)

        # waypoint
        if self._data.way_point:
            self._data.way_point.update_(self.to_scale())
            if profile.maps.use_z_layers:
                self._data.way_point.pixmap.setOpacity(
                    current_alpha
                    if (self._data.way_point.location.z == current_z_level)
                    else other_alpha
                )
                player = self._data.players.get("__you__", None)
                if player and current_z_level in [
                    self._data.way_point.location.z,
                    player.z_level,
                ]:
                    self._data.way_point.line.setOpacity(current_alpha)
                else:
                    self._data.way_point.line.setOpacity(other_alpha)

            else:
                self._data.way_point.pixmap.setOpacity(current_alpha)

        # spawns
        for spawn in self._data.spawns:
            spawn.setScale(self.to_scale())
            spawn.realign(self.to_scale())
            if profile.maps.use_z_layers:
                spawn.setOpacity(
                    current_alpha
                    if (spawn.location.z == current_z_level)
                    else other_alpha
                )
            else:
                spawn.setOpacity(current_alpha)

        # grid lines
        if profile.maps.show_grid:
            pen = self._data.grid.pen()
            pen.setWidth(
                max(
                    profile.maps.grid_line_width,
                    self.to_scale(profile.maps.grid_line_width),
                )
            )
            self._data.grid.setPen(pen)
            self._data.grid.setVisible(True)
        else:
            self._data.grid.setVisible(False)

    def to_scale(self, float_value=1.0):
        return float_value / self._scale

    def center(self):
        player = None
        if self._data:
            player = self._data.players.get("__you__", None)
        if profile.maps.auto_follow and player:
            self.centerOn(player.location.x, player.location.y)

    def add_player(self, name, timestamp, location):
        if name not in self._data.players.keys():
            self._data.players[name] = Player(
                name=name, location=location, timestamp=timestamp
            )
            self._scene.addItem(self._data.players[name])
        else:
            self._data.players[name].previous_location = self._data.players[
                name
            ].location
            self._data.players[name].location = location
            self._data.players[name].timestamp = timestamp
        self._data.players[name].z_level = self._data.get_closest_z_group(
            self._data.players[name].location.z
        )

        if name == "__you__" and profile.maps.use_z_layers:
            self._z_index = self._data.geometry.z_groups.index(
                self._data.get_closest_z_group(self._data.players["__you__"].location.z)
            )

        self.update_()

        if self._data.way_point and name == "__you__":
            self._data.way_point.update_(self.to_scale(), location=location)

        if name == "__you__" and profile.maps.auto_follow:
            self.center()

    def enterEvent(self, event):
        if profile.maps.show_mouse_location:
            self._mouse_location.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._mouse_location.setVisible(False)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self._mouse_location.set_value(self.mapToScene(event.pos()), self._scale, self)
        QGraphicsView.mouseMoveEvent(self, event)

    def wheelEvent(self, event):
        # Scale based on scroll wheel direction
        movement = event.angleDelta().y()
        if self.dragMode() == self.NoDrag:
            if movement > 0:
                self.update_(self._scale + self._scale * 0.1)
            else:
                self.update_(self._scale - self._scale * 0.1)
        else:
            if self._data:
                if movement > 0:
                    self._z_index = max(self._z_index - 1, 0)
                else:
                    self._z_index = min(
                        self._z_index + 1, len(self._data.geometry.z_groups) - 1
                    )
                self.update_()

        # Update Mouse Location
        self._mouse_location.set_value(self.mapToScene(event.pos()), self._scale, self)

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
        QGraphicsView.resizeEvent(self, event)

    def contextMenuEvent(self, event):
        # create menu
        pos = self.mapToScene(event.pos())
        menu = QMenu(self)
        # remove from memory after usage
        menu.setAttribute(Qt.WA_DeleteOnClose)  # remove from memory
        spawn_point_menu = menu.addMenu("Spawn Point")
        spawn_point_create = spawn_point_menu.addAction("Create on Cursor")
        spawn_point_delete = spawn_point_menu.addAction("Delete on Cursor")
        spawn_point_delete_all = spawn_point_menu.addAction("Delete All")
        way_point_menu = menu.addMenu("Way Point")
        way_point_create = way_point_menu.addAction("Create on Cursor")
        way_point_delete = way_point_menu.addAction("Clear")
        load_map = menu.addAction("Load Map")

        # execute
        action = menu.exec_(self.mapToGlobal(event.pos()))

        # parse response

        if action == spawn_point_create:
            spawn_time = text_time_to_seconds("6:40")
            dialog = QInputDialog(self)
            dialog.setWindowTitle("Create Spawn Point")
            dialog.setLabelText("Respawn Time (hh:mm:ss):")
            dialog.setTextValue("6:40")

            if dialog.exec_():
                spawn_time = text_time_to_seconds(dialog.textValue())
            dialog.deleteLater()

            spawn = SpawnPoint(
                location=MapPoint(
                    x=pos.x(), y=pos.y(), z=self._data.geometry.z_groups[self._z_index]
                ),
                length=spawn_time,
            )

            self._scene.addItem(spawn)
            self._data.spawns.append(spawn)
            spawn.start()

        if action == spawn_point_delete:
            pixmap = self._scene.itemAt(pos.x(), pos.y(), QTransform())
            if pixmap:
                group = pixmap.parentItem()
                if group:
                    self._data.spawns.remove(group)
                    self._scene.removeItem(group)

        if action == spawn_point_delete_all:
            for spawn in self._data.spawns:
                self._scene.removeItem(spawn)
            self._data.spawns = []

        if action == way_point_create:
            if self._data.way_point:
                self._scene.removeItem(self._data.way_point.pixmap)
                self._scene.removeItem(self._data.way_point.line)
                self._data.way_point = None

            self._data.way_point = WayPoint(
                location=MapPoint(
                    x=pos.x(), y=pos.y(), z=self._data.geometry.z_groups[self._z_index]
                )
            )

            self._scene.addItem(self._data.way_point.pixmap)
            self._scene.addItem(self._data.way_point.line)

        if action == way_point_delete:
            if self._data.way_point:
                self._scene.removeItem(self._data.way_point.pixmap)
                self._scene.removeItem(self._data.way_point.line)
            self._data.way_point = None

        if action == load_map:
            dialog = QInputDialog(self)
            dialog.setWindowTitle("Load Map")
            dialog.setLabelText("Select map to load:")
            dialog.setComboBoxItems(
                sorted([map.title() for map in MapData.get_zone_dict().keys()])
            )
            if dialog.exec_():
                self.load_map(dialog.textValue().lower())
            dialog.deleteLater()

        self.update_()
