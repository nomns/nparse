import os
import glob
import json
from typing import Dict

from .config import Config
from .profile import Profile
from utils import logger

app_config = Config()
log = logger.get_logger(__name__)

PROFILES_LOCATION = './data/profiles'


class ProfileManager:

    def __init__(self) -> None:
        self.profile: Profile = Profile()
        self.profiles: Dict[str, any] = {}
        if not os.path.exists(PROFILES_LOCATION):
            os.mkdir(PROFILES_LOCATION)
        self.scan()

    def scan(self) -> None:
        self.profiles = {}
        for f in glob.glob(os.path.join(app_config.eq_dir, '/Logs/eqlog*.txt')):
            if not os.path.isdir(f):
                self.profiles[os.path.basename(f)] = os.path.realpath(f)

    def switch(self, log_file: str) -> None:
        self.save()
        self.load(log_file)

    def load(self, log_file: str) -> None:
        try:
            profile_dict = json.loads(
                open(os.path.join('./data/profiles', f'{log_file}.json'))
                .read()
            )
            profile = Profile()
            profile.update(profile_dict)
            self.profile = profile
        except:
            log.error(f'Unable to load profile: {log_file}', exc_info=True)

    def save(self) -> None:
        try:
            if self.profile.name:
                open(os.path.join('./data/profiles', f'{self.profile.log_file}.json'), 'w')\
                    .write(self.profile.json())
        except:
            log.warning(f'Unable to save profile: {self.profile.name}', exc_info=True)
