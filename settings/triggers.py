from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox
from PyQt5.QtGui import QIcon, QMouseEvent
from PyQt5.QtCore import Qt

from helpers import config, resource_path

from .triggereditor import TriggerEditor


class TriggerTree(QTreeWidget):

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.InternalMove)

        self.root = self.invisibleRootItem()
        # do not allow drag and drop to root
        self.root.setFlags(self.root.flags() ^ Qt.ItemIsDropEnabled)

        self._fill()

    def _fill(self):

        for group in config.triggers.keys():
            tg = TriggerGroup(group_name=group)
            tg.setCheckState(
                0,
                Qt.Checked if config.triggers[group]['enabled'] else Qt.Unchecked
            )
            for trig in config.triggers[group]['triggers']:
                qtrig = TriggerItem(
                    trigger_name=trig,
                    trigger_data=config.triggers[group]['triggers'][trig]
                )
                qtrig.setCheckState(
                    0,
                    Qt.Checked if config.triggers[group]['triggers'][trig]['enabled'] else Qt.Unchecked
                )
                tg.addChild(qtrig)
            self.root.addChild(tg)

    def is_group_selected(self):
        try:
            return (
                True
                if isinstance(self.selectedItems()[0], TriggerGroup)
                else False
            )
        except IndexError:
            return False

    def add_new_trigger(self, trigger_name: str) -> None:
        d = {'enabled': False}
        qtrig = TriggerItem(trigger_name=trigger_name, trigger_data=d)
        qtrig.setCheckState(0, Qt.Unchecked)
        selected_item = None
        try:
            selected_item = self.selectedItems()[0]
            if not selected_item.parent():
                selected_item.addChild(qtrig)
            else:
                selected_item = selected_item.parent()
                selected_item.addChild(qtrig)
        except:
            if self.root.childCount() > 0:
                selected_item = self.root.child(0)
                selected_item.addChild(qtrig)
        if selected_item:
            selected_item.sortChildren(0, Qt.AscendingOrder)

    def add_new_group(self, group_name):
        qgroup = TriggerGroup(group_name=group_name)
        qgroup.setCheckState(0, Qt.Checked)
        self.root.addChild(qgroup)
        self.root.sortChildren(0, Qt.AscendingOrder)

    def remove_selected(self):
        try:
            self.root.removeChild(
                self.selectedItems()[0]
            )
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
                menu.addAction('New Trigger', self._add_new_trigger)
                menu.addAction('Delete Group', self._delete_item)
            elif isinstance(item, TriggerItem):
                menu.addAction('Edit Trigger', self._edit_trigger)
                menu.addAction('Delete Trigger', self._delete_item)
            elif isinstance(item, type(None)):
                menu.addAction('New Group', self._add_new_group)
            menu.exec(event.globalPos())
            menu.deleteLater()


    def get_values(self):
        # Return a dict structure for triggers
        d = {}
        for qgroup in [self.root.child(x) for x in range(self.root.childCount())]:
            group_name = qgroup.text(0)
            d[group_name] = {}
            d[group_name]['enabled'] = True if qgroup.checkState(0) == Qt.Checked else False
            d[group_name]['triggers'] = {}
            for qtrig in [qgroup.child(i) for i in range(qgroup.childCount())]:
                trig_name = qtrig.text(0)
                d[group_name]['triggers'][trig_name] = {}
                d[group_name]['triggers'][trig_name] = qtrig.value
                d[group_name]['triggers'][trig_name]['enabled'] = True if qtrig.checkState(0) == Qt.Checked else False
        return d

    def trigger_exists(self, trigger_name):
        for qgroup in [self.root.child(x) for x in range(self.root.childCount())]:
            for qtrig in [qgroup.child(i) for i in range(qgroup.childCount())]:
                if trigger_name == qtrig.text(0):
                    return True
        return False

    def group_exists(self, group_name):
        for qgroup in [self.root.child(x) for x in range(self.root.childCount())]:
            if qgroup.text(0) == group_name:
                return True
        return False

    def dataChanged(self, *args):
        try:
            item = self.itemFromIndex(args[0])
            if item.parent():
                item.value['enabled'] = True if item.checkState(0) == Qt.Checked else False
        except:
            pass

    def dropEvent(self, event):
        self.root.sortChildren(0, Qt.AscendingOrder)
        QTreeWidget.dropEvent(self, event)

    def _add_new_trigger(self) -> None:
        text, response = QInputDialog.getText(
            self,
            "New Trigger",
            "Enter Trigger Name:"
        )
        if response:
            if not self.trigger_exists(text):
                self.add_new_trigger(text)

    def _add_new_group(self) -> None:
        text, response = QInputDialog.getText(
            self,
            "New Group",
            "Enter New Group Name:"
        )
        if response:
            if not self.group_exists(text):
                self.add_new_group(text)
            else:
                QMessageBox(
                    QMessageBox.Warning,
                    "Warning", "{} group already exists.".format(text),
                    QMessageBox.Ok
                ).exec()
                self._addGroup()

    def _delete_item(self, _=None):
        if self.is_group_selected():
            r = QMessageBox.question(
                self,
                "Are you sure?",
                "Selected item is a group.  Remove group and all triggers it contains?"
            )
            if r == QMessageBox.No:
                return
        self.remove_selected()

    def _edit_trigger(self):
        if not self.is_group_selected():
            try:
                item = self.selectedItems()[0]
                te = TriggerEditor(
                    self,
                    trigger_name=item.text(0),
                    trigger_data=item.value,
                )
                r = te.exec()
                te.setParent(None)
                te.deleteLater()
                if r:
                    updated = te.value()
                    if not self.trigger_exists(updated['name']):
                        item.setText(0, updated['name'])
                    item.value = updated['data']
                    item.setCheckState(
                        0,
                        Qt.Checked if updated['data']['enabled'] else Qt.Unchecked
                    )
            except IndexError:
                pass


class TriggerGroup(QTreeWidgetItem):

    def __init__(self, group_name=None):
        super().__init__()
        self.setIcon(0, QIcon(resource_path('data/ui/folder.png')))
        self.setText(0, group_name)
        self.setFlags(self.flags() | Qt.ItemIsDropEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        self.setFlags(self.flags() ^ Qt.ItemIsDragEnabled)


class TriggerItem(QTreeWidgetItem):

    def __init__(self, trigger_name=None, trigger_data={}):
        super().__init__()
        self.setText(0, trigger_name)
        self.value = trigger_data
        self.setFlags(self.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsUserCheckable)
        self.setFlags(self.flags() ^ Qt.ItemIsDropEnabled)
