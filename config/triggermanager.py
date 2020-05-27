import os
import glob
from typing import List

from utils import logger

log = logger.get_logger(__name__)

from .triggerpackage import TriggerPackage

TRIGGERS_LOCATION = "./data/triggers"


class TriggerManager:
    def __init__(self):
        self.packages: List[TriggerPackage] = []
        if not os.path.exists(TRIGGERS_LOCATION):
            os.mkdir(TRIGGERS_LOCATION)
        self.load()
        self.index = 0

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        try:
            package = self.packages[self.index]
        except IndexError:
            raise StopIteration
        self.index += 1
        return package

    def append(self, package: TriggerPackage):
        if isinstance(package, TriggerPackage):
            self.packages.append(package)

    def load(self) -> None:
        # trigger trees are kept in their own file so they can be distributed
        for trigger_package in glob.glob(os.path.join(TRIGGERS_LOCATION, "*")):
            try:
                if os.path.isdir(trigger_package):
                    trigger_package_name = os.path.basename(
                        os.path.normpath(trigger_package)
                    )
                    self.packages.append(TriggerPackage(name=trigger_package_name))
            except:
                log.warning(f"Unable to load {trigger_package}.", exc_info=True)

    def save(self) -> None:
        for package in self:
            package.save()
