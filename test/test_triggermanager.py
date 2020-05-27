import unittest

from config.triggermanager import TriggerManager
from config.triggerpackage import TriggerPackage


class TestTriggerManager(unittest.TestCase):
    def test_init(self):  # .load is also run
        tm = TriggerManager()
        self.assertIsInstance(tm, TriggerManager)

    def test_iter(self):
        tm = TriggerManager()
        for package in tm:
            self.assertIsInstance(package, TriggerPackage)


if __name__ == "__main__":
    unittest.main()
