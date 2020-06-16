import math
from bisect import bisect_left, bisect_right
import numpy as np

from metrics.metric import Metric
import concurrent.futures as cf


class ClassificationMetric(Metric):
    def __init__(self, tolerance=0.1):
        self.fn = []
        self.fp = []
        self.tp = []

        self.tolerance = tolerance

    def join(self, other):
        self.fn.extend(other.fn)
        self.fp.extend(other.fp)
        self.tp.extend(other.tp)
        return self

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        """Tries to match two lists of (supposed) QRS positions.

        Args:
            true_samples: List of samples representing the actual QRS positions.
            true_symbols: Annotation symbols for the samples in true_samples.
            test_samples: List of samples representing the detected QRS positions.
            tolerance: Maximum allowed distance between actual and detected QRS
                position.

        Returns:
            Tuple (tp, fp, fn) whereas tp is a list of true positives characterized
            as tripel (true_sample, test_sample, symbol), fp is a list of false
            positives characterized as tuple (test_sample, symbol?), and fn is a
            list of false negatives characterized as list of tuples (true_sample,
            symbol).
            :param sampling_frequency:
        """
        self.match_classification_annotations(true_samples, true_symbols, test_samples,
                                              self.tolerance * sampling_frequency)

    def match_classification_annotations(self, true_samples, true_symbols, test_samples, tolerance):

        tp, fp, fn = [], [], []

        for true_sample, true_symbol in zip(true_samples, true_symbols):
            matches = [test_sample
                       for test_sample in test_samples
                       if abs(test_sample - true_sample) <= tolerance]
            matches.sort(key=lambda m: abs(m - true_sample))
            if len(matches) == 0:
                fn.append((true_sample, true_symbol))
            if len(matches) > 0:
                tp.append((true_sample, matches[0], true_symbol))
            if len(matches) > 1:
                fp.extend([(match, true_symbol) for match in matches[1:]])

        for test_sample in test_samples:
            matches = [true_sample
                       for true_sample in true_samples
                       if abs(true_sample - test_sample) <= tolerance]
            if len(matches) == 0:
                fp.append((test_sample, ''))

        self.fn.extend(fn)
        self.fp.extend(fp)
        self.tp.extend(tp)
        return tp, fp, fn

    def compute(self):
        raise NotImplementedError


class PositivePredictiveValue(ClassificationMetric):
    __abbrev__ = "PPV"

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        if len(self.tp) == 0 == len(self.fp):
            return 0
        return len(self.tp) / (len(self.fp) + len(self.tp))


class Sensitivity(ClassificationMetric):
    __abbrev__ = "Sens"

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        if len(self.tp) == 0 == len(self.fn):
            return 0
        return len(self.tp) / (len(self.fn) + len(self.tp))


class F1(ClassificationMetric):
    __abbrev__ = "F1 Score"

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        if len(self.tp) == 0 == len(self.fp) == len(self.fn):
            return 0
        return 2 * len(self.tp) / (2 * len(self.tp) + len(self.fn) + len(self.fp))


class RoCCurve(ClassificationMetric):
    __abbrev__ = "RoC"
    __parts__ = 10

    def __init__(self, parts=__parts__):
        super().__init__()
        self.parts = parts
        self.tp_by_tol = [0 for _ in range(parts)]
        self.fp_by_tol = [0 for _ in range(parts)]
        self.tn_by_tol = [0 for _ in range(parts)]
        self.fn_by_tol = [0 for _ in range(parts)]

    def join(self, other):
        for p in range(self.parts):
            self.tp_by_tol[p] += other.tp_by_tol[p]
            self.fp_by_tol[p] += other.fp_by_tol[p]
            self.tn_by_tol[p] += other.tn_by_tol[p]
            self.fn_by_tol[p] += other.fn_by_tol[p]
        return self

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        sf = sampling_frequency // 5
        window_sizes = list(range(1, sf - (sf % self.parts), sf // self.parts))
        confusion_values = map(self.match_classification_annotations,
                               list([true_samples] * len(window_sizes)),
                               list([true_symbols] * len(window_sizes)),
                               list([test_samples] * len(window_sizes)),
                               window_sizes)

        for idx, cv in enumerate(confusion_values):
            self.tp_by_tol[idx] += cv[0]
            self.fp_by_tol[idx] += cv[1]
            self.tn_by_tol[idx] += cv[2]
            self.fn_by_tol[idx] += cv[3]

        return self.compute()

    def match_classification_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        tp, fp, fn, tn = 0, 0, 0, 0
        recording_len = 2 * true_samples[-1] - true_samples[-2] if len(true_samples) > 1 else 2 * true_samples[-1]
        for true_beat in true_samples:
            left_pred_idx = bisect_right(test_samples, true_beat) - 1
            right_pred_idx = bisect_left(test_samples, true_beat)

            left_pred_idx = max(left_pred_idx, 0)
            right_pred_idx = min(right_pred_idx, len(test_samples) - 1)

            left_dist_to_beat = abs(test_samples[left_pred_idx] - true_beat)
            right_dist_to_beat = abs(test_samples[right_pred_idx] - true_beat)
            closest_pred_idx = left_pred_idx if left_dist_to_beat < right_dist_to_beat else right_pred_idx
            # was the beat found
            if min(left_dist_to_beat, right_dist_to_beat) <= tolerance:
                if left_pred_idx != right_pred_idx and left_dist_to_beat <= tolerance and right_dist_to_beat <= tolerance:
                    left_overlap = abs(test_samples[left_pred_idx] - (true_beat - tolerance - 1))
                    right_overlap = abs(test_samples[right_pred_idx] - (true_beat + tolerance + 1))
                    overlap = max(0, test_samples[left_pred_idx] + tolerance - (test_samples[right_pred_idx] - tolerance) - 2)
                    num_tp = left_overlap + right_overlap - overlap
                    tp += int(num_tp)
                else:
                    num_tp = min(abs(test_samples[closest_pred_idx] - (true_beat - tolerance - 1)),
                                 abs(test_samples[closest_pred_idx] - (true_beat + tolerance + 1)),
                                 test_samples[closest_pred_idx] + 1)
                    tp += int(num_tp)
            # are there some windows where no prediction lies
            if left_pred_idx != right_pred_idx and left_dist_to_beat + right_dist_to_beat > tolerance:
                num_fn = min(min(right_dist_to_beat, left_dist_to_beat) - 1, tolerance + 1)
                fn += int(num_fn)
            if left_pred_idx == right_pred_idx:
                fn += min(left_dist_to_beat, tolerance + 1)

        for pred_beat in test_samples:
            next_beat_idx = bisect_right(true_samples, pred_beat)
            previous_beat_idx = next_beat_idx - 1
            previous_beat = true_samples[previous_beat_idx] if previous_beat_idx >= 0 else -1
            if previous_beat == pred_beat:
                continue
            next_beat = true_samples[next_beat_idx] if next_beat_idx != len(true_samples) else previous_beat
            if next_beat - pred_beat <= tolerance and pred_beat - previous_beat <= tolerance and next_beat != previous_beat:
                continue
            num_fp = min(abs(previous_beat - pred_beat),
                         abs(next_beat - pred_beat),
                         tolerance + 1,
                         recording_len - next_beat)
            fp += int(num_fp)

        num_tn = recording_len - tp - fp - fn + 1
        if num_tn < 0:
            print("error:", num_tn, true_samples, test_samples, tolerance)
        tn += max(int(num_tn), 0)
        return tp, fp, tn, fn

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.ppv_fpr(tp, fp, tn, fn))
        return min(metrics_per_tol, key=self.distance_to_upper_left_corner)

    def distance_to_upper_left_corner(self, x):
        fi, se = x
        return math.sqrt((1 - fi) ** 2 + se ** 2)

    def ppv_fpr(self, tp, fp, tn, fn):
        return tp / max(tp + fn, 0.00001), fp / max(fp + tn, 0.00001)


class PPVSpec(RoCCurve):
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


class TP(RoCCurve):
    __abbrev__ = "TP"

    def compute(self):
        return self.tp_by_tol


class FP(RoCCurve):
    __abbrev__ = "FP"

    def compute(self):
        return self.fp_by_tol


class TN(RoCCurve):
    __abbrev__ = "TN"

    def compute(self):
        return self.tn_by_tol


class FN(RoCCurve):
    __abbrev__ = "FN"

    def compute(self):
        return self.fn_by_tol
