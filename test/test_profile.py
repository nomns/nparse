import unittest
from config import profile


class TestProfile(unittest.TestCase):

    def test_profile(self):
        self.assertIsInstance(profile.Profile(), profile.Profile)

    def test_json(self):
        self.assertIsInstance(profile.Profile().json(), str)

    def test_update(self):
        test_profile = profile.Profile()
        test_profile.update(
            {
                'triggers': {
                    'toggled': False
                }
            }
        )
        self.assertIsInstance(test_profile, profile.Profile)
        self.assertEqual(False, test_profile.triggers.toggled)


if __name__ == '__main__':
    unittest.main()
