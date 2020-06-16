import math
from bisect import bisect_right, bisect_left

from metrics.classification_metric import RoCCurve


class FixedWindow(RoCCurve):
    def __init__(self):
        self.parts = 10
        super().__init__(self.parts)

    def match_classification_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        tolerance = tolerance // 2  # necessary because it is to left and to the right
        tp, fp, tn, fn = 0, 0, 0, 0
        last_right_border = -1
        for true_beat in true_samples:
            right_border = bisect_right(test_samples, true_beat + tolerance) - 1
            left_border = bisect_left(test_samples, true_beat - tolerance)

            right_border = max(right_border, 0)
            left_border = min(left_border, len(test_samples) - 1)
            left_dist_to_beat = abs(test_samples[left_border] - true_beat)
            right_dist_to_beat = abs(test_samples[right_border] - true_beat)
            if left_dist_to_beat <= tolerance or right_dist_to_beat <= tolerance:
                tp += 1
            elif left_dist_to_beat > tolerance and right_dist_to_beat > tolerance:
                fn += 1

            if left_border > last_right_border + 1 or left_dist_to_beat > tolerance and last_right_border == -1:
                # not exactly the next predicted beat after last interval
                fp += 1
            elif left_border == last_right_border + 1:
                tn += 1

            last_right_border = right_border
        if test_samples[-1] > true_samples[-1] + tolerance:
            fp += 1
        else:
            tn += 1
        return tp, fp, tn, fn


class WindowedF1Score(FixedWindow):
    __abbrev__ = "Windowed F1"

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.f1score(tp, fp, fn))
        return max(metrics_per_tol)

    def f1score(self, tp, fp, fn):
        if tp == 0 == fp == fn:
            return 0
        return 2 * tp / (2 * tp + fn + fp)


class WindowedPPV(FixedWindow):
    __abbrev__ = "Windowed PPV"

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.ppv(tp, fp))
        return max(metrics_per_tol)

    def ppv(self, tp, fp):
        if tp == 0 == fp:
            return 0
        return tp / (fp + tp)


class WindowedSpecificity(FixedWindow):
    __abbrev__ = "Windowed Speci"

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.specificity(fp, tn))
        return max(metrics_per_tol)

    def specificity(self, fp, tn):
        if fp == tn == 0:
            return 0
        return tn / (fp + tn)


class WindowedPPVSpec(FixedWindow):
    __abbrev__ = "Windowed PPV/Spec"

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.ppv_spec(tp, fp, tn, fn))
        return min(metrics_per_tol, key=self.distance_to_upper_right_corner)

    def distance_to_upper_right_corner(self, x):
        fi, se = x
        return math.sqrt((1 - fi) ** 2 + (1 - se) ** 2)

    def ppv_spec(self, tp, fp, tn, fn):
        return tp / max(tp + fn, 0.00001), tn / max(fp + tn, 0.00001)


class WinTP(FixedWindow):
    __abbrev__ = "Fixed Thesh. TP"

    def compute(self):
        return self.tp_by_tol


class WinFP(FixedWindow):
    __abbrev__ = "Fixed Thesh. FP"

    def compute(self):
        return self.fp_by_tol


class WinTN(FixedWindow):
    __abbrev__ = "Fixed Thesh. TN"

    def compute(self):
        return self.tn_by_tol


class WinFN(FixedWindow):
    __abbrev__ = "Fixed Thesh. FN"

    def compute(self):
        return self.fn_by_tol
