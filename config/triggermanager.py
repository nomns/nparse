import os
import glob

from .trigger import Trigger

TRIGGERS_LOCATION = './data/triggers'


class TriggerManager:

    def __init__(self):
        self.triggers = {}
        if not os.path.exists(TRIGGERS_LOCATION):
            os.mkdir(TRIGGERS_LOCATION)
        self.load()

    def load(self):
        # trigger trees are kept in their own file so they can be distributed
        for trigger_file in glob.glob(TRIGGERS_LOCATION, '*.json'):


