from PyQt5.QtWidgets import (QCheckBox, QDialog, QFormLayout, QFrame,
                             QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QSpinBox, QStackedWidget, QPushButton,
                             QVBoxLayout, QWidget, QComboBox, QLineEdit,
                             QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5 import uic

from helpers import config, text_time_to_seconds, resource_path


class SettingsWindow(QDialog):

    def __init__(self):
        super().__init__()

        uic.loadUi(resource_path('data/ui/settings.ui'), self)

        self._ref = {}
        self._ref = self._build_ref()
        self.set_values()

        # events
        self.addTriggerButton.clicked.connect(self._addTrigger)

        # self.triggerTreeView

    def _addTrigger(self, _):
        text, response = QInputDialog.getText(
            self,
            "New Trigger",
            "Enter Trigger Name:"
        )
        if response:
            print(text)

    def save_settings(self):
        for section, references in self._ref.items():
            for setting, widget in references.items():
                wt = type(widget)
                if wt == QCheckBox:
                    config.data[section][setting] = widget.isChecked()
                    widget.setChecked(config.data[section][setting])
                elif wt == QSpinBox:
                    config.data[section][setting] = widget.value()
                    widget.setValue(config.data[section][setting])
        config.save()

    def set_values(self):
        for section, references in self._ref.items():
            for setting, widget in references.items():
                wt = type(widget)
                if wt == QCheckBox:
                    widget.setChecked(config.data[section][setting])
                elif wt == QSpinBox:
                    widget.setValue(config.data[section][setting])

    def _build_ref(self):
        d = {
            'general': {
                'update_check': self.updateCheckCheckBox,
                'parser_opacity': self.parserOpacitySpinBox,
                'qt_scale_factor': self.qTScalingSpinBox,
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
                'use_secondary_all': self.usePVPSpellDurationsCheckBox
            }
        }
        return d
