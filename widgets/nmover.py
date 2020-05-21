from PyQt5.QtWidgets import (QWidget, QVBoxLayout,
                             QLabel, QSizeGrip)
from PyQt5.QtCore import Qt


class NMover(QWidget):

    def __init__(self, name=None, parent=None):
        super().__init__()

        self._parent = parent
        self._layout = QVBoxLayout()
        self._title = QLabel(name.title())
        self._title.setText(name.title())
        self._title.setObjectName("NMoverTitle")
        self._layout.addWidget(
            self._title,
            1,
            Qt.AlignHCenter | Qt.AlignCenter
        )
        self.setLayout(self._layout)

        self._grip = None
        self._offset = None

    def clear_grip(self):
        self._layout.removeWidget(self._grip)
        self._grip.setParent(None)
        self._grip = None

    def show_grip(self):
        self._grip = QSizeGrip(self._parent)
        self._layout.addWidget(
            self._grip,
            0,
            Qt.AlignBottom | Qt.AlignRight
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._offset = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._offset = None
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        self.setCursor(Qt.SizeAllCursor)
        super().enterEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._offset is not None and event.buttons() == Qt.LeftButton:
            self._parent.move(self._parent.pos() + event.pos() - self._offset)
        super().mouseMoveEvent(event)
