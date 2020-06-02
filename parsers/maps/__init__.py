from .mapdata import MapData  # noqa: F401

from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

from utils import to_real_xy
from widgets import NWindow
from config import profile

from .mapcanvas import MapCanvas
from .mapclasses import MapPoint


class Maps(NWindow):
    def __init__(self):
        super().__init__(name="maps", transparent=False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.set_title(profile.maps.last_zone.title())
        # interface
        self._map = MapCanvas()
        self.content.addWidget(self._map, 1)
        # buttons
        button_layout = QHBoxLayout()
        show_poi = QPushButton("\u272a")
        show_poi.setCheckable(True)
        show_poi.setChecked(profile.maps.show_poi)
        show_poi.setToolTip("Show Points of Interest")
        show_poi.clicked.connect(self._toggle_show_poi)
        button_layout.addWidget(show_poi)
        auto_follow = QPushButton("\u25CE")
        auto_follow.setCheckable(True)
        auto_follow.setChecked(profile.maps.auto_follow)
        auto_follow.setToolTip("Auto Center")
        auto_follow.clicked.connect(self._toggle_auto_follow)
        button_layout.addWidget(auto_follow)
        toggle_z_layers = QPushButton("\u24CF")
        toggle_z_layers.setCheckable(True)
        toggle_z_layers.setChecked(profile.maps.use_z_layers)
        toggle_z_layers.setToolTip("Show Z Layers")
        toggle_z_layers.clicked.connect(self._toggle_z_layers)
        button_layout.addWidget(toggle_z_layers)
        show_grid_lines = QPushButton("#")
        show_grid_lines.setCheckable(True)
        show_grid_lines.setChecked(profile.maps.show_grid)
        show_grid_lines.setToolTip("Show Grid")
        show_grid_lines.clicked.connect(self._toggle_show_grid)
        button_layout.addWidget(show_grid_lines)
        show_mouse_location = QPushButton("\U0001F6C8")
        show_mouse_location.setCheckable(True)
        show_mouse_location.setChecked(profile.maps.show_mouse_location)
        show_mouse_location.setToolTip("Show Loc Under Mouse Pointer")
        show_mouse_location.clicked.connect(self._toggle_show_mouse_location)
        button_layout.addWidget(show_mouse_location)

        self.menu_area.addLayout(button_layout)

        if profile.maps.last_zone:
            self._map.load_map(profile.maps.last_zone)
        else:
            self._map.load_map("west freeport")

    def parse(self, timestamp, text):
        if text[:23] == "LOADING, PLEASE WAIT...":
            pass
        if text[:16] == "You have entered":
            self.set_title(text[17:-1])
            self._map.load_map(text[17:-1])
        if text[:16] == "Your Location is":
            x, y, z = [float(value) for value in text[17:].strip().split(",")]
            x, y = to_real_xy(x, y)
            self._map.add_player("__you__", timestamp, MapPoint(x=x, y=y, z=z))

    # events
    def _toggle_show_poi(self, _):
        profile.maps.show_poi = not profile.maps.show_poi
        self._map.update_()

    def _toggle_auto_follow(self, _):
        profile.maps.auto_follow = not profile.maps.auto_follow
        self._map.center()

    def _toggle_z_layers(self, _):
        profile.maps.use_z_layers = not profile.maps.use_z_layers
        self._map.update_()

    def _toggle_show_grid(self, _):
        profile.maps.show_grid = not profile.maps.show_grid
        self._map.update_()

    def _toggle_show_mouse_location(self,):
        profile.maps.show_mouse_location = not profile.maps.show_mouse_location

    def settings_updated(self):
        super().settings_updated()
        if profile.maps.last_zone:
            self._map.load_map(profile.maps.last_zone)
