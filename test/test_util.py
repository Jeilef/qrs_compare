import unittest

from util.util import get_closest


class TestUtil(unittest.TestCase):
    def setUp(self) -> None:
        self.a = [1, 4, 5, 8, 8, 10, 20]

    def test_get_closest_base(self):
        x = 14
        x1 = get_closest(self.a, x)
        self.assertEqual(10, x1)
