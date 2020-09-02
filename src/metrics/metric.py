def join(x, y):
    return x.join(y)


class Metric:
    __abbrev__ = ''

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        """Tries to match two lists of (supposed) QRS positions.

        Args:
            true_samples: List of samples representing the actual QRS positions.
            true_symbols: Annotation symbols for the samples in true_samples.
            test_samples: List of samples representing the detected QRS positions.
            tolerance: Maximum allowed distance between actual and detected QRS
                position.
                :param sampling_frequency:
        """
        raise NotImplementedError

    def compute(self):
        """
        This method shall compute and return the value of the metric
        :return:
        """
        raise NotImplementedError


class AreaUnderCurve(Metric):
    __abbrev__ = 'AuC'

    def __init__(self):
        self.predictions_per_qrs = []

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        prev_len = len(self.predictions_per_qrs)
        self.predictions_per_qrs.extend([[] for _ in true_samples])

        current_idx = 0
        current_complex = true_samples[0]
        next_complex = true_samples[1] if len(true_samples) > 1 else current_complex
        for ts in test_samples:
            while abs(current_complex - ts) > abs(next_complex - ts):
                current_complex = next_complex

                if current_idx + 1 < len(true_samples):
                    current_idx += 1

                next_complex = true_samples[current_idx]

            self.predictions_per_qrs[prev_len + current_idx].append((ts - current_complex)/sampling_frequency)

    def compute(self):
        pass


class RegressionMetric(Metric):
    def __init__(self):
        self.distance_to_true = []

    def join(self, other):
        self.distance_to_true.extend(other.distance_to_true)
        return self

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        next_idx = 1
        current_complex = true_samples[0]
        next_complex = true_samples[1] if len(true_samples) > 1 else current_complex
        for ts in test_samples:
            while abs(current_complex - ts) > abs(next_complex - ts):
                current_complex = next_complex
                next_idx += 1 if next_idx < len(true_samples) - 1 else 0
                next_complex = true_samples[next_idx]
            if (ts - current_complex)/sampling_frequency < -1:
                print("reg metric error: ", true_samples, test_samples, sampling_frequency)
            self.distance_to_true.append((ts - current_complex)/sampling_frequency)

        return self.compute()

    def compute(self):
        raise NotImplementedError


class RegressionMetricGt(RegressionMetric):
    def __init__(self):
        super().__init__()
        self.distance_to_true = []
        self.beats = 0

    def join(self, other):
        self.distance_to_true.extend(other.distance_to_true)
        self.beats += other.beats
        return self

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        self.beats += len(true_samples)

        next_idx = 1
        current_complex = true_samples[0]
        next_complex = true_samples[1] if len(true_samples) > 1 else current_complex

        for ts in test_samples:
            while abs(current_complex - ts) > abs(next_complex - ts):
                current_complex = next_complex
                next_idx += 1 if next_idx < len(true_samples) - 1 else 0
                next_complex = true_samples[next_idx]

            self.distance_to_true.append((ts - current_complex)/sampling_frequency)

        return self.compute()

    def compute(self):
        raise NotImplementedError


class MeanSquaredError(RegressionMetric):
    __abbrev__ = 'MSE'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        return sum(map(lambda x: x**2, self.distance_to_true))/len(self.distance_to_true)


class MeanSquaredErrorGt(RegressionMetricGt):
    __abbrev__ = 'MSE'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        return sum(map(lambda x: x**2, self.distance_to_true))/self.beats


class MeanAbsoluteError(RegressionMetric):
    __abbrev__ = 'MAE'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        return sum(map(lambda x: abs(x), self.distance_to_true))/len(self.distance_to_true)


class MeanAbsoluteErrorGt(RegressionMetricGt):
    __abbrev__ = 'MSE'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        return sum(map(lambda x: abs(x), self.distance_to_true))/self.beats


class MeanError(RegressionMetric):
    __abbrev__ = 'ME'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        if sum(self.distance_to_true) / len(self.distance_to_true) > 1:
            print("ME Possible Error:", len(self.distance_to_true), self.distance_to_true)
        return sum(self.distance_to_true)/len(self.distance_to_true)


class MeanErrorGt(RegressionMetricGt):
    __abbrev__ = 'MSE'

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        return sum(self.distance_to_true)/self.beats


class DynamicThreshold(RegressionMetric):
    __abbrev__ = "DynThres"

    def compute(self):
        if len(self.distance_to_true) == 0:
            return 0
        abs_dist = list(map(lambda x: abs(x), self.distance_to_true))
        abs_dist = sorted(abs_dist)
        ninety_nine_idx = int((len(abs_dist) - 1) * 0.9999)
        return int(abs_dist[ninety_nine_idx])
