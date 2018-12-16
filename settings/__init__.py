from PyQt5.QtWidgets import (QMessageBox, QInputDialog, QDialog,
                             QCheckBox, QSpinBox)
from PyQt5 import uic
from PyQt5.QtCore import Qt

from helpers import config, resource_path
from .triggers import TriggerTree
from .triggereditor import TriggerEditor


class SettingsWindow(QDialog):

    def __init__(self):
        super().__init__()

        uic.loadUi(resource_path('data/ui/settings.ui'), self)

        self._ref = {}
        self._ref = self._build_ref()
        self.set_values()

        # events
        self.addTriggerButton.clicked.connect(self._addTrigger)
        self.newGroupButton.clicked.connect(self._addGroup)
        self.removeButton.clicked.connect(self._removeItem)

    def _addTrigger(self, _):
        text, response = QInputDialog.getText(
            self,
            "New Trigger",
            "Enter Trigger Name:"
        )
        if response:
            if not self.triggerTree.trigger_exists(text):
                self.triggerTree.add_new_trigger(text)

    def _addGroup(self, _=None):
        text, response = QInputDialog.getText(
            self,
            "New Group",
            "Enter New Group Name:"
        )
        if response:
            # todo read from model
            if not self.triggerTree.group_exists(text):
                self.triggerTree.add_new_group(text)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    "Warning", "{} group already exists.".format(text),
                    QMessageBox.Ok
                ).exec()
                self._addGroup()

    def _removeItem(self, _=None):
        if self.triggerTree.is_group_selected():
            r = QMessageBox.question(
                self,
                "Are you sure?",
                "Selected item is a group.  Remove group and all triggers it contains?"
            )
            if r == QMessageBox.No:
                return
        self.triggerTree.remove_selected()

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
        config.triggers = self.triggerTree.get_values()
        config.save()

    def set_values(self):
        for section, references in self._ref.items():
            for setting, widget in references.items():
                wt = type(widget)
                if wt == QCheckBox:
                    widget.setChecked(config.data[section][setting])
                elif wt == QSpinBox:
                    widget.setValue(config.data[section][setting])
        
        # Remove triggertree if it exists and reinsert it
        try:
            self.treeViewLayout.removeWidget(self.triggerTree)
        except:
            pass
        self.triggerTree = TriggerTree()
        self.triggerTree.edit_trigger.connect(self._edit_selected_trigger)
        self.treeViewLayout.insertWidget(0, self.triggerTree, 1)

    def _edit_selected_trigger(self):
        # if group, do nothing
        # if trigger, edit
        if not self.triggerTree.is_group_selected():
            try:
                item = self.triggerTree.selectedItems()[0]
                te = TriggerEditor(item.text(0), item.value)
                r = te.exec()
                if r:
                    updated = te.value()
                    if not self.triggerTree.trigger_exists(updated['name']):
                        item.setText(0, updated['name'])
                    item.value = updated['data']
                    item.setCheckState(
                        0,
                        Qt.Checked if updated['data']['__enabled__'] else Qt.Unchecked
                    )
            except IndexError:
                pass

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
