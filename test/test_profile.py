import unittest
import os
from glob import glob
from dataclasses import asdict
from typing import List

from config.profiles import Profile


def get_profiles() -> List[str]:
    #  remove '.json' from end of file
    return [os.path.basename(f[:-5]) for f in glob("data/profiles/*.json")]


class TestProfile(unittest.TestCase):
    def test_profile(self):
        self.assertIsInstance(Profile(), Profile)

    def test_json(self):
        self.assertIsInstance(Profile().json(), str)

    def test_update(self):
        test_profile: Profile = Profile()
        test_profile.update({"triggers": {"toggled": False}})
        self.assertEqual(False, test_profile.triggers.toggled)
        test_profile.update(asdict(Profile()))
        self.assertEqual(test_profile, Profile())
        profiles = get_profiles()
        test_profile = Profile()
        if profiles:
            test_profile.load(profiles[0])
        test_profile.update(asdict(Profile()))
        self.assertEqual(test_profile, Profile())
        test_profile.log_file = "not_a_log_file"
        self.assertNotEqual(test_profile, Profile())

    def test_switch(self):
        test_profile = Profile()
        profiles = get_profiles()
        if len(profiles) > 1:
            test_profile.load(profiles[0])
            test_profile.switch(profiles[1])
        self.assertIsInstance(test_profile, Profile)
        self.assertNotEqual(test_profile, Profile())


if __name__ == "__main__":
    unittest.main()
