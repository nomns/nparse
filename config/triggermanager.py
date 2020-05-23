import os
import glob
from typing import List

from .trigger import TriggerContainer

TRIGGERS_LOCATION = "./data/triggers"


class TriggerManager:
    def __init__(self):
        self.triggers: List[TriggerContainer] = []
        if not os.path.exists(TRIGGERS_LOCATION):
            os.mkdir(TRIGGERS_LOCATION)
        self.load()

    def load(self):
        # trigger trees are kept in their own file so they can be distributed
        for trigger_archive in glob.glob(os.path.join(TRIGGERS_LOCATION, "*.json")):
            pass

    def save(self):
        pass
