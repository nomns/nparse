from PyQt5.QtWidgets import QDialog, QColorDialog, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPalette

import os
from glob import glob

from utils import resource_path, set_qcolor, get_rgb, sound, create_tts_mp3, mp3_to_data
from config import profile, app_config, trigger_manager

from .triggertree import TriggerTree


class SettingsWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(resource_path("data/ui/settings.ui"), self)

    # Events

    def selectEQDirectoryButtonClicked(self) -> None:
        dir_path = str(
            QFileDialog.getExistingDirectory(None, "Select Everquest Directory")
        )
        if dir_path:
            self.eqDirectoryLabel.setText(dir_path)

    def ttsDeleteButtonClicked(self) -> None:
        if self.ttsFileCombo.currentText():
            os.remove(os.path.join("data/tts", self.ttsFileCombo.currentText()))
            self.ttsRefreshButtonClicked()

    def ttsCreateButtonClicked(self) -> None:
        if self.ttsTextLineEdit.text():
            created_file = create_tts_mp3(self.ttsTextLineEdit.text())
            if created_file:
                name = os.path.basename(created_file)
                self.ttsRefreshButtonClicked()
                self.ttsFileCombo.setCurrentText(name)
        self.ttsTextLineEdit.setText("")

    def ttsPlayButtonClicked(self) -> None:
        sound.play(
            mp3_to_data(os.path.join("data/tts", self.ttsFileCombo.currentText()))
        )

    def ttsRefreshButtonClicked(self) -> None:
        self.ttsFileCombo.clear()
        self.ttsFileCombo.addItems(os.path.basename(f) for f in glob("data/tts/*.mp3"))

    def spellsSoundPlayButtonClicked(self):
        sound.play(mp3_to_data(self.spellsSoundFileLabel.text()))

    def spellsSoundSelectButtonClicked(self):
        fd = QFileDialog(self)
        fd.setDirectory("./data/mp3")
        f = fd.getOpenFileName(filter="*.mp3")
        if f[0]:
            self.spellsSoundFileLabel.setText(f[0])
        fd.setParent(None)

    def spellsSoundVolumeSliderChanged(self, value: int) -> None:
        self.spellsSoundVolumeLabel.setText(value)

    def spellsBuffTextColorButtonClicked(self) -> None:
        set_qcolor(
            self.spellsBuffBarLabel,
            foreground=self._get_color(
                get_rgb(self.spellsBuffBarLabel, QPalette.Foreground)
            ),
        )

    def spellsBuffBarColorButtonClicked(self) -> None:
        set_qcolor(
            self.spellsBuffBarLabel,
            background=self._get_color(
                get_rgb(self.spellsBuffBarLabel, QPalette.Background)
            ),
        )

    def spellsDebuffTextColorButtonClicked(self) -> None:
        set_qcolor(
            self.spellsDebuffBarLabel,
            foreground=self._get_color(
                get_rgb(self.spellsDebuffBarLabel, QPalette.Foreground)
            ),
        )

    def spellsDebuffBarColorButtonClicked(self) -> None:
        set_qcolor(
            self.spellsDebuffBarLabel,
            background=self._get_color(
                get_rgb(self.spellsDebuffBarLabel, QPalette.Background)
            ),
        )

    def spellsYouColorButtonClicked(self) -> None:
        set_qcolor(
            self.spellsYouTargetLabel,
            background=self._get_color(
                get_rgb(self.spellsYouTargetLabel, QPalette.Background)
            ),
        )

    def spellsFriendlyColorButtonClicked(self, _) -> None:
        set_qcolor(
            self.spellsFriendlyTargetLabel,
            background=self._get_color(
                get_rgb(self.spellsFriendlyTargetLabel, QPalette.Background)
            ),
        )

    def spellsEnemyColorButtonClicked(self, _) -> None:
        set_qcolor(
            self.spellsEnemyTargetLabel,
            background=self._get_color(
                get_rgb(self.spellsEnemyTargetLabel, QPalette.Background)
            ),
        )

    def spellsTargetTextColorButtonClicked(self, _) -> None:
        color = self._get_color(get_rgb(self.spellsYouTargetLabel, QPalette.Foreground))
        set_qcolor(self.spellsYouTargetLabel, foreground=color)
        set_qcolor(self.spellsFriendlyTargetLabel, foreground=color)
        set_qcolor(self.spellsEnemyTargetLabel, foreground=color)

    def textShadowColorButtonClicked(self, _) -> None:
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
        profile.maps.opacity = self.mapOpacitySpinBox.value()
        profile.maps.line_width = self.mapLineSizeSpinBox.value()
        profile.maps.grid_line_width = self.mapGridLineSizeSpinBox.value()
        profile.maps.current_z_alpha = self.mapCurrentLevelSpinBox.value()
        profile.maps.closest_z_alpha = self.mapClosestLevelSpinBox.value()
        profile.maps.other_z_alpha = self.mapOtherLevelSpinBox.value()

        # Spells

        profile.spells.persistent_buffs = (
            self.spellsPersistentBuffTimersCheckBox.isChecked()
        )
        profile.spells.persistent_debuffs = (
            self.spellsPersistentDebuffTimersCheckBox.isChecked()
        )
        profile.spells.use_casting_window = (
            self.spellsUseCastingWindowCheckBox.isChecked()
        )
        profile.spells.casting_window_buffer = (
            self.spellsCastingWindowTimeSpinBox.value()
        )
        profile.spells.sound_enabled = self.spellsSoundEnabledCheckBox.isChecked()
        profile.spells.sound_volume = self.spellsSoundVolumeSlider.value()
        profile.spells.use_secondary_all = (
            self.spellsUsePVPSpellDurationsCheckBox.isChecked()
        )

        profile.spells.buff_text_color = get_rgb(
            self.spellsBuffBarLabel, QPalette.Foreground
        )
        profile.spells.buff_bar_color = get_rgb(
            self.spellsBuffBarLabel, QPalette.Background
        )
        profile.spells.debuff_text_color = get_rgb(
            self.spellsDebuffBarLabel, QPalette.Foreground
        )
        profile.spells.debuff_bar_color = get_rgb(
            self.spellsDebuffBarLabel, QPalette.Background
        )
        profile.spells.you_target_color = get_rgb(
            self.spellsYouTargetLabel, QPalette.Background
        )
        profile.spells.friendly_target_color = get_rgb(
            self.spellsFriendlyTargetLabel, QPalette.Background
        )
        profile.spells.enemy_target_color = get_rgb(
            self.spellsEnemyTargetLabel, QPalette.Background
        )
        profile.spells.target_text_color = get_rgb(
            self.spellsEnemyTargetLabel, QPalette.Foreground
        )

        # Text

        profile.text.direction = self.textDirectionComboBox.currentText()
        profile.text.fade_seconds = self.textFadeSecondsSpinBox.value()
        profile.text.pixels_per_second = self.textPixelsPerSecondSpinBox.value()
        profile.text.shadow_blur_radius = self.textShadowBlurRadiusSpinBox.value()

        profile.text.shadow_color = get_rgb(
            self.textShadowColorLabel, self.textShadowColorLabel.backgroundRole()
        )

        profile.trigger_choices = self.triggerTree.get_choices()
        app_config.save()
        profile.save()

        trigger_manager.save()

    def set_values(self):
        # fill combo boxes
        self.ttsRefreshButtonClicked()
        self.textDirectionComboBox.clear()
        self.textDirectionComboBox.addItems(["up", "down"])

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
        self.spellsUseCastingWindowCheckBox.setChecked(
            profile.spells.use_casting_window
        )
        self.spellsPersistentBuffTimersCheckBox.setChecked(
            profile.spells.persistent_buffs
        )
        self.spellsPersistentDebuffTimersCheckBox.setChecked(
            profile.spells.persistent_debuffs
        )
        self.spellsCastingWindowTimeSpinBox.setValue(
            profile.spells.casting_window_buffer
        )
        self.spellsSoundEnabledCheckBox.setChecked(profile.spells.sound_enabled)
        self.spellsSoundFileLabel.setText(profile.spells.sound_file)
        self.spellsSoundVolumeSlider.setValue(profile.spells.sound_volume)
        self.spellsUsePVPSpellDurationsCheckBox.setChecked(
            profile.spells.use_secondary_all
        )

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

        self.textDirectionComboBox.setCurrentText(profile.text.direction)
        self.textFadeSecondsSpinBox.setValue(profile.text.fade_seconds)
        self.textPixelsPerSecondSpinBox.setValue(profile.text.pixels_per_second)
        self.textShadowBlurRadiusSpinBox.setValue(profile.text.shadow_blur_radius)

        set_qcolor(
            self.textShadowColorLabel, background=QColor(*profile.text.shadow_color),
        )

        # Remove triggertree if it exists and reinsert it
        try:
            self.triggerTree.setParent(None)
        except:
            pass
        self.triggerTree = TriggerTree()
        self.treeViewLayout.insertWidget(0, self.triggerTree, 1)
