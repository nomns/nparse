# testing
import traceback

import os

import pathvalidate
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QTransform, QColor, QPen, QAction
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QInputDialog,
                             QMenu, QLineEdit, QGraphicsPathItem)

from helpers import config, to_range, text_time_to_seconds

from .mapclasses import (MapPoint, WayPoint, Player, SpawnPoint, MouseLocation,
                         PointOfInterest, UserWaypoint)
from .mapdata import MapData, MAP_FILES_PATHLIB, ICON_MAP


class MapCanvas(QGraphicsView):
    """Map Widget for Everquest Map Files."""

    def __init__(self):

        self._data = None
        # UI Init
        super().__init__()
        self.setObjectName('MapCanvas')
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContentsMargins(0, 0, 0, 0)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._scale = config.data['maps']['scale']
        self._mouse_location = MouseLocation()
        self._path_recording = False
        self._path_recording_name = ""
        self._path_file = None
        self._path_last_loc = None

    def load_map(self, map_name):
        try:
            map_data = MapData(str(map_name))

        except:
            traceback.print_exc()

        else:
            self._data = map_data
            self._scene.clear()
            self._z_index = 0
            self._draw()
            rect = self._scene.sceneRect()
            rect.adjust(-self._data.geometry.width * 2, -self._data.geometry.height * 2,
                        self._data.geometry.width * 2, self._data.geometry.height * 2)
            self.setSceneRect(rect)
            self.update()
            self.update_()

            self.centerOn(
                self._data.geometry.center_x,
                self._data.geometry.center_y
            )
            self._mouse_location = MouseLocation()
            self._scene.addItem(self._mouse_location)
            config.data['maps']['last_zone'] = self._data.zone
            config.save()

    def _draw(self):
        for z in self._data.keys():
            self._scene.addItem(self._data[z]['paths'])
            for p in self._data[z]['poi']:
                self._scene.addItem(p.text)

        self._scene.addItem(self._data.grid)

    def update_(self, ratio=None):
        if not ratio:
            ratio = self._scale

        current_alpha = config.data['maps']['current_z_alpha'] / 100
        other_alpha = config.data['maps']['other_z_alpha'] / 100
        closest_alpha = config.data['maps']['closest_z_alpha'] / 100

        # scene
        self.setTransform(QTransform())  # reset transform object
        self._scale = to_range(ratio, 0.0006, 5.0)
        config.data['maps']['scale'] = self._scale
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
            if config.data['maps']['use_z_layers']:
                if z == current_z_level:
                    alpha = current_alpha
                elif z in closest_z_levels:
                    alpha = closest_alpha
                else:
                    alpha = other_alpha
            # lines
            bolded = 0.5 if config.data['maps']['use_z_layers'] else 0.0
            for path in self._data[z]['paths'].childItems():
                if z == current_z_level or not config.data['maps']['use_z_layers']:
                    pen = path.pen()
                    pen.setWidth(int(max(
                        config.data['maps']['line_width'] + bolded,
                        (config.data['maps']['line_width'] +
                         bolded) / self._scale
                    )))
                    path.setPen(pen)
                else:
                    pen = path.pen()
                    pen.setWidth(int(max(
                        config.data['maps']['line_width'] - 0.8,
                        (config.data['maps']['line_width'] - 0.8) / self._scale
                    )))
                    path.setPen(pen)

            self._data[z]['paths'].setOpacity(alpha)

            # points of interest
            for p in self._data[z]['poi']:
                p.update_(min(5, self.to_scale()))
                if not config.data['maps']['show_poi']:
                    p.text.setOpacity(0)
                elif config.data['maps']['use_z_layers']:
                    if z == current_z_level:
                        p.text.setOpacity(current_alpha)
                    else:
                        p.text.setOpacity(other_alpha)
                else:
                    p.text.setOpacity(current_alpha)

        # players
        for player in self._data.players.values():
            player.update_(self.to_scale())
            if config.data['maps']['use_z_layers']:
                if player.z_level == current_z_level:
                    player.setOpacity(current_alpha)
                else:
                    player.setOpacity(other_alpha)
            else:
                player.setOpacity(current_alpha)

        # waypoint
        if self._data.way_point:
            self._data.way_point.update_(self.to_scale())
            if config.data['maps']['use_z_layers']:
                self._data.way_point.pixmap.setOpacity(
                    current_alpha if (self._data.way_point.location.z ==
                                      current_z_level) else other_alpha
                )
                player = self._data.players.get('__you__', None)
                if player and current_z_level in \
                        [self._data.way_point.location.z, player.z_level]:
                    self._data.way_point.line.setOpacity(current_alpha)
                else:
                    self._data.way_point.line.setOpacity(other_alpha)

            else:
                self._data.way_point.pixmap.setOpacity(current_alpha)

        # user waypoints
        for waypoint in self._data.waypoints.values():
            waypoint.update_(self.to_scale())
            if config.data['maps']['use_z_layers']:
                if waypoint.z_level == current_z_level:
                    waypoint.setOpacity(current_alpha)
                else:
                    waypoint.setOpacity(other_alpha)
            else:
                waypoint.setOpacity(current_alpha)

        # spawns
        for spawn in self._data.spawns:
            spawn.setScale(self.to_scale())
            spawn.realign(self.to_scale())
            if config.data['maps']['use_z_layers']:
                spawn.setOpacity(
                    current_alpha if (spawn.location.z ==
                                      current_z_level) else other_alpha
                )
            else:
                spawn.setOpacity(current_alpha)

        # grid lines
        if config.data['maps']['show_grid']:
            pen = self._data.grid.pen()
            pen.setWidth(int(max(
                config.data['maps']['grid_line_width'],
                self.to_scale(config.data['maps']['grid_line_width'])
            )))
            self._data.grid.setPen(pen)
            self._data.grid.setVisible(True)
        else:
            self._data.grid.setVisible(False)

    def to_scale(self, float_value=1.0):
        return float_value / self._scale

    def center(self):
        player = None
        if self._data:
            player = self._data.players.get('__you__', None)
        if config.data['maps']['auto_follow'] and player:
            self.centerOn(
                player.location.x,
                player.location.y
            )

    def remove_player(self, name):
        player = self._data.players.pop(name)
        if player:
            self._scene.removeItem(player)

    def add_player(self, name, timestamp, location):
        if name not in self._data.players:
            self._data.players[name] = Player(
                name=name,
                location=location,
                timestamp=timestamp)
            self._scene.addItem(self._data.players[name])
        else:
            self._data.players[name].previous_location = self._data.players[name].location
            self._data.players[name].location = location
            self._data.players[name].timestamp = timestamp
        self._data.players[name].z_level = self._data.get_closest_z_group(
            self._data.players[name].location.z
        )

        if name == '__you__' and config.data['maps']['use_z_layers']:
            self._z_index = self._data.geometry.z_groups.index(
                self._data.get_closest_z_group(
                    self._data.players['__you__'].location.z
                ))

        self.update_()

        if self._data.way_point and name == '__you__':
            self._data.way_point.update_(
                self.to_scale(),
                location=location
            )

        if name == '__you__' and config.data['maps']['auto_follow']:
            self.center()

    def remove_waypoint(self, name):
        waypoint = self._data.waypoints.pop(name)
        if waypoint:
            self._scene.removeItem(waypoint)

    def add_waypoint(self, name, location, icon):
        if name not in self._data.waypoints:
            self._data.waypoints[name] = UserWaypoint(
                name=name.rsplit(":", 1)[0],
                icon=ICON_MAP.get(icon, 'data/maps/waypoint.png'),
                location=location
            )
            self._scene.addItem(self._data.waypoints[name])

        self._data.waypoints[name].z_level = self._data.get_closest_z_group(
            self._data.waypoints[name].location.z
        )

        self.update_()

    def enterEvent(self, event):
        if config.data['maps']['show_mouse_location']:
            self._mouse_location.setVisible(True)
        QGraphicsView.enterEvent(self, event)

    def leaveEvent(self, event):
        self._mouse_location.setVisible(False)
        QGraphicsView.leaveEvent(self, event)

    def mouseMoveEvent(self, event):
        self._mouse_location.set_value(
            self.mapToScene(event.pos()),
            self._scale,
            self
            )
        QGraphicsView.mouseMoveEvent(self, event)

    def wheelEvent(self, event):
        # Scale based on scroll wheel direction
        movement = event.angleDelta().y()
        if self.dragMode() == QGraphicsView.DragMode.NoDrag:
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
                        self._z_index + 1, len(self._data.geometry.z_groups) - 1)
                self.update_()

        # Update Mouse Location
        mouse_pos = int(event.position().x()), int(event.position().y())
        self._mouse_location.set_value(
            self.mapToScene(*mouse_pos),
            self._scale,
            self
        )

    def keyPressEvent(self, event):
        # Enable drag mode while control button is being held down
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        # Disable drag mode when control button released
        if event.key() == Qt.Key.Key_Control:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        QGraphicsView.keyPressEvent(self, event)

    def resizeEvent(self, event):
        self.center()
        QGraphicsView.resizeEvent(self, event)

    def contextMenuEvent(self, event):
        # create menu
        pos = self.mapToScene(event.pos())
        menu = QMenu(self)
        # remove from memory after usage
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # remove from memory
        spawn_point_menu = menu.addMenu('Spawn Point')
        spawn_point_create = spawn_point_menu.addAction('Create on Cursor')
        spawn_point_delete = spawn_point_menu.addAction('Delete on Cursor')
        spawn_point_delete_all = spawn_point_menu.addAction('Delete All')
        way_point_menu = menu.addMenu('Way Point')
        way_point_create = way_point_menu.addAction('Create on Cursor')
        way_point_delete = way_point_menu.addAction('Clear')
        pathing_menu = menu.addMenu('Custom Pathing')
        pathing_start_recording = QAction('Start Recording')
        pathing_rename_recording = QAction('Rename Path')
        pathing_stop_recording = QAction('Stop Recording')
        if not self._path_recording:
            pathing_menu.addAction(pathing_start_recording)
        else:
            current = pathing_menu.addAction(self._path_recording_name)
            current.setEnabled(False)
            pathing_menu.addSeparator()
            pathing_menu.addAction(pathing_rename_recording)
            pathing_menu.addAction(pathing_stop_recording)
        load_map = menu.addAction('Load Map')

        # execute
        action = menu.exec(self.mapToGlobal(event.pos()))

        # parse response

        if action == spawn_point_create:
            dialog = QInputDialog(self)
            dialog.setWindowTitle('Create Spawn Point')
            dialog.setLabelText('Respawn Time (hh:mm:ss):')
            dialog.setTextValue(self._data.get_default_spawn_timer())

            if dialog.exec():
                spawn_time = text_time_to_seconds(dialog.textValue())
                spawn = SpawnPoint(
                    location=MapPoint(
                        x=pos.x(),
                        y=pos.y(),
                        z=self._data.geometry.z_groups[self._z_index]
                    ),
                    length=spawn_time
                )

                self._scene.addItem(spawn)
                self._data.spawns.append(spawn)
                spawn.start()
            dialog.deleteLater()

        if action == spawn_point_delete:
            pixmap = self._scene.itemAt(
                pos.x(), pos.y(), QTransform())
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
                    x=pos.x(),
                    y=pos.y(),
                    z=self._data.geometry.z_groups[self._z_index]
                )
            )

            self._scene.addItem(self._data.way_point.pixmap)
            self._scene.addItem(self._data.way_point.line)

        if action == way_point_delete:
            if self._data.way_point:
                self._scene.removeItem(self._data.way_point.pixmap)
                self._scene.removeItem(self._data.way_point.line)
            self._data.way_point = None

        if action == pathing_start_recording:
            self.start_path_recording()

        if action == pathing_rename_recording:
            self.rename_path_recording()

        if action == pathing_stop_recording:
            self.stop_path_recording()

        if action == load_map:
            dialog = QInputDialog(self)
            dialog.setStyleSheet("QFrame { background-color: #f0f0f0 }")
            dialog.setWindowTitle('Load Map')
            dialog.setLabelText('Select map to load:')
            dialog.setComboBoxItems(
                sorted([map.title() for map in MapData.get_zone_dict()]))
            if dialog.exec():
                self.load_map(dialog.textValue().lower())
            dialog.deleteLater()

        self.update_()

    def _get_path_filename(self, custom_name=None, relative=False):
        custom_name = custom_name or self._path_recording_name
        clean_name = pathvalidate.sanitize_filename(custom_name)
        clean_name = clean_name.replace(' ', '_')
        if relative:
            return clean_name
        zone_key = MapData.get_zone_dict().get(self._data.zone)
        filename = "{zone}_{recording}.txt".format(
            zone=zone_key,
            recording=clean_name)

        # Make sure the directory exists
        record_dir = MAP_FILES_PATHLIB.joinpath('recordings')
        if not os.path.exists(record_dir):
            try:
                print("Creating custom map directory.")
                os.makedirs(record_dir)
            except Exception as e:
                print("Failed to make custom map directory: %s" % e)
        return record_dir.joinpath(filename)

    def start_path_recording(self, name=None):
        print("Start recording!")
        if self._path_recording:
            return

        if name:
            path_name = name
            ok_pressed = True
        else:
            path_name, ok_pressed = QInputDialog.getText(
                self,  # parent
                "Start Recording Path",  # title
                "Name of path to record:",  # label
                echo=QLineEdit.EchoMode.Normal,
                text="")
        if ok_pressed:
            self._path_recording_name = path_name
            try:
                self._path_file = open(self._get_path_filename(), 'a')
                self._path_recording = True
                self._path_last_loc = None
            except Exception as e:
                print("Failed to open pathfile: %s" % e)

    def rename_path_recording(self, new_name=None):
        print("Rename recording!")
        if not self._path_recording:
            return

        if new_name:
            path_name = new_name
            ok_pressed = True
        else:
            path_name, ok_pressed = QInputDialog.getText(
                self,  # parent
                "Rename Path",  # title
                "New path name:",  # label
                echo=QLineEdit.EchoMode.Normal,
                text=self._path_recording_name)

        if ok_pressed:
            old_path_name = self._path_recording_name
            new_path_name = path_name
            try:
                self._path_file.close()
                self._path_file = None
            except Exception as e:
                print("Failed to close path recording file: %s" % e)
                return
            try:
                os.rename(self._get_path_filename(custom_name=old_path_name),
                          self._get_path_filename(custom_name=new_path_name))
                self._path_recording_name = new_path_name
            except Exception as e:
                print("Failed to rename path recording file: %s" % e)
                self._path_recording = False
                return
            try:
                self._path_file = open(self._get_path_filename(), 'a')
            except Exception as e:
                print("Failed to open renamed path recording file: %s" % e)
                self._path_recording = False
                return

    def stop_path_recording(self):
        print("Stop recording!")
        if not self._path_recording:
            return

        if self._path_last_loc is not None:
            print("Recording final path point.")
            self.record_path_point(
                self._path_last_loc, "%s (end)" % self._path_recording_name)

        try:
            self._path_file.close()
        except Exception as e:
            print("Failed to stop recording: %s" % e)
            return
        self._path_file = None
        self._path_recording = False
        self._path_last_loc = None

    def record_path_loc(self, loc):
        if not self._path_recording:
            return

        print("Recording loc: %s" % str(loc))
        if self._path_last_loc is None:
            print("Recording first path point.")
            self.record_path_point(
                loc, "%s (start)" % self._path_recording_name)
        else:
            line = (
                "L {x1}, {y1}, {z1}, {x2}, {y2}, {z2}, {r}, {g}, {b}\n".format(
                    x1=self._path_last_loc[0],
                    y1=self._path_last_loc[1],
                    z1=self._path_last_loc[2],
                    x2=loc[0], y2=loc[1], z2=loc[2],
                    r=255, g=0, b=0
                ))
            try:
                self._path_file.write(line)
                self._path_file.flush()
            except Exception as e:
                print("Failed to write loc to pathfile: %s" % e)

            # Also add line to the active map
            z_group = self._data.get_closest_z_group(loc[2])
            color = MapData.color_transform(QColor(255, 0, 0))
            map_line = QGraphicsPathItem()
            map_line.setPen(
                QPen(color, config.data['maps']['line_width']))
            map_path = map_line.path()
            map_path.moveTo(self._path_last_loc[0], self._path_last_loc[1])
            map_path.lineTo(loc[0], loc[1])
            map_line.setPath(map_path)
            self._data[z_group]['paths'].addToGroup(map_line)
            self.update_()

        # Update past loc to current loc
        self._path_last_loc = loc

    def record_path_point(self, loc, desc):
        if not self._path_recording:
            return
        point = "P {x}, {y}, {z}, {r}, {g}, {b}, {size}, {desc}\n".format(
            x=loc[0], y=loc[1], z=loc[2],
            r=255, g=0, b=0,
            size=3, desc=desc
        )
        try:
            self._path_file.write(point)
            self._path_file.flush()
        except Exception as e:
            print("Failed to write point to pathfile: %s" % e)

        # Also add point to the active map
        z_group = self._data.get_closest_z_group(loc[2])
        color = MapData.color_transform(QColor(255, 0, 0))
        map_poi = MapPoint(
            x=loc[0], y=loc[1], z=loc[2],
            color=color, size=3, text=desc)
        self._data[z_group]['poi'].append(
            PointOfInterest(location=map_poi))
        self._draw()
        self.update_()
