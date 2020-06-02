import unittest
from dataclasses import asdict
from config.triggers import trigger


class TestTrigger(unittest.TestCase):
    def test_trigger(self):
        self.assertIsInstance(trigger.Trigger(), trigger.Trigger)

    def test_update(self):
        test_trigger = trigger.Trigger()
        test_trigger.update(asdict(trigger.Trigger()))
        self.assertEqual(test_trigger, trigger.Trigger())
        test_trigger.update(
            {"name": "Nomns", "start_action": {"sound": {"enabled": True}}}
        )
        self.assertEqual(test_trigger.start_action.sound.enabled, True)


if __name__ == "__main__":
    unittest.main()
