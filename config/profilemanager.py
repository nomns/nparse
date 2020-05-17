import os
import glob
from typing import Dict

from .config import Config
from .profile import Profile
from helpers import logger

app_config = Config()
log = logger.get_logger(__name__)


class ProfileManager:

    def __init__(self) -> None:
        self.profile: Profile = Profile()
        self.profiles: Dict[str, any] = {}
        if not os.path.exists('./data/profiles'):
            os.mkdir('./data/profiles')
        self.scan()

    def scan(self) -> None:
        self.profiles = {}
        for f in glob.glob(os.path.join(app_config.eq_dir, '/Logs/eqlog*.txt')):
            if not os.path.isdir(f):
                self.profiles[os.path.basename(f)] = os.path.realpath(f)

    def save(self) -> None:
        try:
            if self.profile.name:
                open(
                    os.path.join(
                        './data/profiles',
                        f'{self.profile.log_file}.json'
                    ),
                    'w'
                ).write(self.profile.json())
        except:
            log.warning(
                'Unable to save profile.',
                exc_info=True
            )
