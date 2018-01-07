from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QGridLayout, QHBoxLayout, QPushButton,
                             QButtonGroup, QComboBox, QListView)

from maps.mapcanvas import MapCanvas
from maps.mapdata import MapData


class Maps(QWidget):

    def __init__(self, settings):
        # Settings
        self.settings = settings

        # Class Init
        self._active = False
        self.map_pairs = MapData(None).map_pairs

        # UI Init
        super(QWidget, self).__init__()
        self.setWindowTitle("Map")
        self.setWindowIcon(QIcon('ui/icon.png'))
        self.setWindowFlags(Qt.WindowStaysOnTopHint |
                            Qt.WindowCloseButtonHint |
                            Qt.FramelessWindowHint |
                            Qt.WindowMinMaxButtonsHint)
        self.borderless = True
        if self.settings.get_value('maps', 'geometry') is not None:
            self.setGeometry(
                self.settings.get_value('maps', 'geometry')
            )
        else:
            self.setGeometry(100, 100, 400, 400)
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.map_canvas = MapCanvas()
        self.grid.addWidget(self.map_canvas, 1, 0, 1, 1)
        self.setLayout(self.grid)
        self.setWindowOpacity(0.85)

        # Menu
        self.menu_container = QWidget()
        self.menu_container.setObjectName('menu_container')
        self.menu = QHBoxLayout()
        self.menu_container.setLayout(self.menu)
        self.menu.setSpacing(5)
        self.menu.setContentsMargins(0, 0, 0, 0)
        self.create_menu_buttons()
        self.grid.addWidget(self.menu_container, 0, 0, 1, 1)

        # Testing
        self.toggle()
        self.map_canvas.load_map('The Overthere')

    def create_menu_buttons(self):
        # Center on Player Button
        button_center_player = QPushButton(
            QIcon('ui/gfx/map_menu_center_player.png'),
            ''
        )
        button_center_player.setCheckable(True)  # Make toggle button
        button_center_player.setToolTip('Center on Player')
        button_center_player.setObjectName('button_center_player')
        # Center on Last Point Button
        button_center_point = QPushButton(
            QIcon('ui/gfx/map_menu_center_map.png'),
            ''
        )
        button_center_point.setCheckable(True)  # Make toggle button
        button_center_point.setToolTip('Center Normally')
        button_center_point.setObjectName('button_center_point')
        # Create Button Group for Exclusive Toggling
        toggle_group = QButtonGroup(self)
        toggle_group.addButton(button_center_player, 1)
        toggle_group.addButton(button_center_point, 2)
        toggle_group.buttonClicked.connect(self.center_button_toggled)
        self.menu.addWidget(button_center_player)
        self.menu.addWidget(button_center_point)

        # Apply settings for current toggle
        if self.settings.get_value('maps', 'center_on') == 'point':
            button_center_point.setChecked(True)
        else:
            button_center_player.setChecked(True)

        # Fit to Window Button
        button_fit_window = QPushButton(
            QIcon('ui/gfx/map_menu_fit_window.png'),
            ''
        )
        button_fit_window.setToolTip('Fit Map to Window')
        button_fit_window.clicked.connect(self.fit_to_window)
        self.menu.addWidget(button_fit_window, 0, Qt.AlignLeft)

        # Maps Combo Box
        self.combo_load_map = QComboBox(self)
        # Need to setView otherwise CSS doesn't work
        self.combo_load_map.setView(QListView())
        self.combo_load_map.setToolTip('Manually Load Selected Map')
        for map_name in sorted(self.map_pairs.keys(), key=str.lower):
            self.combo_load_map.addItem(map_name)
        self.combo_load_map.currentIndexChanged.connect(
            self.load_map_from_combo
        )
        self.menu.addWidget(self.combo_load_map, 0, Qt.AlignLeft)
        button_borderless_toggle = QPushButton(
            QIcon('ui/gfx/map_menu_borderless_toggle.png'),
            ''
        )
        button_borderless_toggle.setToolTip('Toggle Borderless Window')
        button_borderless_toggle.clicked.connect(self.toggle_borderless)
        self.menu.addWidget(
            button_borderless_toggle,
            0,
            Qt.AlignRight
        )

    def load_map_from_combo(self, widget):
        self.map_canvas.load_map(
            self.combo_load_map.currentText().strip()
        )
        self.fit_to_window(False)

    def fit_to_window(self, button):
        # Can't use QGraphicsView().fitInView because of scaling issues.
        # So calculate scale and use the lesser numeric scale to fit window
        # Use 0.9 against width/height to create a 10% border around map
        x_scale = self.map_canvas.geometry().width() * 0.9 \
            / self.map_canvas.map_data.map_grid_geometry.width
        y_scale = self.map_canvas.geometry().height() * 0.9 \
            / self.map_canvas.map_data.map_grid_geometry.height
        if x_scale <= y_scale:
            self.map_canvas.set_scale(x_scale)
        else:
            self.map_canvas.set_scale(y_scale)
        # Center Map on middle of map
        self.map_canvas.centerOn(
            self.map_canvas.map_data.map_grid_geometry.center_x,
            self.map_canvas.map_data.map_grid_geometry.center_y
        )

    def center_button_toggled(self, button):
        if button.objectName() == 'button_center_point':
            self.settings.set_value('maps', 'center_on', 'point')
        else:
            self.settings.set_value('maps', 'center_on', 'player')
            if '__you__' in self.map_canvas.players.keys():
                player = self.map_canvas.players['__you__']
                self.map_canvas.centerOn(
                    player.x,
                    player.y
                )

    def toggle_borderless(self, button):
        self.borderless = False if self.borderless else True
        if self.borderless:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.settings.set_value('maps', 'geometry', self.geometry())
        self._active = False
        self.hide()

    def is_active(self):
        return self._active

    def toggle(self):
        if self.is_active():
            self._active = False
            self.hide()
        else:
            self._active = True
            self.show()

    def parse(self, item):
        if item[27:50] == "LOADING, PLEASE WAIT...":
            self.map_canvas.draw_loading_screen()
        if item[27:43] == 'You have entered':
            self.map_canvas.load_map(item[44:-2])
        if item[27:43] == 'Your Location is':
            try:
                self.map_canvas.add_player('__you__', item[:27], item[43:])
                self.map_canvas.update_players()
            except Exception as e:
                print(e)
