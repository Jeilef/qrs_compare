import os
import numpy as np
import sys
sys.path.append('../src')

import unittest
from functools import reduce
import concurrent.futures as cf

from algorithm_evaluation import read_ann_files, evaluate_algorithm_with_metric
from algorithm_store import AlgorithmStore
from metrics.adapted_fixed_window_metric import AdTP, AdFP, AdTN, AdFN
from metrics.metric import MeanError, join
from util.easy_algorithm_execution import algs_with_name
from data_handling.data_docker_setup import ECGData


class MockAlgStore(AlgorithmStore):
    def __init__(self, pred_alg_dir, gt_alg_dir="../comparison_data/annotations"):
        self.pred_alg_dir = pred_alg_dir
        self.gt_alg_dir = gt_alg_dir

    def groundtruth_dir(self):
        return self.gt_alg_dir

    def prediction_dir(self):
        return self.pred_alg_dir


class TestDataSplicing(unittest.TestCase):
    def setUp(self) -> None:
        base_path = "../comparison_data"
        self.ecg = ECGData(base_path + "/signal",
                           base_path + "/annotations", 0, 2, 5)

        self.ecg.read_noise_data()
        print("finished setup")

    def test_read_all_data(self):
        self.ecg.__records_per_beat_type__ = 1000
        self.ecg.setup_evaluation_data()

    def test_alg_metrics(self):
        splice_save_dir = "data/latex_data/splices"
        prediction_dir = "data/algorithm_prediction/"

        self.generate_metric_values(prediction_dir, splice_save_dir)

    def test_noise_alg_metrics(self):
        splice_save_dir = "data/latex_data/splices_noise"
        prediction_dir = "data/algorithm_prediction_noise/"

        self.generate_metric_values(prediction_dir, splice_save_dir)

    def generate_metric_values(self, prediction_dir, splice_save_dir):
        alg_splice_size = {}
        metrics = [MeanError, AdTP, AdFP, AdTN, AdFN]
        for alg_name, alg_func in algs_with_name().items():
            mas = MockAlgStore(prediction_dir + alg_name)
            alg_splice_size[alg_name] = {}
            print(alg_name)
            # need to be adapted to the available values
            for noise_level in np.linspace(0, 2, 5):
                noise_str = str(noise_level).replace(".", "-")
                alg_splice_size[alg_name][noise_level] = {}
                for splice_size in range(3, 11, 2):
                    reg = "[a-zA-Z]_{}_{}.*_[0-9]+\\.atr".format(noise_str, splice_size)
                    loaded_data = read_ann_files(mas, reg)
                    alg_splice_size[alg_name][noise_level][splice_size] = {}
                    with cf.ProcessPoolExecutor(max_workers=len(metrics)) as pool:
                        met_per_beats = list(pool.map(evaluate_algorithm_with_metric, metrics,
                                                      list([loaded_data] * len(metrics))))
                    for met_idx, met_per_beat in enumerate(met_per_beats):
                        reduced_metric = reduce(join, met_per_beat.values())
                        alg_splice_size[alg_name][noise_level][splice_size][metrics[met_idx].__abbrev__] = reduced_metric.compute()
                    print(alg_splice_size)

        for alg in alg_splice_size:
            os.makedirs(splice_save_dir, exist_ok=True)
            for noise_level, noise_vals in alg_splice_size[alg].items():
                write_strs = {}
                for spli, vals in noise_vals.items():
                    for metric, metric_value in vals.items():
                        write_strs.setdefault(metric, "")
                        write_strs[metric] += "{} {}\n".format(spli, metric_value)
                for metrics_abbrev, write_str in write_strs.items():
                    with open(splice_save_dir + "/{}-{}-{}.dat".format(metrics_abbrev, alg, noise_level), "w") as splice_file:
                        splice_file.write(write_str)

    def test_predictions_not_empty(self):
        alg_splice_size = {}
        for alg_name, alg_func in algs_with_name().items():
            mas = MockAlgStore("alg_pred2/" + alg_name)
            alg_splice_size[alg_name] = {}
            print(alg_name)
            for splice_size in range(1, 22, 2):
                reg = "[a-zA-Z]_0-0_{}_[0-9]+\\.atr".format(splice_size)
                loaded_data = read_ann_files(mas, reg)





















