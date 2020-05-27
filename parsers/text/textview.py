from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QRectF

from config import profile

from .textitem import TextItem


class TextView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TextView")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(self.AnchorViewCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self._scene = QGraphicsScene()
        # need to set Scene size to View size
        self._scene.setSceneRect(QRectF(self.rect()))
        self.setScene(self._scene)

    def add(self, text_item: TextItem) -> None:
        offset = text_item.boundingRect()
        if profile.text.direction == "down":
            text_item.setPos(self.mapToScene(self.width() / 2 - offset.width() / 2, 0))
        else:
            text_item.setPos(
                self.mapToScene(
                    self.width() / 2 - offset.width() / 2,
                    self.height() - offset.height(),
                )
            )
        self._scene.addItem(text_item)

    def clear(self):
        self._scene.clear()
