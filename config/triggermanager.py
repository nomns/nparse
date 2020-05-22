import os
import glob
from pathlib import Path
from typing import Dict

from .trigger import Trigger, TriggerContainer

TRIGGERS_LOCATION = './data/triggers'

def dict_to_triggers(dictionary: Dict[str, any]):


class TriggerManager:

    def __init__(self):
        self.triggers = {}
        if not os.path.exists(TRIGGERS_LOCATION):
            os.mkdir(TRIGGERS_LOCATION)
        self.load()

    def load(self):
        # trigger trees are kept in their own file so they can be distributed
        for trigger_archive in glob.glob(TRIGGERS_LOCATION, '*.json'):
            name = Path(trigger_archive).stem
            container = TriggerContainer(

            )

