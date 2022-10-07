import functools

from PyQt6.QtWidgets import (QCheckBox, QDialog, QFormLayout, QFrame,
                             QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QSpinBox, QStackedWidget, QPushButton,
                             QVBoxLayout, QWidget, QComboBox, QLineEdit,
                             QMessageBox, QColorDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from helpers import config, text_time_to_seconds
from helpers import location_service
from parsers.spells import CustomTrigger


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

WHATS_THIS_ITEM_TRIGGERS = """Certain items don't have a casting message, which prevents them from registering. Enabling
this option allows nParse to attempt to catch these spells anyway. This may also cause nParse to detect spells cast on
you by other players. WARNING: This option is very buggy. Use it at your own risk, and only if you absolutely need item
spell durations at all costs. There will be other strange behavior.
""".replace('\n', ' ')

WHATS_THIS_SHARING = """Your location can be shared with others via a central location server. If you enable this, you
agree to send and receive location data via a third-party server. The only data other players can see is your character
name and the zone+loc you send. Nothing personally identifiable will be visible beyond this.
""".replace('\n', ' ')

WHATS_THIS_SHARING_DISCORD = """Automatically share with other users in your configured discord channel.
When this option is set, the sharing key specified above will be ignored.""".replace('\n', ' ')

WHATS_THIS_CLICKTHROUGH = """When set, the window will not capture mouse clicks, so your click will go through to
whatever is below it. Practically, this means you can still interact with EverQuest *through* the nParse
window.""".replace('\n', ' ')


class SettingsWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('nParse Settings')

        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self._list_widget = QListWidget()
        self._list_widget.setObjectName('SettingsList')
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list_widget.currentItemChanged.connect(self._switch_stack)
        self._widget_stack = QStackedWidget()
        self._widget_stack.setObjectName('SettingsStack')
        top_layout.addWidget(self._list_widget, 0)
        top_layout.addWidget(self._widget_stack, 1)
        self._color_dialogs = dict()

        settings = self._create_settings()
        if settings:
            for setting_name, stacked_widget in settings:
                self._list_widget.addItem(QListWidgetItem(setting_name))
                self._widget_stack.addWidget(stacked_widget)

            self._list_widget.setCurrentRow(0)
        self._list_widget.setMaximumWidth(
            self._list_widget.minimumSizeHint().width())

        self._list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
                elif wt == QSpinBox:
                    key1, key2 = widget.objectName().split(':')
                    config.data[key1][key2] = widget.value()
                elif wt == QLineEdit:
                    key1, key2 = widget.objectName().split(':')
                    config.data[key1][key2] = widget.text()
        for widget in self._color_dialogs.values():
            wt = type(widget)
            if wt == QColorDialog:
                key1, key2 = widget.objectName().split(':')
                hexcolor = hex(widget.currentColor().rgb()).replace('0xff', '#')
                config.data[key1][key2] = hexcolor
        config.save()
        self._config_update_triggers()
        self.accept()

    def _config_update_triggers(self):
        location_service.SIGNALS.config_updated.emit()

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
                    if key1 == 'sharing' and key2 == 'discord_channel' \
                            and config.data[key1][key2]:
                        self.sharing_group_key.setDisabled(True)
                    if key1 == 'sharing' and key2 == 'player_name_override' \
                            and not config.data[key1][key2]:
                        self.sharing_player_name.setDisabled(True)
                elif wt == QSpinBox:
                    key1, key2 = widget.objectName().split(':')
                    widget.setValue(config.data[key1][key2])
                elif wt == QLineEdit:
                    key1, key2 = widget.objectName().split(':')
                    widget.setText(config.data[key1][key2])
                elif wt == QPushButton and widget.objectName():
                    # Using QPushButton as a poor-man's rectangle
                    key1, key2 = widget.objectName().split(':')
                    hexcolor = config.data[key1][key2]
                    widget.setStyleSheet(
                        "background-color: {0}; "
                        "border: 4px solid {0};".format(hexcolor))
        for widget in self._color_dialogs.values():
            wt = type(widget)
            if wt == QColorDialog:
                key1, key2 = widget.objectName().split(':')
                hexcolor = config.data[key1][key2]
                intcolor = int(hexcolor.replace('#', '0xff'), 16)
                widget.setCurrentColor(QColor(intcolor))

    def _create_settings(self):
        stacked_widgets = []

        # General Settings
        general_settings = QFrame()
        gsl = QFormLayout()
        gsl.addRow(SettingsHeader('general'))
        gsl_update_check = QCheckBox()
        gsl_update_check.setObjectName('general:update_check')
        gsl.addRow('Check for Updates', gsl_update_check)
        gsl.addRow(SettingsHeader('parsers'))
        gsl_scaling = QSpinBox()
        gsl_scaling.setRange(100, 300)
        gsl_scaling.setSingleStep(5)
        gsl_scaling.setSuffix('%')
        gsl_scaling.setObjectName('general:qt_scale_factor')
        gsl.addRow('Window Scaling Factor', gsl_scaling)
        gsl_window_flush = QCheckBox()
        gsl_window_flush.setObjectName('general:window_flush')
        gsl.addRow('Flush Vertical Placement', gsl_window_flush)
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

        ssl.addRow(
            'Casting Window Buffer (msec 1-4000)',
            ssl_casting_window_buffer
            )
        ssl_open_custom = QPushButton("Edit")
        ssl_open_custom.clicked.connect(self._get_custom_timers)
        ssl.addRow('Custom Timers', ssl_open_custom)

        ssl.addRow(SettingsHeader('experimental'))
        ssl_secondary_duration = QCheckBox()
        ssl_secondary_duration.setWhatsThis(WHATS_THIS_PVP_DURATION)
        ssl_secondary_duration.setObjectName('spells:use_secondary_all')
        ssl.addRow('Use PvP Durations', ssl_secondary_duration)
        ssl_item_trigger_mode = QCheckBox()
        ssl_item_trigger_mode.setWhatsThis(WHATS_THIS_ITEM_TRIGGERS)
        ssl_item_trigger_mode.setObjectName('spells:use_item_triggers')
        ssl.addRow('Permissive Item Triggers', ssl_item_trigger_mode)
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

        # Sharing Settings
        sharing_settings = QFrame()
        shsl = QFormLayout()
        shsl.addRow(SettingsHeader('general'))

        enable_sharing = QCheckBox()
        enable_sharing.setWhatsThis(WHATS_THIS_SHARING)
        enable_sharing.setObjectName('sharing:enabled')
        shsl.addRow('Enable Sharing', enable_sharing)

        self.sharing_player_name = QLineEdit()
        self.sharing_player_name.setObjectName('sharing:player_name')
        shsl.addRow(
            'Display Name',
            self.sharing_player_name
        )

        sharing_player_name_override = QCheckBox()
        sharing_player_name_override.setObjectName(
            'sharing:player_name_override')
        shsl.addRow(
            'Display Name Override',
            sharing_player_name_override
        )
        sharing_player_name_override.clicked.connect(
            functools.partial(self._dynamic_field_toggle,
                              sharing_player_name_override,
                              self.sharing_player_name, True))

        sharing_hostname = QLineEdit()
        sharing_hostname.setObjectName('sharing:url')
        shsl.addRow(
            'Sharing Hostname',
            sharing_hostname
        )

        self.sharing_group_key = QLineEdit()
        self.sharing_group_key.setObjectName('sharing:group_key')
        shsl.addRow(
            'Group Key',
            self.sharing_group_key
        )
        sharing_discord_channel = QCheckBox()
        sharing_discord_channel.setObjectName('sharing:discord_channel')
        sharing_discord_channel.setWhatsThis(WHATS_THIS_SHARING_DISCORD)
        shsl.addRow('Use Discord Channel', sharing_discord_channel)
        sharing_discord_channel.clicked.connect(
            functools.partial(self._dynamic_field_toggle,
                              sharing_discord_channel,
                              self.sharing_group_key, False))

        sharing_reconnect_delay = QSpinBox()
        sharing_reconnect_delay.setRange(1, 300)
        sharing_reconnect_delay.setSingleStep(1)
        sharing_reconnect_delay.setSuffix(' seconds')
        sharing_reconnect_delay.setObjectName('sharing:reconnect_delay')
        shsl.addRow('Reconnect Delay', sharing_reconnect_delay)
        sharing_settings.setLayout(shsl)
        stacked_widgets.append(('Sharing', sharing_settings))

        # Appearance Settings
        appearance_settings = QFrame()
        appear_sl = QFormLayout()
        for window in ("maps", "spells", "discord"):
            appear_sl.addRow(SettingsHeader(window.title()))
            opacity = QSpinBox()
            opacity.setRange(0, 100)
            opacity.setSingleStep(5)
            opacity.setSuffix('%')
            opacity.setObjectName('%s:opacity' % window)
            appear_sl.addRow('Window Opacity (% 0-100)', opacity)
            if window == 'discord':
                # Discord has a second opacity setting
                bg_opacity = QSpinBox()
                bg_opacity.setRange(0, 100)
                bg_opacity.setSingleStep(5)
                bg_opacity.setSuffix('%')
                bg_opacity.setObjectName('%s:bg_opacity' % window)
                appear_sl.addRow('Background Opacity (% 0-100)', bg_opacity)
                # Color is also only discord for now
                color_hbox = QHBoxLayout()
                color_button = QPushButton('Set Color')
                color_preview = QPushButton("")
                color_preview.setObjectName('%s:color' % window)
                color_hbox.addWidget(color_preview)
                color_hbox.addWidget(color_button)
                color_dialog = QColorDialog()
                color_dialog.setObjectName('%s:color' % window)
                color_dialog.setWindowTitle("Set %s Color" % window.title())
                self._color_dialogs[window] = color_dialog
                color_button.clicked.connect(functools.partial(
                    self.show_color_picker,
                    window=window, preview=color_preview))
                color_preview.clicked.connect(functools.partial(
                    self.show_color_picker,
                    window=window, preview=color_preview))
                appear_sl.addRow('Background Color', color_hbox)
            enable_clickthrough = QCheckBox()
            enable_clickthrough.setWhatsThis(WHATS_THIS_SHARING)
            enable_clickthrough.setObjectName('%s:clickthrough' % window)
            enable_clickthrough.setWhatsThis(WHATS_THIS_CLICKTHROUGH)
            appear_sl.addRow('Enable Click-through', enable_clickthrough)

        appearance_settings.setLayout(appear_sl)
        stacked_widgets.append(('Appearance', appearance_settings))

        return stacked_widgets

    def show_color_picker(self, window, preview):
        dialog = self._color_dialogs[window]
        if dialog.exec():
            current_color = dialog.currentColor()
            hexcolor = hex(current_color.rgb()).replace('0xff', '#')
            preview.setStyleSheet("background-color: {0}; "
                                  "border: 4px solid {0};".format(hexcolor))
        else:
            hexcolor = config.data[window]['color']
            intcolor = int(hexcolor.replace('#', '0x'), 16)
            dialog.setCurrentColor(QColor(intcolor))

    def _get_custom_timers(self):
        dialog = CustomTriggerSettings()
        dialog.exec()

    def _dynamic_field_toggle(self, toggle_field, dynamic_field, invert=False):
        if toggle_field.isChecked():
            dynamic_field.setDisabled(not invert)
        else:
            dynamic_field.setDisabled(bool(invert))


class SettingsHeader(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('SettingsLabel')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class CustomTriggerSettings(QDialog):

    def __init__(self):
        super().__init__()

        self._custom_triggers = {}
        self._current_trigger = ''

        self.setWindowTitle("Custom Timers")
        self._setup_ui()
        self._load_from_config()

    def _setup_ui(self):

        layout = QVBoxLayout()

        self._triggers = QComboBox()
        self._triggers.setObjectName("TriggersCombo")
        self._triggers.activated.connect(self._activated)
        layout.addWidget(self._triggers, 1)

        button_layout = QHBoxLayout()
        self._add_trigger_button = QPushButton()
        self._add_trigger_button.setText('add')
        self._add_trigger_button.clicked.connect(self._add_trigger)
        button_layout.addWidget(self._add_trigger_button)

        self._remove_trigger_button = QPushButton()
        self._remove_trigger_button.setText('remove')
        self._remove_trigger_button.clicked.connect(self._remove_trigger)
        button_layout.addWidget(self._remove_trigger_button)

        self._save_trigger_button = QPushButton()
        self._save_trigger_button.setText('save')
        self._save_trigger_button.clicked.connect(self._save_trigger)
        button_layout.addWidget(self._save_trigger_button)

        layout.addItem(button_layout)

        trigger_layout = QFormLayout()
        trigger_layout.setSpacing(10)

        trigger_layout.addRow(SettingsHeader('Trigger'))

        self._trigger_name = QLineEdit()
        self._trigger_name.setMaxLength(50)
        trigger_layout.addRow('Name', self._trigger_name)

        self._trigger_text = QLineEdit()
        trigger_layout.addRow('Text', self._trigger_text)

        trigger_layout.addWidget(QLabel("* can be used to match anything."))

        self._trigger_time = QLineEdit()
        self._trigger_time.setText("hh:mm:ss")
        trigger_layout.addRow('Time', self._trigger_time)

        layout.addItem(trigger_layout)

        layout.addWidget(QWidget(), 1)  # spacer

        button_layout = QHBoxLayout()
        button_layout.addWidget(QWidget(), 1)  # spacer
        self._exit_button = QPushButton("Close")
        self._exit_button.clicked.connect(self._close)
        button_layout.addWidget(self._exit_button)
        layout.addItem(button_layout)

        self.setLayout(layout)

    def _load_from_config(self):
        self._triggers.clear()
        for item in config.data['spells']['custom_timers']:
            ct = CustomTrigger(*item)
            self._custom_triggers[ct.name] = ct
            self._triggers.addItem(ct.name)

        if self._custom_triggers:
            ct = self._custom_triggers[self._triggers.currentText()]
            self._trigger_name.setText(ct.name)
            self._trigger_text.setText(ct.text)
            self._trigger_time.setText(ct.time)
            self._current_trigger = self._triggers.currentText()
        else:
            self._current_trigger = None
            self._clear()

    def _save_to_config(self):
        config.data['spells']['custom_timers'] =\
            [
                x.to_list() for x
                in sorted(self._custom_triggers.values(), key=lambda x: x.name)
                if x.name != ""
            ]
        config.save()

    def _add_trigger(self):
        self._triggers.addItem('')
        self._triggers.setCurrentIndex(self._triggers.count() - 1)
        self._current_trigger = self._triggers.currentText()
        self._clear()
        self._trigger_name.setPlaceholderText('<new>')
        self._trigger_name.selectAll()
        self._trigger_name.setFocus()
        self._trigger_text.setPlaceholderText('match*me')
        self._trigger_time.setPlaceholderText('hh:mm:ss')

    def _remove_trigger(self):
        if self._triggers.currentText():
            self._custom_triggers.pop(self._triggers.currentText())
            self._save_to_config()
            self._load_from_config()
        else:
            self._triggers.removeItem(self._triggers.currentIndex())
        self._load_from_config()

    def _save_trigger(self):
        if self._trigger_name.text():
            # validate text and time
            if self._trigger_text.text() and \
                    text_time_to_seconds(self._trigger_time.text()):
                if self._trigger_name.text() in self._custom_triggers and \
                        not self._trigger_name.text() == self._current_trigger:
                    m = QMessageBox()
                    m.setText("A custom trigger with this name already exists.")
                    m.exec()
                elif not self._trigger_name.text() == self._current_trigger and \
                        self._current_trigger != '':
                    # update name and info
                    ct = self._custom_triggers.pop(self._current_trigger)
                    ct.name = self._trigger_name.text()
                    ct.text = self._trigger_text.text()
                    ct.time = self._trigger_time.text()
                    self._custom_triggers[ct.name] = ct
                elif self._current_trigger == '':
                    # new trigger
                    ct = CustomTrigger(
                        self._trigger_name.text(),
                        self._trigger_text.text(),
                        self._trigger_time.text()
                    )
                    self._custom_triggers[ct.name] = ct
                else:
                    # update
                    ct = self._custom_triggers[self._current_trigger]
                    ct.text = self._trigger_text.text()
                    ct.time = self._trigger_time.text()
                    self._custom_triggers[self._current_trigger] = ct

                # save and reload
                current_index = self._triggers.currentIndex()
                self._save_to_config()
                self._load_from_config()
                self._triggers.setCurrentIndex(current_index)
                self._activated(None)

            else:
                m = QMessageBox()
                m.setText("Both the text and time (hh:mm:ss) need to be filled out.")
                m.exec()

    def _activated(self, _):
        self._current_trigger = name = self._triggers.currentText()
        if name != "":
            self._trigger_name.setText(self._custom_triggers[name].name)
            self._trigger_text.setText(self._custom_triggers[name].text)
            self._trigger_time.setText(self._custom_triggers[name].time)
        else:
            self._clear()

    def _clear(self):
        self._trigger_name.clear()
        self._trigger_text.clear()
        self._trigger_time.clear()

    def _close(self, _):
        self._save_to_config()
        self.accept()

    def closeEvent(self, _):
        self._save_to_config()
        self.accept()
