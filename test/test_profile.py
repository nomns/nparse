import unittest
from config import profile


class TestProfile(unittest.TestCase):

    def test_profile(self):
        self.assertIsInstance(profile.Profile(), profile.Profile)

    def test_json(self):
        self.assertIsInstance(profile.Profile().json(), str)

    def test_update(self):
        p = profile.Profile()
        p.update({
            'triggers': {
                'toggled': False
            }
        })
        self.assertIsInstance(p, profile.Profile)
        self.assertEqual(False, p.triggers.toggled)


if __name__ == '__main__':
    unittest.main()
