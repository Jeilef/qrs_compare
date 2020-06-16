import unittest
from concurrent.futures import ProcessPoolExecutor

from metrics.classification_metric import RoCCurve


class TestRocCurve(unittest.TestCase):
    def test_roc_curve_speed(self):
        roc = RoCCurve(10)
        true_samples = list(range(1, 600000, 300))
        true_symbols = ['N'] * len(true_samples)
        test_samples = list(range(1, 600000, 290))
        with ProcessPoolExecutor(max_workers=2) as pool:
            pool.map(roc.match_annotations,
                     list([true_samples] * 10),
                     list([true_symbols] * 10),
                     list([test_samples] * 10))

    def test_faster_Roc_computation_perfect_prediction_no_tol(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10], 0)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)

    def test_faster_Roc_computation_perfect_prediction(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10], 1)
        self.assertEqual(2, tp)
        self.assertEqual(0, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)

    def test_faster_Roc_computation_perfect_prediction_bigger_tolerance(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10], 10)
        self.assertEqual(11, tp)
        self.assertEqual(0, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)

    def test_faster_Roc_computation_close_prediction(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [9], 5)
        self.assertEqual(5, tp)
        self.assertEqual(1, fp)
        self.assertEqual(4, tn)
        self.assertEqual(1, fn)

    def test_faster_Roc_computation_close_prediction_after(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [11], 10)
        self.assertEqual(10, tp)
        self.assertEqual(1, fp)
        self.assertEqual(0, tn)
        self.assertEqual(1, fn)

    def test_faster_Roc_computation_perfect_prediction_next_not_perfect(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10, 15], 10)
        self.assertEqual(11, tp)
        self.assertEqual(5, fp)
        self.assertEqual(0, tn)
        self.assertEqual(0, fn)

    def test_faster_Roc_computation_not_found_beat(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [15], 4)
        self.assertEqual(0, tp)
        self.assertEqual(5, fp)
        self.assertEqual(6, tn)
        self.assertEqual(5, fn)

    def test_faster_Roc_computation_not_found_beat_multiple_predictions(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [15, 5], 4)
        self.assertEqual(0, tp)
        self.assertEqual(10, fp)
        self.assertEqual(0, tn)
        self.assertEqual(5, fn)

    def test_faster_Roc_computation_not_found_beat_no_prediction(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [0], 4)
        self.assertEqual(0, tp)
        self.assertEqual(1, fp)
        self.assertEqual(11, tn)
        self.assertEqual(5, fn)

    def test_faster_Roc_computation_not_found_beat_single_prediction(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([162], ['N'], [176], 19)
        self.assertEqual(5, tp)
        self.assertEqual(14, fp)
        self.assertEqual(144, tn)
        self.assertEqual(14, fn)

    def test_faster_Roc_computation_tn(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10], 1)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(10, tn)
        self.assertEqual(0, fn)

    def test_faster_Roc_computation_tn_with_window(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [10], 2)
        self.assertEqual(2, tp)
        self.assertEqual(0, fp)
        self.assertEqual(9, tn)
        self.assertEqual(0, fn)

    def test_right_number_tp_if_two_window_size_apart(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [9, 13], 3)
        self.assertEqual(4, tp)
        self.assertEqual(4, fp)
        self.assertEqual(6, tn)
        self.assertEqual(0, fn)

    def test_right_number_tp_if_overlapping_predictions(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [9, 11], 3)
        self.assertEqual(4, tp)
        self.assertEqual(2, fp)
        self.assertEqual(6, tn)
        self.assertEqual(0, fn)

    def test_right_number_tp_if_overlapping_predictions_further_apart(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([10], ['N'], [9, 12], 3)
        self.assertEqual(4, tp)
        self.assertEqual(3, fp)
        self.assertEqual(6, tn)
        self.assertEqual(0, fn)

    def test_large_threshold(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([68], ['N'], [110], 50)
        self.assertEqual(9, tp)
        self.assertEqual(18, fp)
        self.assertEqual(18, tn)
        self.assertEqual(42, fn)

    def test_large_threshold2(self):
        roc = RoCCurve(10)
        tp, fp, tn, fn = roc.match_classification_annotations([46], ['N'], [0], 50)
        self.assertEqual(1, tp)
        self.assertEqual(0, fp)
        self.assertEqual(18, tn)
        self.assertEqual(42, fn)
