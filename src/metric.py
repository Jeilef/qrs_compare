class Metric:
    def match_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        """Tries to match two lists of (supposed) QRS positions.

        Args:
            true_samples: List of samples representing the actual QRS positions.
            true_symbols: Annotation symbols for the samples in true_samples.
            test_samples: List of samples representing the detected QRS positions.
            tolerance: Maximum allowed distance between actual and detected QRS
                position.
        """
        raise NotImplementedError

    def compute(self):
        """
        This method shall compute and return the value of the metric
        :return:
        """
        raise NotImplementedError


class ClassificationMetric(Metric):
    def __init__(self):
        self.fn = []
        self.fp = []
        self.tp = []

    def match_annotations(self, true_samples, true_symbols, test_samples, tolerance):
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

        self.fn = fn
        self.fp = fp
        self.tp = tp
        return tp, fp, fn

    def compute(self):
        raise NotImplementedError


class PositivePredictiveValue(ClassificationMetric):
    def match_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        super().match_annotations(true_samples, true_symbols, test_samples, tolerance)
        return self.compute()

    def compute(self):
        return len(self.tp) / (len(self.fp) + len(self.tp))


class Sensitivity(ClassificationMetric):
    def match_annotations(self, true_samples, true_symbols, test_samples, tolerance):
        super().match_annotations(true_samples, true_symbols, test_samples, tolerance)
        return self.compute()

    def compute(self):
        return len(self.tp) / (len(self.fn) + len(self.tp))
