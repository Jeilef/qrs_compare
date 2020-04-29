class Metric:
    __abbrev__ = ''
    def match_annotations(self, true_samples, true_symbols, test_samples):
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


class RegressionMetric:
    def __init__(self):
        self.distance_to_true = []

    def match_annotations(self, true_samples, true_symbols, test_samples):

        idx = 1
        last_complex = true_samples[0]
        next_complex = true_samples[1]
        for ts in test_samples:
            if abs(last_complex - ts) <= abs(next_complex - ts):
                self.distance_to_true.append(ts - last_complex)
            else:
                self.distance_to_true.append(ts - next_complex)
                last_complex = next_complex
                idx += 1 if idx < len(true_samples) - 1 else 0
                next_complex = true_samples[idx]
        return self.compute()

    def compute(self):
        raise NotImplementedError


class MeanSquaredError(RegressionMetric):
    __abbrev__ = 'MSE'

    def compute(self):
        return sum(map(lambda x: x**2, self.distance_to_true))/len(self.distance_to_true)


class MeanAbsoluteError(RegressionMetric):
    __abbrev__ = 'MAE'

    def compute(self):
        return sum(map(lambda x: abs(x), self.distance_to_true))/(len(self.distance_to_true))


class MeanError(RegressionMetric):
    __abbrev__ = 'ME'

    def compute(self):
        return sum(self.distance_to_true)/len(self.distance_to_true)
