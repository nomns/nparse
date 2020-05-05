from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

from helpers import config


player = QMediaPlayer(flags=QMediaPlayer.LowLatency)


def play(filename):
    try:
        player.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
        player.setVolume(config.data['general']['sound_volume'])
        player.play()
    except Exception as e:
        print(e)
