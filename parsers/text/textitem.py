from datetime import datetime

from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer

from config import profile
from config.triggers.trigger import TriggerText


class TextItem(QGraphicsTextItem):
    def __init__(self, text: str, trigger_text: TriggerText) -> None:
        super().__init__()
        self.trigger_text = trigger_text
        self.timestamp = datetime.now()
        self._opacity = trigger_text.color[-1] / 255
        self._update_frequency = 30
        self._direction = 1 if profile.text.direction == "down" else -1

        self.setPlainText(text)
        self.setDefaultTextColor(QColor(*trigger_text.color))
        self.setFont(QFont("Arial", trigger_text.text_size))
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(profile.text.shadow_blur_radius)
        effect.setOffset(0, 0)
        effect.setColor(QColor(*profile.text.shadow_color))
        self.setGraphicsEffect(effect)
        self.setOpacity(self._opacity)

        QTimer.singleShot(self._update_frequency, self._update)

    def _update(self) -> None:
        seconds = (datetime.now() - self.timestamp).total_seconds()
        if seconds > profile.text.fade_seconds:
            self._remove()
        else:
            self.moveBy(0, profile.text.pixels_per_second * 0.03 * self._direction)
            self.setOpacity(
                self._opacity - (self._opacity * (seconds / profile.text.fade_seconds))
            )
            QTimer.singleShot(self._update_frequency, self._update)

    def _remove(self) -> None:
        self.setParent(None)
        self.deleteLater()
