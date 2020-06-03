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

from utils import resource_path, get_unique_str
from config import profile, trigger_manager

from .triggereditor import TriggerEditor
from ..triggers.trigger import Trigger, TriggerContainer, TriggerChoice
from ..triggers.triggerpackage import TriggerPackage


class TriggerGroup(QTreeWidgetItem):
    def __init__(self, container: any):
        super().__init__()
        self.container = container
        self.setIcon(0, QIcon(resource_path("data/ui/folder.png")))
        self.setText(0, container.name)
        self.setFlags(
            self.flags()
            | Qt.ItemIsDropEnabled
            | Qt.ItemIsUserCheckable
            | Qt.ItemIsEditable
        )
        self.setFlags(self.flags() ^ Qt.ItemIsDragEnabled)

    def __lt__(self, other_item):
        other_text = other_item.text(0).lower()
        if isinstance(other_item, TriggerGroup):
            other_text = f"_{other_text}"
        return f"_{self.text(0).lower()}" < other_text

    def get_package(self):
        if isinstance(self.container, TriggerPackage):
            return self.container
        else:
            return self.parent().get_package()


class TriggerItem(QTreeWidgetItem):
    def __init__(self, trigger: Trigger):
        super().__init__()
        self.setText(0, trigger.name)
        self.trigger = trigger
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setFlags(self.flags() ^ (Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled))

    def __lt__(self, other_item):
        return self.text(0).lower() < other_item.text(0).lower()


class TriggerTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.InternalMove)

        self.root: QTreeWidgetItem = self.invisibleRootItem()
        # do not allow drag and drop to root
        self.root.setFlags(self.root.flags() ^ Qt.ItemIsDropEnabled)

        self.setAnimated(True)

        for container in trigger_manager:
            tg = TriggerGroup(container)
            tg.setCheckState(0, Qt.Unchecked)
            self._fill_trigger_group(container.items, tg)
            self.root.addChild(tg)
        self.root.sortChildren(0, Qt.AscendingOrder)

        self.set_choices()
        self.expandAll()

    def _fill_trigger_group(self, items: List[any] = None, group: TriggerGroup = None):
        for item in items:
            if isinstance(item, Trigger):
                trigger_item = TriggerItem(item)
                trigger_item.setCheckState(0, Qt.Unchecked)
                group.addChild(trigger_item)
            elif isinstance(item, TriggerContainer):
                tg = TriggerGroup(item)
                tg.setCheckState(0, Qt.Unchecked)
                self._fill_trigger_group(item.items, tg)
                group.addChild(tg)
        group.sortChildren(0, Qt.AscendingOrder)

    def get_choices(self, item: QTreeWidgetItem = None):
        choices = []
        if not item:
            item = self.root
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(child, TriggerGroup):
                choices.append(
                    TriggerChoice(
                        name=child.container.name,
                        enabled=True if child.checkState(0) else False,
                        group=self.get_choices(child),
                    )
                )
            elif isinstance(child, TriggerItem):
                choices.append(
                    TriggerChoice(
                        name=child.trigger.name,
                        enabled=True if child.checkState(0) else False,
                        type_="trigger",
                    )
                )
        return choices

    def set_choices(
        self, item: QTreeWidgetItem = None, choices: List[TriggerChoice] = None
    ):
        if not item:
            item = self.root
            choices = profile.trigger_choices
        for choice in choices:
            for i in range(item.childCount()):
                child = item.child(i)
                if isinstance(child, TriggerGroup):
                    if child.container.name == choice.name and choice.type_ == "group":
                        child.setCheckState(
                            0, Qt.Checked if choice.enabled else Qt.Unchecked
                        )
                        if choice.group:
                            self.set_choices(child, choice.group)
                else:
                    if child.trigger.name == choice.name and choice.type_ == "trigger":
                        child.setCheckState(
                            0, Qt.Checked if choice.enabled else Qt.Unchecked
                        )

    def remove_selected(self):
        if self.selectedItems():
            item = self.selectedItems()[0]
            parent_item = item.parent()
            trigger_object = (
                item.container if isinstance(item, TriggerGroup) else item.trigger
            )
            if not parent_item:
                trigger_manager.delete(trigger_object)
                self.root.removeChild(item)
            else:
                parent_item.container.items.remove(trigger_object)
                item.parent().removeChild(item)

    def add_new_trigger(self, trigger: Trigger, group: TriggerGroup) -> None:
        trigger_item = TriggerItem(trigger)
        trigger_item.setCheckState(0, Qt.Unchecked)
        group.addChild(trigger_item)
        group.container.items.append(trigger_item.trigger)
        group.sortChildren(0, Qt.AscendingOrder)

    def add_new_group(self, name: str, parent: any) -> None:
        if isinstance(parent, TriggerGroup):
            container = TriggerContainer(name=name)
            parent.container.items.append(container)
        else:
            container = TriggerPackage(name=name)
            trigger_manager.append(container)
        group = TriggerGroup(container)
        group.setCheckState(0, Qt.Checked)
        parent.addChild(group)
        parent.sortChildren(0, Qt.AscendingOrder)

    def trigger_exists(self, name: str, parent: any) -> bool:
        for item in [parent.child(x) for x in range(parent.childCount())]:
            if type(item) == TriggerItem:
                if item.trigger.name == name:
                    return True
        return False

    def group_exists(self, name: str, parent: any) -> bool:
        for item in [parent.child(x) for x in range(parent.childCount())]:
            if type(item) == TriggerGroup:
                if item.container.name == name:
                    return True
        return False

    # Events

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

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            if type(self.itemAt(event.pos())) == TriggerItem:
                self.menuEditTriggerClicked()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            menu = QMenu()
            if isinstance(item, TriggerGroup):
                menu.addAction("New Trigger", self.menuAddNewTriggerClicked)
                menu.addAction("New Group", self.menuAddNewGroupClicked)
                if isinstance(item.container, TriggerPackage):
                    menu.addAction("Delete Package", self.menuDeletePackageClicked)
                else:
                    menu.addAction("Delete Group", self.menuDeleteGroupClicked)
            elif isinstance(item, TriggerItem):
                menu.addAction("Edit Trigger", self.menuEditTriggerClicked)
                menu.addAction("Delete Trigger", self.menuDeleteTriggerClicked)
            elif isinstance(item, type(None)):
                menu.addAction("New Package", self.menuAddNewPackageClicked)
            menu.exec(event.globalPos())
            menu.deleteLater()

    def menuAddNewGroupClicked(self) -> None:
        name, response = QInputDialog.getText(
            self, "New Group", "Enter New Group Name:"
        )
        if name and response:
            item = self.selectedItems()[0] if self.selectedItems() else None
            parent = item if type(item) == TriggerGroup else self.root
            if type(item) == TriggerGroup:
                parent = item
            if not self.group_exists(name, parent):
                self.add_new_group(name, parent)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    "Warning",
                    f"Group already exists: {name}",
                    QMessageBox.Ok,
                ).exec()

    def menuAddNewPackageClicked(self) -> None:
        name, response = QInputDialog.getText(
            self, "New Package", "Enter New Package Name:"
        )
        if name and response:
            parent = self.root
            if not self.group_exists(name, parent):
                self.add_new_group(name, parent)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    "Warning",
                    f"Package already exists: {name}",
                    QMessageBox.Ok,
                ).exec()

    def menuAddNewTriggerClicked(self) -> None:
        group: TriggerGroup = self.selectedItems()[0]
        trigger = Trigger()
        trigger.package = group.get_package()
        trigger_editor = TriggerEditor(self, trigger)
        results = trigger_editor.exec()
        if results:
            trigger = trigger_editor.get_trigger()
            if self.trigger_exists(trigger.name, group):
                trigger.name = get_unique_str(
                    trigger.name,
                    [
                        group.child(x).trigger.name
                        for x in range(group.childCount())
                        if type(group.child(x)) == TriggerItem
                    ],
                )
            self.add_new_trigger(trigger, group)

    def menuDeleteGroupClicked(self) -> None:
        result = QMessageBox.question(
            self,
            "Are you sure?",
            "Selected item is a group.  Remove group and all triggers it contains?",
        )
        if result == QMessageBox.No:
            return
        self.remove_selected()

    def menuDeletePackageClicked(self) -> None:
        result = QMessageBox.question(
            self,
            "Are you sure?",
            (
                "Selected item is a package. "
                "Remove package and all triggers and sound files it contains?"
            ),
        )
        if result == QMessageBox.No:
            return
        self.remove_selected()

    def menuDeleteTriggerClicked(self, _=None):
        self.remove_selected()

    def menuEditTriggerClicked(self):
        item = self.selectedItems()[0]
        parent = item.parent()
        te = TriggerEditor(self, item.trigger)
        r = te.exec()
        te.setParent(None)
        te.deleteLater()
        if r:
            updated = te.get_trigger()
            if self.trigger_exists(updated.name, parent):
                updated.name = get_unique_str(
                    updated.name,
                    [
                        parent.child(x).trigger.name
                        for x in range(parent.childCount())
                        if (
                            (type(parent.child(x)) == TriggerItem)
                            and (parent.child(x) != item)
                        )
                    ],
                )
            item.trigger = updated
            item.setText(0, updated.name)
