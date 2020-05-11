from metrics.metric import Metric
from bisect import bisect_right

class ClassificationMetric(Metric):
    def __init__(self, tolerance=36):
        self.fn = []
        self.fp = []
        self.tp = []

        self.tolerance = tolerance

    def match_annotations(self, true_samples, true_symbols, test_samples):
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
        """
        self.match_classification_annotations(true_samples, true_symbols, test_samples, self.tolerance)

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

    def match_annotations(self, true_samples, true_symbols, test_samples):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        return len(self.tp) / max((len(self.fp) + len(self.tp)), 0.00001)


class Sensitivity(ClassificationMetric):
    __abbrev__ = "Sens"

    def match_annotations(self, true_samples, true_symbols, test_samples):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        return len(self.tp) / max((len(self.fn) + len(self.tp)), 0.00001)


class F1(ClassificationMetric):
    __abbrev__ = "F1 Score"

    def match_annotations(self, true_samples, true_symbols, test_samples):
        super().match_annotations(true_samples, true_symbols, test_samples)
        return self.compute()

    def compute(self):
        return 2 * len(self.tp)/max((2 * len(self.tp) + len(self.fn) + len(self.fp)), 0.00001)


class RoCCurve(ClassificationMetric):
    __abbrev__ = "RoC"

    def __init__(self, sample_rate=360):
        super().__init__()
        self.sample_rate = sample_rate
        self.spacing = sample_rate // 5
        self.tp_by_tol = [[] for _ in range(1, self.sample_rate, self.spacing)]
        self.fp_by_tol = [[] for _ in range(1, self.sample_rate, self.spacing)]
        self.tn_by_tol = [[] for _ in range(1, self.sample_rate, self.spacing)]
        self.fn_by_tol = [[] for _ in range(1, self.sample_rate, self.spacing)]
        self.tn = []

    def match_annotations(self, true_samples, true_symbols, test_samples):
        # TODO: add multiprocessing
        for tol in range(1, self.sample_rate, self.spacing):
            tp, fp, tn, fn = self.match_classification_annotations(true_samples, true_symbols, test_samples, tol)
            self.tp_by_tol[tol // self.spacing].extend(tp)
            self.fp_by_tol[tol // self.spacing].extend(fp)
            self.tn_by_tol[tol // self.spacing].extend(tn)
            self.fn_by_tol[tol // self.spacing].extend(fn)
        return self.compute()

    def match_classification_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        interval_start = 0
        interval_end = tolerance
        true_idx = 0
        true_queue = []
        test_idx = 0
        test_queue = []
        tp, fp, fn, tn = [], [], [], []
        while true_idx < len(true_samples) and true_samples[true_idx] <= interval_end:
            true_queue.append(true_idx)
            true_idx += 1

        while test_idx < len(test_samples) and test_samples[test_idx] <= interval_end:
            test_queue.append(test_idx)
            test_idx += 1

        while interval_end < max(true_samples[-1], test_samples[-1]):
            len_test = len(test_queue)
            len_true = len(true_queue)
            if len_test == len_true and len_true > 0:
                tp.append(interval_start)
            if len_test > len_true:
                fp.append(interval_start)
            if len_test < len_true:
                fn.append(interval_start)
            if len_test == 0 == len_true:
                tn.append(interval_start)

            interval_start += 1
            interval_end += 1
            if len(true_queue) > 0 and true_samples[true_queue[0]] < interval_start:
                true_queue.pop(0)
            if len(test_queue) > 0 and test_samples[test_queue[0]] < interval_start:
                test_queue.pop(0)
            if true_idx < len(true_samples) and true_samples[true_idx] <= interval_end:
                true_queue.append(true_idx)
                true_idx += 1
            if test_idx < len(test_samples) and test_samples[test_idx] <= interval_end:
                test_queue.append(test_idx)
                test_idx += 1
        return tp, fp, tn, fn

    def compute(self):
        metrics_per_tol = []
        for tp, fp, tn, fn in zip(self.tp_by_tol, self.fp_by_tol, self.tn_by_tol, self.fn_by_tol):
            metrics_per_tol.append(self.ppv_fpr(len(tp), len(fp), len(tn), len(fn)))
        return metrics_per_tol

    def ppv_fpr(self, tp, fp, tn, fn):
        return tp/max(tp + fn, 0.00001), fp/max(fp + tn, 0.00001)
