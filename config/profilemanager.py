import os
import glob

from .config import Config
from .profile import Profile
app_config = Config()


class ProfileManager:

    def __init__(self) -> None:
        self.profiles = {}
        if not os.path.exists('./data/profiles'):
            os.mkdir('./data/profiles')
        self.scan()

    def get_profile(self, profile_name: str) -> Profile:
        if not profile_name:
            return Profile()


    def scan(self) -> None:
        self.profiles = {}
        for f in glob.glob(
                os.path.join(
                    app_config.eq_dir,
                    '/Logs/eqlog*.*'),
                recursive=True):
            if not os.path.isdir(f):
                self.profiles[os.path.basename(f)] = os.path.realpath(f)
