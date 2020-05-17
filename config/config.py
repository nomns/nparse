import os
from dataclasses import dataclass
import json
import glob

from helpers import logger
log = logger.get_logger(__name__)


@dataclass
class Config:

    eq_dir: str = ''
    update_check: bool = True
    last_profile: str = ''
    qt_scale_factor: int = 100

    def __post_init__(self):
        try:
            self.__dict__.update(
                **json.loads(open('./data/nparse.config.json', 'r+').read()).items()
                )
        except:
            log.warning('Unable to load ./data/nparse.config.json', exc_info=True)

    def save(self):
        try:
            open('./data/nparse.config.json', 'w').write(json.dumps(self.__dict__))
        except:
            log.warning('Unable to save ./data/nparse.config.json', exc_info=True)

    def verify_paths(self):
        # verify eq log directory exists
        try:
            assert(os.path.isdir(os.path.join(self.eq_dir)))
        except:
            raise ValueError(
                'Everquest Log Directory Error',
                'Everquest log directory needs to be set before proceeding. \
                    Use Settings->General->Everquest Directory to set it.'
            )

        # verify eq log directory contains log files for reading.
        log_filter = os.path.join(self.eq_dir, 'Logs', 'eqlog*.*')
        if not glob(log_filter):
            raise ValueError(
                'No Logs Found',
                'No Everquest log files were found.  Ensure both your directory is set \
                    and logging is turned on in your Everquest client.'
            )
