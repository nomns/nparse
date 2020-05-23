from PyQt5.QtWidgets import (
    QDialog,
    QColorDialog,
    QFileDialog,
)
from PyQt5 import uic
from PyQt5.QtCore import QItemSelection, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QPalette

import os
from glob import glob

from utils import resource_path, set_qcolor, get_rgb, sound, create_tts_mp3
from config import profile_manager, trigger_manager, app_config

profile = profile_manager.profile

from .triggertree import TriggerTree


class SettingsWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(resource_path("data/ui/settings.ui"), self)

        # spell mp3 events
        self.spellSoundSelectButton.clicked.connect(self._set_spell_sound)
        self.spellSoundPlayButton.clicked.connect(self._play_spell_sound)

        # tts events
        self.ttsCreateButton.clicked.connect(self._create_tts)
        self.ttsPlayButton.clicked.connect(self._play_tts)
        self.ttsFileRefreshButton.clicked.connect(self._fill_tts_files)
        self.ttsDeleteButton.clicked.connect(self._remove_tts_file)
        self._fill_tts_files(None)

    def selectEQDirectoryButtonPress(self) -> None:
        dir_path = str(
            QFileDialog.getExistingDirectory(None, "Select Everquest Logs Directory")
        )
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
        self.settingsStack.setCurrentIndex(self._section_indexes.index(section))

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
        fd.setDirectory("./data/mp3")
        f = fd.getOpenFileName(filter="*.mp3")
        if f[0]:
            self.spellSoundFileLabel.setText(f[0])
        fd.setParent(None)

    def buffTextColorButtonPress(self, _) -> None:
        set_qcolor(
            self.buffBarLabel,
            foreground=self._get_color(get_rgb(self.buffBarLabel, QPalette.Foreground)),
        )

    def buffBarColorButtonPress(self, _) -> None:
        set_qcolor(
            self.buffBarLabel,
            background=self._get_color(get_rgb(self.buffBarLabel, QPalette.Background)),
        )

    def debuffTextColorButtonPress(self, _) -> None:
        set_qcolor(
            self.debuffBarLabel,
            foreground=self._get_color(
                get_rgb(self.debuffBarLabel, QPalette.Foreground)
            ),
        )

    def debuffBarColorButtonPress(self, _) -> None:
        set_qcolor(
            self.debuffBarLabel,
            background=self._get_color(
                get_rgb(self.debuffBarLabel, QPalette.Background)
            ),
        )

    def youColorButtonPress(self, _) -> None:
        set_qcolor(
            self.youTargetLabel,
            background=self._get_color(
                get_rgb(self.youTargetLabel, QPalette.Background)
            ),
        )

    def friendlyColorButtonPress(self, _) -> None:
        set_qcolor(
            self.friendlyTargetLabel,
            background=self._get_color(
                get_rgb(self.friendlyTargetLabel, QPalette.Background)
            ),
        )

    def enemyColorButtonPress(self, _) -> None:
        set_qcolor(
            self.enemyTargetLabel,
            background=self._get_color(
                get_rgb(self.enemyTargetLabel, QPalette.Background)
            ),
        )

    def targetTextColorButtonPress(self, _) -> None:
        color = self._get_color(get_rgb(self.youTargetLabel, QPalette.Foreground))
        set_qcolor(self.youTargetLabel, foreground=color)
        set_qcolor(self.friendlyTargetLabel, foreground=color)
        set_qcolor(self.enemyTargetLabel, foreground=color)

    def textShadowColorButtonPress(self, _) -> None:
        set_qcolor(
            self.textShadowColorLabel,
            background=self._get_color(
                get_rgb(self.textShadowColorLabel, QPalette.Background)
            ),
        )

    def _get_color(self, rgba: list = None) -> QColor:
        color = QColorDialog.getColor(
            QColor(*rgba), self, "Choose a Color", QColorDialog.ShowAlphaChannel
        )
        return color if color.isValid() else QColor(*rgba)

    def save_settings(self):
        # General
        app_config.update_check = self.updateCheckCheckBox.isChecked()
        app_config.eq_dir = self.eqDirectoryLabel.text()
        app_config.qt_scale_factor = self.qtScalingSpinBox.value()

        # Maps
        profile.maps.opacity = self.mapsOpacitySpinBox.value()
        profile.maps.line_width = self.mapLineSizeSpinBox.value()
        profile.maps.grid_line_width = self.mapGridLineSizeSpinBox.value()
        profile.maps.current_z_alpha = self.mapCurrentLevelSpinBox.value()
        profile.maps.closest_z_alpha = self.mapClosestLevelSpinBox.value()
        profile.maps.other_z_alpha = self.mapOtherLevelSpinBox.value()

        # Spells

        profile.spells.use_casting_window = self.spellsUseCastingWindowCheckBox.isChecked()
        profile.spells.casting_window_buffer = self.spellsCastingWindowTimeSpinBox.value()
        profile.spells.sound_enabled = self.spellsSoundEnabledCheckBox.isChecked()
        profile.spells.sound_volume = self.spellsSoundVolumesSlider.value()
        profile.spells.use_secondary_all = self.spellsUsePVPSpellDurationsCheckBox.isChecked()

        profile.spells.buff_text_color = get_rgb(
            self.buffBarLabel, self.buffBarLabel.foregroundRole()
        )
        profile.spells.buff_bar_color = get_rgb(
            self.buffBarLabel, self.buffBarLabel.backgroundRole()
        )
        profile.spells.debuff_text_color = get_rgb(
            self.debuffBarLabel, self.debuffBarLabel.foregroundRole()
        )
        profile.spells.debuff_bar_color = get_rgb(
            self.debuffBarLabel, self.debuffBarLabel.backgroundRole()
        )
        profile.spells.you_target_color = get_rgb(
            self.youTargetLabel, self.youTargetLabel.backgroundRole()
        )
        profile.spells.friendly_target_color = get_rgb(
            self.friendlyTargetLabel, self.friendlyTargetLabel.backgroundRole()
        )
        profile.spells.enemy_target_color = get_rgb(
            self.enemyTargetLabel, self.enemyTargetLabel.backgroundRole()
        )
        profile.spells.target_text_color = get_rgb(
            self.enemyTargetLabel, self.enemyTargetLabel.foregroundRole()
        )

        # Text

        profile.text.direction = self.textDirectionComboBox.currentText()
        profile.text.fade_seconds = self.textFadeSecondsSpinBox.value()
        profile.text.pixels_per_second = self.textPixelsPerSecondSpinBox.value()
        profile.text.shadow_blur_radius = self.textShadowBlurRadiusSpinBox.value()

        profile.text.shadow_color = get_rgb(
            self.textShadowColorLabel, self.textShadowColorLabel.backgroundRole()
        )

        app_config.save()
        profile_manager.save()
        trigger_manager.update(self.triggerTree.get_values())
        trigger_manager.save()

    def set_values(self):

        # General
        self.updateCheckCheckBox.setChecked(app_config.update_check)
        self.eqDirectoryLabel.setText(app_config.eq_dir)
        self.qtScalingSpinBox.setValue(app_config.qt_scale_factor)

        # Maps
        self.mapOpacitySpinBox.setValue(profile.maps.opacity)
        self.mapLineSizeSpinBox.setValue(profile.maps.line_width)
        self.mapGridLineSizeSpinBox.setValue(profile.maps.grid_line_width)
        self.mapCurrentLevelSpinBox.setValue(profile.maps.current_z_alpha)
        self.mapClosestLevelSpinBox.setValue(profile.maps.closest_z_alpha)
        self.mapOtherLevelSpinBox.setValue(profile.maps.other_z_alpha)

        # Spells
        self.spellsUseCastingWindowCheckBox.setChecked(profile.spells.use_casting_window)
        self.spellsCastingWindowTimeSpinBox.setValue(profile.spells.casting_window_buffer)
        self.spellsSoundEnabledCheckBox.setChecked(profile.spells.sound_enabled)
        self.spellsSoundVolumeSlider.setValue(profile.spells.sound_volume)
        self.spellsUsePVPSpellDurationsCheckBox.setChecked(profile.spells.use_secondary_all)

        set_qcolor(
            self.spellsBuffBarLabel,
            foreground=QColor(*profile.spells.buff_text_color),
            background=QColor(*profile.spells.buff_bar_color),
        )
        set_qcolor(
            self.spellsDebuffBarLabel,
            foreground=QColor(*profile.spells.debuff_text_color),
            background=QColor(*profile.spells.debuff_bar_color),
        )
        set_qcolor(
            self.spellsYouTargetLabel,
            foreground=QColor(*profile.spells.target_text_color),
            background=QColor(*profile.spells.you_target_color),
        )
        set_qcolor(
            self.spellsFriendlyTargetLabel,
            foreground=QColor(*profile.spells.target_text_color),
            background=QColor(*profile.spells.friendly_target_color),
        )
        set_qcolor(
            self.spellsEnemyTargetLabel,
            foreground=QColor(*profile.spells.target_text_color),
            background=QColor(*profile.spells.enemy_target_color),
        )

        # Text

        self.textDirectionComboBox.clear()
        self.textDirectionComboBox.addItems(["up", "down"])

        self.textDirectionComboBox.setCurrentText(profile.text.direction)
        self.textFadeSecondsSpinBox.setValue(profile.text.fade_seconds)
        self.textPixelsPerSecondSpinBox.setValue(profile.text.pixels_per_second)
        self.textShadowBlurRadiusSpinBox.setValue(profile.text.shadow_blur_radius)

        set_qcolor(
            self.textShadowColorLabel, background=QColor(*profile.text.shadow_color)
        )

        # Remove triggertree if it exists and reinsert it
        try:
            self.triggerTree.setParent(None)
        except:
            pass
        self.triggerTree = TriggerTree()
        self.treeViewLayout.insertWidget(0, self.triggerTree, 1)
