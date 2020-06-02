import unittest
import os
from dataclasses import asdict

from test.common import get_profiles
from config.profiles.profiles import Profile


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

    def test_save(self, delete: bool = True):
        test_profile = Profile(log_file="__testing__")
        test_profile.name = "Leela"
        profile_path = os.path.join("data/profiles", f"{test_profile.log_file}.json")
        test_profile.save()
        self.assertTrue(os.path.exists(profile_path))
        if delete:
            os.remove(profile_path)

    def test_load(self):
        self.test_save(delete=False)
        test_profile = Profile()
        test_profile.load("__testing__")
        profile_path = os.path.join("data/profiles", f"{test_profile.log_file}.json")
        self.assertIsInstance(test_profile, Profile)
        self.assertEqual(test_profile.name, "Leela")
        os.remove(os.path.abspath(profile_path))

    def test_enabled(self):
        test_profile = Profile()
        profiles = get_profiles()
        if profiles:
            test_profile.load(profiles[0])
            self.assertIsNotNone(test_profile.trigger_choices)


if __name__ == "__main__":
    unittest.main()
