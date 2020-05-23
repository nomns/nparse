from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QByteArray

from utils import logger
log = logger.get_logger(__name__)

from config import profile_manager
profile = profile_manager.profile


player = QMediaPlayer(flags=QMediaPlayer.LowLatency)


def play(mp3_data: QByteArray):
    try:
        player.setMedia(QMediaContent(QUrl.fromEncoded(mp3_data)))
        player.setVolume(profile.sound_volume)
        player.play()
    except Exception as e:
        log.warning(f'Unable to play sound. {e}', exc_info=True)
