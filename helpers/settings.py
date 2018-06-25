from PyQt5.Qt import Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QFormLayout, QFrame,
                             QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QSpinBox, QStackedWidget, QPushButton,
                             QVBoxLayout, QWidget, QComboBox)

from helpers import config


WHATS_THIS_CASTING_WINDOW = """The Casting Window is a range of time in which the spell you are casting will land.
nParse limits parsing successful casts for the spell to only within that window.  This disables nParse from using other's
successful casts as yours.  It will also enable the ability to parse Group, Bard, and AOE spells.  The size of the buffer
window is equal to (2 x casting_window_buffer) + 1 msec.
""".replace('\n', ' ')

WHATS_THIS_CASTING_BUFFER = """The Casting Window Buffer will widen the Casting Window to accept successful casts.
If you are laggy or group spells are not parsing all successful targets, you may need to widen this.  On the other hand,
if you are getting too much interference from other's successful casts, you may want to lessen the buffer.
""".replace('\n', ' ')

WHATS_THIS_PVP_DURATION = """Within spells_us.txt, there are secondary timers that, from my limited testing, seem to be
the duration of debuffs when you cast on yourself.  Are these timers that coincide with PVP?  I don't know, I don't play
on Red.  Using the 'PvP Duration' will use the secondary timers for non beneficiary spells and will use the primary
durations for all good buffs.
""".replace('\n', ' ')


class SettingsWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('nParse Settings')

        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self._list_widget = QListWidget()
        self._list_widget.setObjectName('SettingsList')
        self._list_widget.setSelectionMode(QListWidget.SingleSelection)
        self._list_widget.currentItemChanged.connect(self._switch_stack)
        self._widget_stack = QStackedWidget()
        self._widget_stack.setObjectName('SettingsStack')
        top_layout.addWidget(self._list_widget, 0)
        top_layout.addWidget(self._widget_stack, 1)

        settings = self._create_settings()
        if settings:
            for setting_name, stacked_widget in settings:
                self._list_widget.addItem(QListWidgetItem(setting_name))
                self._widget_stack.addWidget(stacked_widget)

            self._list_widget.setCurrentRow(0)
        self._list_widget.setMaximumWidth(
            self._list_widget.minimumSizeHint().width())

        self._list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        buttons = QWidget()
        buttons.setObjectName('SettingsButtons')
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        save_button = QPushButton('Save')
        save_button.setAutoDefault(False)
        save_button.clicked.connect(self._save)
        buttons_layout.addWidget(save_button)
        cancel_button = QPushButton('Cancel')
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self._cancelled)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.insertStretch(0)
        buttons.setLayout(buttons_layout)
        layout.addLayout(top_layout, 1)
        layout.addWidget(buttons, 0)

        self.setLayout(layout)

        self._set_values()

    def _save(self):
        for stacked_widget in self._widget_stack.findChildren(QFrame):
            for widget in stacked_widget.children():
                wt = type(widget)
                if wt == QCheckBox:
                    key1, key2 = widget.objectName().split(':')
                    config.data[key1][key2] = widget.isChecked()
                if wt == QSpinBox:
                    key1, key2 = widget.objectName().split(':')
                    config.data[key1][key2] = widget.value()
        config.save()
        self.accept()

    def _cancelled(self):
        self._set_values()
        self.reject()

    def closeEvent(self, _):
        self._set_values()
        self.reject()

    def _switch_stack(self):
        if self._list_widget.selectedIndexes():
            self._widget_stack.setCurrentIndex(self._list_widget.currentRow())

    def _set_values(self):
        for stacked_widget in self._widget_stack.findChildren(QFrame):
            for widget in stacked_widget.children():
                wt = type(widget)
                if wt == QCheckBox:
                    key1, key2 = widget.objectName().split(':')
                    widget.setChecked(config.data[key1][key2])
                if wt == QSpinBox:
                    key1, key2 = widget.objectName().split(':')
                    widget.setValue(config.data[key1][key2])


    def _create_settings(self):
        stacked_widgets = []

        # General Settings
        general_settings = QFrame()
        gsl = QFormLayout()
        gsl.addRow(SettingsHeader('parsers'))
        gsl_opacity = QSpinBox()
        gsl_opacity.setRange(1, 100)
        gsl_opacity.setSingleStep(5)
        gsl_opacity.setSuffix('%')
        gsl_opacity.setObjectName('general:parser_opacity')
        gsl.addRow('Parser Window Opacity (% 1-100)', gsl_opacity)
        gsl_scaling = QSpinBox()
        gsl_scaling.setRange(50, 300)
        gsl_scaling.setSingleStep(5)
        gsl_scaling.setSuffix('%')
        gsl_scaling.setObjectName('general:qt_scale_factor')
        gsl.addRow('Window Scaling Factor', gsl_scaling)
        general_settings.setLayout(gsl)

        stacked_widgets.append(('General', general_settings))

        # Spell Settings
        spells_settings = QFrame()
        ssl = QFormLayout()
        ssl.addRow(SettingsHeader('general'))
        ssl_casting_window = QCheckBox()
        ssl_casting_window.setWhatsThis(WHATS_THIS_CASTING_WINDOW)
        ssl_casting_window.setObjectName('spells:use_casting_window')
        ssl.addRow('Use Casting Window', ssl_casting_window)
        ssl_casting_window_buffer = QSpinBox()
        ssl_casting_window_buffer.setWhatsThis(WHATS_THIS_CASTING_BUFFER)
        ssl_casting_window_buffer.setRange(1, 4000)
        ssl_casting_window_buffer.setSingleStep(100)
        ssl_casting_window_buffer.setObjectName('spells:casting_window_buffer')

        ssl.addRow('Casting Window Buffer (msec 1-4000)',
                ssl_casting_window_buffer)
        ssl_instants = QComboBox()
        row = ssl.addRow('Instants/Clickies', ssl_instants)
        print(row)

        ssl.addRow(SettingsHeader('experimental'))
        ssl_secondary_duration = QCheckBox()
        ssl_secondary_duration.setWhatsThis(WHATS_THIS_PVP_DURATION)
        ssl_secondary_duration.setObjectName('spells:use_secondary_all')
        ssl.addRow('Use PvP Durations', ssl_secondary_duration)
        spells_settings.setLayout(ssl)

        stacked_widgets.append(('Spells', spells_settings))

        # Map Settings
        map_settings = QFrame()
        msl = QFormLayout()
        msl.addRow(SettingsHeader('general'))
        msl_line_width = QSpinBox()
        msl_line_width.setObjectName('maps:line_width')
        msl_line_width.setRange(1, 10)
        msl_line_width.setSingleStep(1)
        msl.addRow('Map Line Width', msl_line_width)

        msl_grid_line_width = QSpinBox()
        msl_grid_line_width.setObjectName('maps:grid_line_width')
        msl_grid_line_width.setRange(1, 10)
        msl_grid_line_width.setSingleStep(1)
        msl.addRow('Grid Line Width', msl_grid_line_width)

        msl.addRow(SettingsHeader('z levels'))

        msl_current_z_alpha = QSpinBox()
        msl_current_z_alpha.setRange(1, 100)
        msl_current_z_alpha.setSingleStep(1)
        msl_current_z_alpha.setSuffix('%')
        msl_current_z_alpha.setObjectName('maps:current_z_alpha')
        msl.addRow('Current Z Opacity', msl_current_z_alpha)

        msl_closest_z_alpha = QSpinBox()
        msl_closest_z_alpha.setRange(1, 100)
        msl_closest_z_alpha.setSingleStep(1)
        msl_closest_z_alpha.setSuffix('%')
        msl_closest_z_alpha.setObjectName('maps:closest_z_alpha')
        msl.addRow('Closest Z Opacity', msl_closest_z_alpha)

        msl_other_z_alpha = QSpinBox()
        msl_other_z_alpha.setRange(1, 100)
        msl_other_z_alpha.setSingleStep(1)
        msl_other_z_alpha.setSuffix('%')
        msl_other_z_alpha.setObjectName('maps:other_z_alpha')
        msl.addRow('Other Z Opacity', msl_other_z_alpha)

        map_settings.setLayout(msl)
        stacked_widgets.append(('Maps', map_settings))

        return stacked_widgets


class SettingsHeader(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('SettingsLabel')
        self.setAlignment(Qt.AlignCenter)


class SpellBrowser(QDialog):

    def __init__(self):
        super().__init__()
