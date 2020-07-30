from bisect import bisect_right, bisect_left

from metrics.classification_metric import RoCCurve


class AdaptedFixedWindow(RoCCurve):
    def __init__(self):
        self.parts = 10
        super().__init__(self.parts)

    def match_classification_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        if len(test_samples) == 0:
            return 0, 0, len(true_samples), len(true_samples)
        tolerance = tolerance // 2  # necessary because it is to left and to the right of the beat
        tp, fp, tn, fn = 0, 0, 0, 0
        for true_idx, true_beat in enumerate(true_samples):
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

            # TN
            if true_idx > 0:
                last_border = (true_beat + true_samples[true_beat - 1]) / 2
            else:
                last_border = 0
            if true_idx < len(true_samples) - 1:
                next_border = (true_beat + true_samples[true_beat + 1]) / 2
            else:
                next_border = max(true_samples[-1], test_samples[-1])

            pre_tolerance_idx = bisect_left(test_samples, true_beat - tolerance) - 1
            post_tolerance_idx = bisect_right(test_samples, true_beat + tolerance)

            pre_clear = pre_tolerance_idx < 0 or test_samples[pre_tolerance_idx] < last_border
            post_clear = post_tolerance_idx >= len(test_samples) or test_samples[post_tolerance_idx] > next_border
            if pre_clear and post_clear:
                tn += 1
            else:
                fp += 1

        return tp, fp, tn, fn


class AdTP(AdaptedFixedWindow):
    __abbrev__ = "TP"

    def compute(self):
        return self.tp_by_tol[-1]


class AdFP(AdaptedFixedWindow):
    __abbrev__ = "FP"

    def compute(self):
        return self.fp_by_tol[-1]


class AdTN(AdaptedFixedWindow):
    __abbrev__ = "TN"

    def compute(self):
        return self.tn_by_tol[-1]


class AdFN(AdaptedFixedWindow):
    __abbrev__ = "FN"

    def compute(self):
        return self.fn_by_tol[-1]