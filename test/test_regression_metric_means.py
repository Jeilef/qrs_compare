import unittest
from matplotlib import pyplot as plt
import numpy as np

from algorithm_evaluation import read_ann_files, evaluate_algorithm_with_metric
from algorithm_store import AlgorithmStore
from metrics.metric import MeanError, RegressionMetric


class TestRegressionMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.alg_stores = AlgorithmStore.for_all_existing("../algorithms", "../comparison_data")

    def test_different_confusion_matrix_tresholds(self):
        for alg_num, alg_store in enumerate(self.alg_stores):
            print(alg_store.alg_name)
            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            me = evaluate_algorithm_with_metric(MeanError, loaded_data)
            distances = []
            for data_type in me:
                distances.extend(me[data_type].distance_to_true)
            bins = [-1, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
            hist = np.histogram(distances, bins=bins)
            print(list(hist[0]))
            print(list(hist[1]))
            file_data = ""
            for i in range(len(hist[0])):
                file_data += "{} {}\n".format(hist[1][i], hist[0][i])
            with open("data/latex_data/offset-al{}.dat".format(alg_num), "w+") as data_file:
                data_file.write(file_data)

    def test_reg_metric_does_not_error(self):
        gt = [7388]
        pred = [6482, 6977, 7472]
        fs = 500
        metric = MeanError()
        metric.match_annotations(gt, ["N"]*len(gt), pred, fs)
