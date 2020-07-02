import unittest

from metrics.hopping_window_metric import HoppingWindow


class TestHoppingWindow(unittest.TestCase):

    def test_perfect_prediction_no_tol(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([10], [10], 0, 1)
        self.assertEqual(2, tp)
        self.assertEqual(0, fp)
        self.assertEqual(19, tn)
        self.assertEqual(0, fn)

    def test_perfect_prediction_no_tol_step_two(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([10], [10], 1, 2)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(10, tn)
        self.assertEqual(0, fn)

    def test_non_recognized_filler_beat(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([50], [0], 57, 11)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(5, tn)
        self.assertEqual(4, fn)

    def test_non_recognized_filler_beat_low_step_size(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([493], [0], 7, 5)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(196, tn)
        self.assertEqual(1, fn)

    def test_most_close_prediction(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([12], [5], 7, 5)
        self.assertEqual(1, tp)
        self.assertEqual(2, fp)
        self.assertEqual(1, tn)
        self.assertEqual(1, fn)

    def test_most_close_prediction_after(self):
        hw = HoppingWindow()
        tp, fp, tn, fn = hw.match_hopping_annotations([12], [17], 7, 5)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(2, tn)
        self.assertEqual(1, fn)

    def test_num_modulo_empty(self):
        hw = HoppingWindow()
        num = hw.num_modulo(1, 3, 5)
        self.assertEqual(0, num)

    def test_num_modulo_single(self):
        hw = HoppingWindow()
        num = hw.num_modulo(1, 4, 5)
        self.assertEqual(1, num)
