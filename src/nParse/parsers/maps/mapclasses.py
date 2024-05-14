import datetime

import colorhash
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPixmap, QPen
from PySide6.QtWidgets import (QGraphicsItemGroup, QGraphicsLineItem,
                             QGraphicsPixmapItem, QGraphicsTextItem)

from nParse.helpers import format_time, get_degrees_from_line, to_eq_xy


class MouseLocation(QGraphicsTextItem):

    def __init__(self, **_):
        super().__init__()
        self.setZValue(100)

    def set_value(self, pos, scale, view):
        # pos = QGraphicsView.mapToScale return of mouse event pos()
        # view = QGraphicsView of the scene view
        x, y = to_eq_xy(pos.x(), pos.y())

        self.setHtml(
            "<font color='white' size='4'>{}, {}</font>".format(
                str(int(x)), str(int(y))
            )
        )

        # move hover to left if it goes out of view
        scene_rect = view.mapToScene(view.viewport().rect()).boundingRect()
        visible_x = -(scene_rect.x() + scene_rect.width())
        my_rect = self.mapRectToScene(self.boundingRect())
        if y + -(15/scale + my_rect.width()) < visible_x:
            self.setPos(pos.x() - 15/scale - my_rect.width(), pos.y())
        else:
            self.setPos(pos.x() + 15/scale, pos.y())

        self.setScale(1/scale)


class PointOfInterest:

    def __init__(self, **kwargs):
        super().__init__()
        self.location = MapPoint()
        self.__dict__.update(kwargs)
        self.text = QGraphicsTextItem()
        self.text.setHtml(
            "<font color='{}' size='{}'>{}</font>".format(
                self.location.color.name(),
                1 + self.location.size,
                '\u272a' + self.location.text
            )
        )
        self.text.setZValue(2)
        self.text.setPos(self.location.x, self.location.y)

    def update_(self, scale):
        self.text.setScale(scale)
        self.text.setPos(
            self.location.x - self.text.boundingRect().width() * 0.05 * scale,
            self.location.y - self.text.boundingRect().height() / 2 * scale
        )


class Player(QGraphicsItemGroup):

    def __init__(self, **kwargs):
        super().__init__()
        self.name = ''
        self.location = MapPoint()
        self.previous_location = MapPoint()
        self.timestamp = None  # datetime
        self.__dict__.update(kwargs)
        if self.name == "__you__":
            self.icon = QGraphicsPixmapItem(
                QPixmap('data/maps/user.png')
            )
            self.setZValue(15)
        else:
            self.icon = QGraphicsPixmapItem(
                QPixmap('data/maps/otheruser.png')
            )
            self.setZValue(10)
        self.icon.setOffset(-10, -10)
        self.directional = QGraphicsPixmapItem(
            QPixmap('data/maps/directional.png')
        )
        self.directional.setOffset(-15, -15)
        self.directional.setVisible(False)
        self.nametag = QGraphicsTextItem()
        self.nametag.setPos(10, -15)
        self.addToGroup(self.icon)
        self.addToGroup(self.directional)
        self.addToGroup(self.nametag)
        self.z_level = 0
        self.color = colorhash.ColorHash(self.name)

    def update_(self, scale):
        if self.previous_location:
            self.directional.setRotation(
                get_degrees_from_line(
                    self.location.x, self.location.y,
                    self.previous_location.x, self.previous_location.y
                )
            )
            self.setScale(scale)
            self.setPos(self.location.x, self.location.y)
            self.directional.setVisible(True)
        self.setPos(self.location.x, self.location.y)
        self.nametag.setHtml(
            "<font color='{}' size='{}'>{}</font>".format(
                self.color.hex if self.name != "__you__" else "purple",
                5,
                self.name if self.name != "__you__" else "You"
            )
        )


class SpawnPoint(QGraphicsItemGroup):

    def __init__(self, **kwargs):
        super().__init__()
        self.location = MapPoint()
        self.length = 10
        self.name = 'pop'
        self.__dict__.update(**kwargs)
        self.setToolTip(self.name)

        pixmap = QGraphicsPixmapItem(QPixmap('data/maps/spawn.png'))
        text = QGraphicsTextItem('0')

        self.addToGroup(pixmap)
        self.addToGroup(text)
        self.setPos(self.location.x, self.location.y)

        self.setZValue(18)

        self.pixmap = pixmap
        self.text = text

        self.timer = QTimer()

    def _update(self):
        if self.timer:
            remaining = self._end_time - datetime.datetime.now()
            remaining_seconds = remaining.total_seconds()
            if remaining_seconds < 0:
                self.stop()
            elif remaining_seconds <= 30:
                self.text.setHtml(
                    "<font color='red' size='5'>{}</font>".format(
                        format_time(remaining))
                )
            else:
                self.text.setHtml(
                    "<font color='white'>{}</font>".format(
                        format_time(remaining))
                )
            self.realign()

            if remaining_seconds > 0 and self.timer:
                self.timer.singleShot(1000, self._update)

    def realign(self, scale=None):
        if scale:
            self.setPos(self.location.x - self.boundingRect().width() / 2 * scale,
                        self.location.y - self.boundingRect().height() / 2 * scale)
        self.text.setPos(-self.text.boundingRect().width() /
                         2 + self.pixmap.boundingRect().width() / 2, 15)

    def start(self, _=None, timestamp=None):
        timestamp = timestamp if timestamp else datetime.datetime.now()
        self._end_time = timestamp + datetime.timedelta(seconds=self.length)
        if self.timer:
            self._update()

    def stop(self):
        self.text.setHtml(
            "<font color='green' align='center'>{}</font>".format(self.name.upper()))

    def mouseDoubleClickEvent(self, _):
        self.start()


class MapPoint:
    def __init__(self, **kwargs):
        self.x = 0
        self.y = 0
        self.z = 0
        self.color = None  # QColor
        self.size = 0
        self.text = ''
        self.__dict__.update(kwargs)


class UserWaypoint(QGraphicsItemGroup):
    def __init__(self, name, icon, location):
        super().__init__()
        self.location = location
        self.name = name
        self.z_level = 0
        self.color = colorhash.ColorHash(self.name)

        self.pixmap = QGraphicsPixmapItem(QPixmap(icon))
        self.pixmap.setOffset(-10, -10)
        self.text = QGraphicsTextItem()
        self.text.setHtml(
            "<font color='{}' size='{}'>{}</font>".format(
                self.color.hex,
                5,
                self.name
            )
        )
        self.text.setPos(10, -15)
        self.setToolTip(self.name)

        self.addToGroup(self.pixmap)
        self.addToGroup(self.text)
        self.setPos(self.location.x, self.location.y)

        self.setZValue(12)

    def update_(self, scale):
        self.setScale(scale)


class WayPoint:

    def __init__(self, **kwargs):
        super().__init__()
        self.location = MapPoint()
        self.__dict__.update(kwargs)

        self.pixmap = QGraphicsPixmapItem(QPixmap('data/maps/waypoint.png'))
        self.pixmap.setOffset(-10, -20)

        self.line = QGraphicsLineItem(
            0.0, 0.0, self.location.x, self.location.y)
        self.line.setPen(QPen(
            Qt.GlobalColor.green, 1, Qt.PenStyle.DashLine
        ))
        self.line.setVisible(False)

        self.pixmap.setZValue(5)
        self.line.setZValue(4)

        self.pixmap.setPos(self.location.x, self.location.y)

    def update_(self, scale, location=None):
        self.pixmap.setScale(scale)
        if location:
            line = self.line.line()
            line.setP1(QPointF(location.x, location.y))
            self.line.setLine(line)

            pen = self.line.pen()
            pen.setWidth(int(1 / scale))
            self.line.setPen(pen)

            self.line.setVisible(True)


class MapLine:
    def __init__(self, **kwargs):
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.z1 = 0
        self.color = None  # QColor
        self.__dict__.update(kwargs)


class MapGeometry:
    def __init__(self, **kwargs):
        self.lowest_x = 0
        self.highest_x = 0
        self.lowest_y = 0
        self.highest_y = 0
        self.highest_z = 0
        self.lowest_z = 0
        self.center_x = 0
        self.center_y = 0
        self.width = 0
        self.height = 0
        self.z_groups = []  # [(number:int, count:int)]
        self.__dict__.update(kwargs)
