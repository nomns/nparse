from PyQt5.QtWidgets import (QDialog, QComboBox,
                             QCheckBox, QSpinBox, QColorDialog,
                             QSlider, QLabel, QFileDialog,)
from PyQt5 import uic
from PyQt5.QtCore import Qt, QItemSelection, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor

import os
from glob import glob
from dataclasses import dataclass

from helpers import config, resource_path, set_qcolor, get_rgb, sound, create_tts_mp3
from .triggers import TriggerTree
from .triggereditor import TriggerEditor


class SettingsWindow(QDialog):

    def __init__(self) -> None:
        super().__init__()

        uic.loadUi(resource_path('data/ui/settings.ui'), self)

        self._ref = {}
        self._ref = self._build_ref()

        # spell mp3 events
        self.spellSoundSelectButton.clicked.connect(self._set_spell_sound)
        self.spellSoundPlayButton.clicked.connect(self._play_spell_sound)

        # tts events
        self.ttsCreateButton.clicked.connect(self._create_tts)
        self.ttsPlayButton.clicked.connect(self._play_tts)
        self.ttsFileRefreshButton.clicked.connect(self._fill_tts_files)
        self.ttsDeleteButton.clicked.connect(self._remove_tts_file)
        self._fill_tts_files(None)

        # section Tree
        data = {
            'General': [{'Sound': ['Text to Speech']}],
            'Profiles': [],
            'Parsers': [
                'Maps',
                {'Spells': ['Appearance']},
                {'Triggers': ['Defaults']},
                'Text'
            ]
        }

        model = QStandardItemModel()
        model.setColumnCount(1)
        self._section_indexes: list = []
        self._add_section_data(data, model)
        self.settingsSectionTree.setModel(model)
        self.settingsSectionTree.selectionModel().selectionChanged.connect(self._section_changed)
        self.settingsSectionTree.expandAll()
        self.settingsSectionTree.resizeColumnToContents(0)
        self.settingsSectionTree.setMinimumWidth(150)

    def selectEQDirectoryButtonPress(self, _) -> None:
        dir_path = str(QFileDialog.getExistingDirectory(
            None, 'Select Everquest Logs Directory'))
        if dir_path:
            self.eqDirectoryLabel.setText(dir_path)

    def _add_section_data(self, data: dict, item) -> None:
        for k, i in data.items():
            k_item = QStandardItem(k)
            k_item.setSizeHint(QSize(0, 20))
            item.appendRow(k_item)
            self._section_indexes.append(k_item)
            for i2 in i:
                if type(i2) == str:
                    i2_item = QStandardItem(i2)
                    i2_item.setSizeHint(QSize(0, 20))
                    k_item.appendRow(i2_item)
                    self._section_indexes.append(i2_item)
                else:
                    self._add_section_data(i2, k_item)

    def _section_changed(self, event: QItemSelection) -> None:
        index = self.settingsSectionTree.selectedIndexes()[0]
        section: QStandardItem = index.model().itemFromIndex(index)
        self.settingsStack.setCurrentIndex(
            self._section_indexes.index(section)
        )

    def _remove_tts_file(self, _) -> None:
        try:
            if self.ttsFileCombo.currentText():
                os.remove(self.ttsFileCombo.currentText())
                self._fill_tts_files(None)
        except:
            pass

    def _create_tts(self, _):
        if self.ttsTextLineEdit.text():
            created_file = create_tts_mp3(self.ttsTextLineEdit.text())
            if created_file:
                self.ttsFileCombo.addItem(created_file)
                self.ttsFileCombo.setCurrentIndex(self.ttsFileCombo.count() - 1)
        self.ttsTextLineEdit.setText("")

    def _fill_tts_files(self, _):
        self.ttsFileCombo.clear()
        self.ttsFileCombo.addItems(glob("data/tts/*.mp3"))

    def _play_tts(self, _):
        sound.play(self.ttsFileCombo.currentText())

    def _play_spell_sound(self, _):
        sound.play(self.spellSoundFileLabel.text())

    def _set_spell_sound(self, _):
        fd = QFileDialog(self)
        fd.setDirectory('./data/mp3')
        f = fd.getOpenFileName(filter='*.mp3')
        if f[0]:
            self.spellSoundFileLabel.setText(f[0])
        fd.setParent(None)

    def buffTextColorButtonPress(self, _) -> None:
        set_qcolor(self.buffBarLabel, foreground=self._get_color())

    def buffBarColorButtonPress(self, _) -> None:
        set_qcolor(self.buffBarLabel, background=self._get_color())

    def debuffTextColorButtonPress(self, _) -> None:
        set_qcolor(self.debuffBarLabel, foreground=self._get_color())

    def debuffBarColorButtonPress(self, _) -> None:
        set_qcolor(self.debuffBarLabel, background=self._get_color())

    def youColorButtonPress(self, _) -> None:
        set_qcolor(self.youTargetLabel, background=self._get_color())

    def friendlyColorButtonPress(self, _) -> None:
        set_qcolor(self.friendlyTargetLabel,background=self._get_color())

    def enemyColorButtonPress(self, _) -> None:
        set_qcolor(self.enemyTargetLabel,background=self._get_color())

    def targetTextColorButtonPress(self, _) -> None:
        color = self._get_color()
        set_qcolor(self.youTargetLabel, foreground=color)
        set_qcolor(self.friendlyTargetLabel, foreground=color)
        set_qcolor(self.enemyTargetLabel, foreground=color)

    def textShadowColorButtonPress(self, _) -> None:
        set_qcolor(self.textShadowColorLabel,background=self._get_color())

    def _get_color(self) -> QColor:

        cd = QColorDialog(self)
        cd.setOption(QColorDialog.ShowAlphaChannel)
        color = cd.exec()
        cd.setParent(None)
        return color

    def save_settings(self):
        for section, references in self._ref.items():
            for setting, widget in references.items():
                wt = type(widget)
                if wt == QCheckBox:
                    config.data[section][setting] = widget.isChecked()
                elif wt == QSpinBox:
                    config.data[section][setting] = widget.value()
                elif wt == QSlider:
                    config.data[section][setting] = widget.value()
                elif wt == QLabel:
                    config.data[section][setting] = widget.text()
                elif wt == QComboBox:
                    config.data[section][setting] = widget.currentText()

        # spell color bars
        config.data['spells']['buff_text_color'] = get_rgb(self.buffBarLabel, self.buffBarLabel.foregroundRole())
        config.data['spells']['buff_bar_color'] = get_rgb(self.buffBarLabel, self.buffBarLabel.backgroundRole())
        config.data['spells']['debuff_text_color'] = get_rgb(self.debuffBarLabel, self.debuffBarLabel.foregroundRole())
        config.data['spells']['debuff_bar_color'] = get_rgb(self.debuffBarLabel, self.debuffBarLabel.backgroundRole())
        config.data['spells']['you_target_color'] = get_rgb(self.youTargetLabel, self.youTargetLabel.backgroundRole())
        config.data['spells']['friendly_target_color'] = get_rgb(self.friendlyTargetLabel, self.friendlyTargetLabel.backgroundRole())
        config.data['spells']['enemy_target_color'] = get_rgb(self.enemyTargetLabel, self.enemyTargetLabel.backgroundRole())
        config.data['spells']['target_text_color'] = get_rgb(self.enemyTargetLabel, self.enemyTargetLabel.foregroundRole())

        # text color
        config.data['text']['shadow_color'] = get_rgb(self.textShadowColorLabel, self.textShadowColorLabel.backgroundRole())

        config.triggers = self.triggerTree.get_values()
        config.save()

    def set_values(self):
        # Combo box setups
        # text
        self.textDirectionComboBox.clear()
        self.textDirectionComboBox.addItems(['up', 'down'])

        for section, references in self._ref.items():
            for setting, widget in references.items():
                wt = type(widget)
                if wt == QCheckBox:
                    widget.setChecked(config.data[section][setting])
                elif wt == QSpinBox:
                    widget.setValue(config.data[section][setting])
                elif wt == QSlider:
                    widget.setValue(config.data[section][setting])
                elif wt == QLabel:
                    widget.setText(config.data[section][setting])
                elif wt == QComboBox:
                    widget.setCurrentText(config.data[section][setting])


        # set bar colors for spells

        # buff bar
        set_qcolor(
            self.buffBarLabel,
            foreground=QColor(*config.data['spells']['buff_text_color']),
            background=QColor(*config.data['spells']['buff_bar_color'])
        )

        # debuff bar
        set_qcolor(
            self.debuffBarLabel,
            foreground=QColor(*config.data['spells']['debuff_text_color']),
            background=QColor(*config.data['spells']['debuff_bar_color'])
        )

        # you target
        set_qcolor(
            self.youTargetLabel,
            foreground=QColor(*config.data['spells']['target_text_color']),
            background=QColor(*config.data['spells']['you_target_color'])
        )

        # friendly target
        set_qcolor(
            self.friendlyTargetLabel,
            foreground=QColor(*config.data['spells']['target_text_color']),
            background=QColor(*config.data['spells']['friendly_target_color'])
        )

        # enemey target
        set_qcolor(
            self.enemyTargetLabel,
            foreground=QColor(*config.data['spells']['target_text_color']),
            background=QColor(*config.data['spells']['enemy_target_color'])
        )

        # text shadow color
        set_qcolor(
            self.textShadowColorLabel,
            background=QColor(*config.data['text']['shadow_color'])
        )

        # Remove triggertree if it exists and reinsert it
        try:
            self.triggerTree.setParent(None)
        except:
            pass
        self.triggerTree = TriggerTree()
        self.treeViewLayout.insertWidget(0, self.triggerTree, 1)

    def _build_ref(self) -> dict:
        d = {
            'general': {
                'eq_dir': self.eqDirectoryLabel,
                'update_check': self.updateCheckCheckBox,
                'parser_opacity': self.parserOpacitySpinBox,
                'qt_scale_factor': self.qTScalingSpinBox,
                'sound_volume': self.soundVolume
            },
            'maps': {
                'line_width': self.mapLineSizeSpinBox,
                'grid_line_width': self.gridLineSizeSpinBox,
                'current_z_alpha': self.currentLevelSpinBox,
                'closest_z_alpha': self.closestLevelSpinBox,
                'other_z_alpha': self.otherLevelsSpinBox
            },
            'spells': {
                'use_casting_window': self.useCastingWindowCheckBox,
                'casting_window_buffer': self.castingWindowTimeSpinBox,
                'use_secondary_all': self.usePVPSpellDurationsCheckBox,
                'sound_enabled': self.spellSoundEnabledCheckBox,
                'sound_file': self.spellSoundFileLabel
            },
            'text': {
                'direction': self.textDirectionComboBox,
                'fade_seconds': self.fadeSecondsSpinBox,
                'pixels_per_second': self.movePixelsSecondSpinBox,
                'shadow_radius': self.shadowBlurRadiusSpinBox
            }
        }
        return d
