import unittest

from metrics.fixed_window_classification_metric import FixedWindow


class TestFixedWindowMetric(unittest.TestCase):
    def test_perfect_prediction_no_tol(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [10], 1)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(2, tn)
        self.assertEqual(0, fn)

    def test_almost_perfect_prediction_no_tol(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [9], 2)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(2, tn)
        self.assertEqual(0, fn)

    def test_almost_perfect_prediction_no_tol_larger(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [11], 2)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(2, tn)
        self.assertEqual(0, fn)

    def test_no_prediction(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [0], 2)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(1, tn)
        self.assertEqual(1, fn)

    def test_higher_right_and_wrong_prediction(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [0, 11], 2)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(1, tn)
        self.assertEqual(0, fn)

    def test_lower_right_and_wrong_prediction(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [0, 9], 2)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(1, tn)
        self.assertEqual(0, fn)

    def test_two_right_and_wrong_prediction(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [0, 9, 11], 2)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(1, tn)
        self.assertEqual(0, fn)

    def test_lower_right_and_two_lower_wrong_prediction(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10], ["n"], [0, 5, 9, 11], 2)
        self.assertEqual(1, tp)
        self.assertEqual(1, fp)
        self.assertEqual(1, tn)
        self.assertEqual(0, fn)

    def test_multiple_beats_two_right_predictions(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10, 20], ["n"], [10, 20], 2)
        self.assertEqual(2, tp)
        self.assertEqual(0, fp)
        self.assertEqual(3, tn)
        self.assertEqual(0, fn)

    def test_multiple_beats_two_right_predictions_three_missed(self):
        hw = FixedWindow()
        tp, fp, tn, fn = hw.match_classification_annotations([10, 20], ["n"], [5, 10, 15, 20, 25], 2)
        self.assertEqual(2, tp)
        self.assertEqual(3, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)
