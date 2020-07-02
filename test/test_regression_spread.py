import unittest
from functools import reduce

from matplotlib import pyplot as plt
import numpy as np

from algorithm_evaluation import read_ann_files, evaluate_algorithm_with_metric
from algorithm_store import AlgorithmStore
from metrics.metric import MeanError, MeanSquaredError, MeanAbsoluteError, MeanErrorGt, MeanSquaredErrorGt, \
    MeanAbsoluteErrorGt, join


class TestSpread(unittest.TestCase):
    def setUp(self) -> None:
        self.alg_stores = AlgorithmStore.for_all_existing("../algorithms", "../comparison_data")

    def test_different_confusion_matrix_tresholds(self):
        algorthim_metrics = []

        for alg_num, alg_store in enumerate(self.alg_stores):
            print(alg_store.alg_name)
            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            me = evaluate_algorithm_with_metric(MeanError, loaded_data)
            mse = evaluate_algorithm_with_metric(MeanSquaredError, loaded_data)
            mae = evaluate_algorithm_with_metric(MeanAbsoluteError, loaded_data)
            gtme = evaluate_algorithm_with_metric(MeanErrorGt, loaded_data)
            gtmse = evaluate_algorithm_with_metric(MeanSquaredErrorGt, loaded_data)
            gtmae = evaluate_algorithm_with_metric(MeanAbsoluteErrorGt, loaded_data)

            combined_metrics = []
            combined_metrics.append(reduce(join, me.values()))
            combined_metrics.append(reduce(join, gtme.values()))
            combined_metrics.append(reduce(join, mse.values()))
            combined_metrics.append(reduce(join, gtmse.values()))
            combined_metrics.append(reduce(join, mae.values()))
            combined_metrics.append(reduce(join, gtmae.values()))

            combined_metrics = list(map(lambda x: x.compute(), combined_metrics))
            print(combined_metrics)
            algorthim_metrics.append(combined_metrics)

        for ic in range(6):
            alg_data = ""
            for ia, alg_met in enumerate(algorthim_metrics):
                alg_data += "{} {}\n".format(ia, alg_met[ic])
            with open("data/latex_data/reg-met{}.dat".format(ic), "w+") as data_file:
                data_file.write(alg_data)
