from typing import List

from PyQt5.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QInputDialog,
    QMessageBox,
)
from PyQt5.QtGui import QIcon, QMouseEvent
from PyQt5.QtCore import Qt

from utils import resource_path
from config import profile_manager, trigger_manager

profile = profile_manager.profile
triggers = trigger_manager.triggers

from .triggereditor import TriggerEditor
from ..trigger import Trigger, TriggerContainer


class TriggerGroup(QTreeWidgetItem):
    def __init__(self, group_name=None):
        super().__init__()
        self.setIcon(0, QIcon(resource_path("data/ui/folder.png")))
        self.setText(0, group_name)
        self.setFlags(
            self.flags()
            | Qt.ItemIsDropEnabled
            | Qt.ItemIsUserCheckable
            | Qt.ItemIsEditable
        )
        self.setFlags(self.flags() ^ Qt.ItemIsDragEnabled)


class TriggerItem(QTreeWidgetItem):
    def __init__(self, trigger: Trigger):
        super().__init__()
        self.setText(0, trigger.name)
        self.trigger = trigger
        self.setFlags(self.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsUserCheckable)
        self.setFlags(self.flags() ^ Qt.ItemIsDropEnabled)


class TriggerTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.InternalMove)

        self.root = self.invisibleRootItem()
        # do not allow drag and drop to root
        self.root.setFlags(self.root.flags() ^ Qt.ItemIsDropEnabled)

        self.setAnimated(True)

        self._fill(triggers)

    def _fill(self, triggers: List[any]):
        for container in triggers:
            tg = TriggerGroup(group_name=container.name)
            self._fill_trigger_group(container.items, tg)
            self.root.addChild(tg)

    def _fill_trigger_group(
        self, triggers: List[any] = None, trigger_group: TriggerGroup = None
    ):
        for item in triggers:
            if type(item) == Trigger:
                trigger_group.addChild(TriggerItem(item))
            elif type(item) == TriggerContainer:
                tg = TriggerGroup(group_name=item.name)
                self._fill_trigger_group(item.items, tg)
                trigger_group.addChild(tg)

    def is_group_selected(self):
        try:
            return True if isinstance(self.selectedItems()[0], TriggerGroup) else False
        except IndexError:
            return False

    def add_new_trigger(self, trigger_name: str) -> None:
        d = {"enabled": False}
        trigger_item = TriggerItem(trigger_name=trigger_name, trigger_data=d)
        trigger_item.setCheckState(0, Qt.Unchecked)
        selected_item = None
        try:
            selected_item = self.selectedItems()[0]
            if not selected_item.parent():
                selected_item.addChild(trigger_item)
            else:
                selected_item = selected_item.parent()
                selected_item.addChild(trigger_item)
        except:
            if self.root.childCount() > 0:
                selected_item = self.root.child(0)
                selected_item.addChild(trigger_item)
        if selected_item:
            selected_item.sortChildren(0, Qt.AscendingOrder)

    def add_new_group(self, group_name):
        group = TriggerGroup(group_name=group_name)
        group.setCheckState(0, Qt.Checked)
        self.root.addChild(group)
        self.root.sortChildren(0, Qt.AscendingOrder)

    def remove_selected(self):
        try:
            self.root.removeChild(self.selectedItems()[0])
        except IndexError:
            pass

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, TriggerItem):
                self._edit_trigger()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            menu = QMenu()
            if isinstance(item, TriggerGroup):
                menu.addAction("New Trigger", self._add_new_trigger)
                menu.addAction("Delete Group", self._delete_item)
            elif isinstance(item, TriggerItem):
                menu.addAction("Edit Trigger", self._edit_trigger)
                menu.addAction("Delete Trigger", self._delete_item)
            elif isinstance(item, type(None)):
                menu.addAction("New Group", self._add_new_group)
            menu.exec(event.globalPos())
            menu.deleteLater()

    def get_values(self):
        # Return a dict structure for triggers
        d = {}
        for group in [self.root.child(x) for x in range(self.root.childCount())]:
            group_name = group.text(0)
            d[group_name] = {}
            d[group_name]["enabled"] = (
                True if group.checkState(0) == Qt.Checked else False
            )
            d[group_name]["triggers"] = {}
            for trigger in [group.child(i) for i in range(group.childCount())]:
                trigger_name = trigger.text(0)
                d[group_name]["triggers"][trigger_name] = {}
                d[group_name]["triggers"][trigger_name] = trigger.value
                d[group_name]["triggers"][trigger_name]["enabled"] = (
                    True if trigger.checkState(0) == Qt.Checked else False
                )
        return d

    def trigger_exists(self, trigger_name):
        for group in [self.root.child(x) for x in range(self.root.childCount())]:
            for trigger in [group.child(i) for i in range(group.childCount())]:
                if trigger_name == trigger.text(0):
                    return True
        return False

    def group_exists(self, group_name):
        for group in [self.root.child(x) for x in range(self.root.childCount())]:
            if group.text(0) == group_name:
                return True
        return False

    def dataChanged(self, *args):
        try:
            item = self.itemFromIndex(args[0])
            if item.parent():
                item.value["enabled"] = (
                    True if item.checkState(0) == Qt.Checked else False
                )
        except:
            pass

    def dropEvent(self, event):
        self.root.sortChildren(0, Qt.AscendingOrder)
        QTreeWidget.dropEvent(self, event)

    def _add_new_trigger(self) -> None:
        text, response = QInputDialog.getText(
            self, "New Trigger", "Enter Trigger Name:"
        )
        if response:
            if not self.trigger_exists(text):
                self.add_new_trigger(text)

    def _add_new_group(self) -> None:
        text, response = QInputDialog.getText(
            self, "New Group", "Enter New Group Name:"
        )
        if response:
            if not self.group_exists(text):
                self.add_new_group(text)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    "Warning",
                    "{} group already exists.".format(text),
                    QMessageBox.Ok,
                ).exec()
                self._addGroup()

    def _delete_item(self, _=None):
        if self.is_group_selected():
            r = QMessageBox.question(
                self,
                "Are you sure?",
                "Selected item is a group.  Remove group and all triggers it contains?",
            )
            if r == QMessageBox.No:
                return
        self.remove_selected()

    def _edit_trigger(self):
        if not self.is_group_selected():
            try:
                item = self.selectedItems()[0]
                te = TriggerEditor(
                    self, item.trigger
                )
                r = te.exec()
                te.setParent(None)
                te.deleteLater()
                if r:
                    updated = te.value()
                    if not self.trigger_exists(updated["name"]):
                        item.setText(0, updated["name"])
                    item.value = updated["data"]
                    item.setCheckState(
                        0, Qt.Checked if updated["data"]["enabled"] else Qt.Unchecked
                    )
            except IndexError:
                pass
