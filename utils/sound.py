from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from utils import logger

log = logger.get_logger(__name__)


player = QMediaPlayer(flags=QMediaPlayer.LowLatency)


def play(mp3_data: QMediaContent, volume: int = 100):
    try:
        player.setMedia(mp3_data)
        player.setVolume(volume)
        player.play()
    except Exception as e:
        log.warning(f"Unable to play sound. {e}", exc_info=True)
