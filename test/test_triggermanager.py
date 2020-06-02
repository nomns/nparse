import unittest

from config.triggers.triggermanager import TriggerManager
from config.triggers.triggerpackage import TriggerPackage
from config.profiles.profiles import Profile

from test.common import get_profiles


class TestTriggerManager(unittest.TestCase):
    def test_init(self):  # .load is also run
        tm = TriggerManager()
        self.assertIsInstance(tm, TriggerManager)

    def test_iter(self):
        tm = TriggerManager()
        for package in tm:
            self.assertIsInstance(package, TriggerPackage)

    def test_create_parsers(self):
        tm = TriggerManager()
        test_profile = Profile()
        profiles = get_profiles()
        if profiles:
            test_profile.load(profiles[0])
        tm.create_parsers(test_profile.trigger_choices)


if __name__ == "__main__":
    unittest.main()
