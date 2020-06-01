import unittest

from utils import parse_name_from_log, is_new_version_available


class TestUtil(unittest.TestCase):
    def test_parse_name_from_log(self):
        self.assertIsInstance(parse_name_from_log("eqlog_Nomns_project1999.txt"), str)

    def test_is_new_version_available(self):
        self.assertTrue(
            all(
                (
                    is_new_version_available("0.6.1", "0.6.0"),
                    is_new_version_available("1.6.0", "0.6.0"),
                    is_new_version_available("0.7.0", "0.6.1"),
                )
            )
        )
        self.assertFalse(
            any(
                (
                    is_new_version_available("0.5.0", "0.5.0"),
                    is_new_version_available("0.9.9", "1.0.0"),
                    is_new_version_available("0.6.9", "0.7.0"),
                )
            )
        )
