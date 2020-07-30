import unittest

from metrics.adapted_fixed_window_metric import AdaptedFixedWindow


class TestFixedWindowMetric(unittest.TestCase):
    def test_perfect_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [10], 1)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(1, tn)
        self.assertEqual(0, fn)

    def test_no_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [], 1)
        self.assertEqual(0, tp)
        self.assertEqual(0, fp)
        self.assertEqual(1, tn)
        self.assertEqual(1, fn)

    def test_two_before_and_after_false_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [5, 15], 1)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(0, tn)
        self.assertEqual(1, fn)

    def test_one_before_false_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [5], 1)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(0, tn)
        self.assertEqual(1, fn)

    def test_one_after_false_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [15], 1)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(0, tn)
        self.assertEqual(1, fn)

    def test_two_after_true_false_prediction_no_tol(self):
        hw = AdaptedFixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [11, 15], 2)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)
