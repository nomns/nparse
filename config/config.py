import os
from dataclasses import dataclass, field
import json
import glob
from typing import List

from utils import logger

log = logger.get_logger(__name__)


@dataclass
class Config:

    eq_dir: str = ""
    update_check: bool = True
    last_profile: str = ""
    qt_scale_factor: int = 100
    use_secondary: List[str] = field(
        default_factory=lambda: ["levitate", "malise", "malisement"]
    )

    def __post_init__(self):
        try:
            self.__dict__.update(
                json.loads(open("data/nparse.config.json", "r").read()).items()
            )
        except:
            log.warning("Unable to load data/nparse.config.json", exc_info=True)

    def save(self):
        try:
            open("data/nparse.config.json", "w").write(
                json.dumps(self.__dict__, indent=4)
            )
        except:
            log.warning("Unable to save data/nparse.config.json", exc_info=True)

    def verify_paths(self):
        # verify Everquest Directory Exists
        try:
            assert os.path.isdir(os.path.join(self.eq_dir))
        except:
            raise ValueError(
                "Everquest Directory Error",
                (
                    "Everquest directory needs to be set before proceeding. "
                    "Use Settings->General->Everquest Directory to set it."
                ),
            )

        # verify eq log directory contains log files for reading.
        log_filter = os.path.join(self.eq_dir, "Logs", "eqlog*.*")
        if not glob.glob(log_filter):
            raise ValueError(
                "No Logs Found",
                (
                    "No Everquest log files were found.  Ensure both your directory is set "
                    "and logging is turned on in your Everquest client."
                ),
            )
