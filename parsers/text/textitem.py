from datetime import datetime

from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer

from helpers import config

from .common import TextAction


class TextItem(QGraphicsTextItem):

    def __init__(self, text_action: TextAction) -> None:
        super().__init__()
        self.action = text_action
        self.timestamp = datetime.now()
        self._opacity = self.action.color[-1]/255
        self._update_frequency = 30
        self._direction = 1 if config.data['text']['direction'] == 'down' else -1

        self.setPlainText(text_action.text)
        self.setDefaultTextColor(QColor(*self.action.color))
        self.setFont(
            QFont('Arial', self.action.text_size)
        )
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(config.data['text']['shadow_radius'])
        effect.setOffset(0, 0)
        effect.setColor(QColor(*config.data['text']['shadow_color']))
        self.setGraphicsEffect(effect)
        self.setOpacity(self._opacity)

        QTimer.singleShot(self._update_frequency, self._update)

    def _update(self) -> None:
        seconds = (datetime.now() - self.timestamp).total_seconds()
        if seconds > config.data['text']['fade_seconds']:
            self._remove()
        else:
            self.moveBy(
                0,
                config.data['text']['pixels_per_second']*0.03 * self._direction
            )
            self.setOpacity(
                self._opacity - (
                        self._opacity
                        * (seconds/config.data['text']['fade_seconds'])
                   )
            )
            QTimer.singleShot(self._update_frequency, self._update)

    def _remove(self) -> None:
        self.setParent(None)
        self.deleteLater()
