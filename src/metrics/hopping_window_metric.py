from bisect import bisect_right, bisect_left
import numpy as np

from metrics.classification_metric import ClassificationMetric


class HoppingWindow(ClassificationMetric):
    __abbrev__ = "Hop. Window"
    __parts__ = 10
    __steps__ = 6  # 2, 12, ..., 52

    def __init__(self, parts=__parts__):
        super().__init__()
        self.parts = parts
        self.tp_by_tol = [[0 for _ in range(self.__steps__)] for _ in range(parts)]
        self.fp_by_tol = [[0 for _ in range(self.__steps__)] for _ in range(parts)]
        self.tn_by_tol = [[0 for _ in range(self.__steps__)] for _ in range(parts)]
        self.fn_by_tol = [[0 for _ in range(self.__steps__)] for _ in range(parts)]

    def join(self, other):
        for p in range(self.parts):
            for s in range(self.__steps__):
                self.tp_by_tol[p][s] += other.tp_by_tol[p][s]
                self.fp_by_tol[p][s] += other.fp_by_tol[p][s]
                self.tn_by_tol[p][s] += other.tn_by_tol[p][s]
                self.fn_by_tol[p][s] += other.fn_by_tol[p][s]
        return self

    def match_annotations(self, true_samples, true_symbols, test_samples, sampling_frequency=360):
        sf = sampling_frequency // 5
        window_sizes = list(np.linspace(1, sf - (sf % self.parts), self.parts))
        step_sizes = list(np.linspace(sampling_frequency / 1000, sf, self.__steps__))
        for wi, ws in enumerate(window_sizes):
            for si, step in enumerate(step_sizes):
                cv = self.match_hopping_annotations(true_samples, test_samples, ws, step)
                self.tp_by_tol[wi][si] += cv[0]
                self.fp_by_tol[wi][si] += cv[1]
                self.tn_by_tol[wi][si] += cv[2]
                self.fn_by_tol[wi][si] += cv[3]

        return self.compute()

    def match_hopping_annotations(self, true_samples, test_samples, tolerance, step):
        tp, fp, fn, tn = 0, 0, 0, 0
        recording_len = 2 * true_samples[-1] - true_samples[-2] if len(true_samples) > 1 else 2 * true_samples[-1]
        if len(test_samples) == 0:
            num_tn = (recording_len // step) - tp - fp - fn + 1
            tn += max(int(num_tn), 0)
            fn = sum(map(lambda x: self.num_modulo(x - tolerance, tolerance + 1, step), true_samples))
            return 0, 0, fn, tn
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
                    left_start = max(true_beat - tolerance, 0)
                    left_end = min(test_samples[left_pred_idx] + tolerance, test_samples[right_pred_idx] - tolerance)

                    right_start = test_samples[right_pred_idx] - tolerance
                    right_end = min(true_beat + tolerance, test_samples[right_pred_idx])

                    tp += self.num_modulo(left_start, left_end - left_start, step) + self.num_modulo(right_start, right_end - right_start + 1, step)
                else:
                    num_tp = min(abs(test_samples[closest_pred_idx] - (true_beat - tolerance - 1)),
                                 abs(test_samples[closest_pred_idx] - (true_beat + tolerance + 1)),
                                 (test_samples[closest_pred_idx] // step) + 1)
                    start = max(true_beat - tolerance, test_samples[left_pred_idx] - tolerance, 0)

                    tp += self.num_modulo(start, int(num_tp), step)
            # are there some windows where no prediction lies
            if left_pred_idx != right_pred_idx and left_dist_to_beat + right_dist_to_beat > tolerance:
                start = max(test_samples[left_pred_idx] + tolerance, true_beat - tolerance, 0)
                end = min(test_samples[right_pred_idx] - tolerance, true_beat + tolerance)

                fn += self.num_modulo(start, end - start, step)
            if left_pred_idx == right_pred_idx and left_dist_to_beat != 0:
                if test_samples[left_pred_idx] < true_beat:
                    start = max(true_beat - tolerance, test_samples[left_pred_idx] + 1)
                    fn += self.num_modulo(start, min(left_dist_to_beat, tolerance), step)
                else:
                    start = min(true_beat, test_samples[left_pred_idx] - 1 - tolerance)
                    fn += self.num_modulo(start, min(left_dist_to_beat, tolerance), step)

        for pred_beat in test_samples:
            next_beat_idx = bisect_right(true_samples, pred_beat)
            previous_beat_idx = next_beat_idx - 1
            previous_beat = true_samples[previous_beat_idx] if previous_beat_idx >= 0 else - tolerance - 1
            if previous_beat == pred_beat:
                continue
            next_beat = true_samples[next_beat_idx] if next_beat_idx != len(true_samples) else previous_beat
            #if next_beat - pred_beat <= tolerance or pred_beat - previous_beat <= tolerance:
            #    continue
            start = max(previous_beat + 1, pred_beat - tolerance, 0)
            end = min(next_beat, pred_beat) if next_beat != previous_beat else pred_beat

            fp += self.num_modulo(start, end - start + 1, step)

        num_tn = (recording_len // step) - tp - fp - fn + 1

        tn += max(int(num_tn), 0)
        return tp, fp, tn, fn

    def num_modulo(self, start, length, step):
        if start % step != 0:
            true_start = start + (step - (start % step)) if start >= 0 else start + (step - (start % step))
        else:
            true_start = start
        return (start + length - true_start) // step + 1

    def compute(self):
        raise NotImplementedError


class HopTP(HoppingWindow):
    __abbrev__ = "Hop TP"

    def compute(self):
        return self.tp_by_tol


class HopFP(HoppingWindow):
    __abbrev__ = "Hop FP"

    def compute(self):
        return self.fp_by_tol


class HopTN(HoppingWindow):
    __abbrev__ = "Hop TN"

    def compute(self):
        return self.tn_by_tol


class HopFN(HoppingWindow):
    __abbrev__ = "Hop FN"

    def compute(self):
        return self.fn_by_tol
