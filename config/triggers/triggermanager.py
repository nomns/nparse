import os
import glob
from shutil import rmtree
from typing import List

from utils import logger

log = logger.get_logger(__name__)

from .triggerpackage import TriggerPackage
from .trigger import TriggerChoice
from .triggerparser import TriggerParser


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

    def delete(self, package: TriggerPackage):
        log.info(f"Deleting package: {package.name}")
        try:
            self.packages.remove(package)
            rmtree(os.path.abspath(package.location))
        except:
            log.warning("Unable to delete package: {package.name}", exc_info=True)

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

    def create_parsers(
        self,
        choices: List[TriggerChoice] = None,
        triggers: List[any] = None,
        flattened: List[any] = None,
        slot=None,
    ) -> List[TriggerParser]:
        if not isinstance(flattened, List):
            flattened = []
        if not triggers:
            triggers = self.packages
        for choice in choices:
            if choice.enabled:
                for item in triggers:
                    if (
                        item.name == choice.name
                        and choice.type_ == "group"
                        and choice.group
                        and item.type_ in ["container", "package"]
                    ):
                        self.create_parsers(choice.group, item.items, flattened, slot)
                    elif (item.name, item.type_) == (choice.name, choice.type_):
                        parser = TriggerParser(item)
                        if slot:
                            parser.triggered.connect(slot)
                        flattened.append(parser)

        return flattened
