from PyQt5.Qt import QIntValidator, Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
                             QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QPushButton,
                             QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

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
        self._setup_ui()

        self._set_values()
    
    def _setup_ui(self):
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

        settings = create_settings()
        if settings:
            for setting_name, stacked_widget in settings:
                self._list_widget.addItem(QListWidgetItem(setting_name))
                self._widget_stack.addWidget(stacked_widget)
            
            self._list_widget.setCurrentRow(0)
        
        self._list_widget.setMaximumWidth(self._list_widget.minimumSizeHint().width())
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
    
    def _save(self):
        for stacked_widget in self._widget_stack.findChildren(QFrame):
            for widget in stacked_widget.children():
                wt = widget_type = type(widget)
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


def create_settings():
    stacked_widgets = []

    # General Settings
    general_settings = QFrame()
    gsl = general_settings_layout = QFormLayout()
    gsl.addRow(SettingsHeader('parsers'))
    gsl_opacity = QSpinBox()
    gsl_opacity.setRange(1, 100)
    gsl_opacity.setSingleStep(5)
    gsl_opacity.setSuffix('%')
    gsl_opacity.setObjectName('general:parser_opacity')
    gsl.addRow('Parser Window Opacity (% 1-100)', gsl_opacity)
    general_settings.setLayout(gsl)

    stacked_widgets.append(('General', general_settings))
    
    # Spell Settings
    spells_settings = QFrame()
    ssl = spells_settings.layout = QFormLayout()
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
    ssl.addRow('Casting Window Buffer (msec 1-4000)', ssl_casting_window_buffer)
    ssl.addRow(SettingsHeader('experimental'))
    ssl_secondary_duration = QCheckBox()
    ssl_secondary_duration.setWhatsThis(WHATS_THIS_PVP_DURATION)
    ssl_secondary_duration.setObjectName('spells:use_secondary_all')
    ssl.addRow('Use PvP Durations', ssl_secondary_duration)
    spells_settings.setLayout(ssl)

    stacked_widgets.append(('Spells', spells_settings))


    return stacked_widgets

class SettingsHeader(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('SettingsLabel')
        self.setAlignment(Qt.AlignCenter)
