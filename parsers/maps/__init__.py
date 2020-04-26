from .mapdata import MapData  # noqa: F401

from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

from helpers import config, to_real_xy
from widgets.nwindow import NWindow

from .mapcanvas import MapCanvas
from .mapclasses import MapPoint


class Maps(NWindow):

    def __init__(self):
        super().__init__(transparent=False)
        self.name = 'maps'
        self.set_title(self.name.title())
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
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

    def parse(self, timestamp, text):
        if text[:23] == 'LOADING, PLEASE WAIT...':
            pass
        if text[:16] == 'You have entered':
            self._map.load_map(text[17:-1])
        if text[:16] == 'Your Location is':
            x, y, z = [float(value) for value in text[17:].strip().split(',')]
            x, y = to_real_xy(x, y)
            self._map.add_player('__you__', timestamp, MapPoint(x=x, y=y, z=z))

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
