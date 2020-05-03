from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from helpers import config, resource_path


class TriggerTree(QTreeWidget):

    edit_trigger = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setContentsMargins(0, 0, 0, 0)

        self.root = self.invisibleRootItem()
        # do not allow drag and drop to root
        self.root.setFlags(self.root.flags() ^ Qt.ItemIsDropEnabled)

        # Events
        self.doubleClicked.connect(self._double_click)

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

    def add_new_trigger(self, trigger_name):
        d = {'enabled': False}
        qtrig = TriggerItem(trigger_name=trigger_name, trigger_data=d)
        qtrig.setCheckState(0, Qt.Unchecked)
        try:
            selected_item = self.selectedItems()[0]
            if not selected_item.parent():
                selected_item.addChild(qtrig)
            else:
                selected_item = selected_item.parent()
                selected_item.addChild(qtrig)
        except:
            if self.root.childCount() > 0:
                qgroup = self.root.child(0)
                qgroup.addChild(qtrig)

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

    def _double_click(self, event):
        self.edit_trigger.emit()

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
