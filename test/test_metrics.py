import os
import unittest

from algorithm_evaluation import evaluate_algorithm, read_ann_files, evaluate_algorithm_with_metric
from algorithm_store import AlgorithmStore
from metrics.classification_metric import TP, FP, FN, TN


class TestManipData(unittest.TestCase):
    def setUp(self) -> None:
        self.alg_stores = AlgorithmStore.for_all_existing("../algorithms", "../comparison_data")

    def test_confusion_matrix_treshold(self):
        for alg_store in self.alg_stores:
            print(alg_store.alg_name)
            sum_tp = 0
            sum_fp = 0
            sum_tn = 0
            sum_fn = 0

            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            tps = evaluate_algorithm_with_metric(TP, loaded_data)
            fps = evaluate_algorithm_with_metric(FP, loaded_data)
            tns = evaluate_algorithm_with_metric(TN, loaded_data)
            fns = evaluate_algorithm_with_metric(FN, loaded_data)

            for data_type in tps:
                tp_vals = tps[data_type].compute()
                fp_vals = fps[data_type].compute()
                tn_vals = tns[data_type].compute()
                fn_vals = fns[data_type].compute()
                max_vals = min(zip(range(len(tp_vals)), tp_vals, fp_vals, tn_vals, fn_vals),
                               key=lambda x: (x[2] ** 2 + x[4] ** 2)**0.5)
                # print("1", data_type, max_vals)
                max_vals = max(zip(range(len(tp_vals)), tp_vals, fp_vals, tn_vals, fn_vals),
                               key=lambda x: x[1] + x[3] - x[2] - x[4])
                # print("2", data_type, max_vals)
                max_vals = max(zip(range(len(tp_vals)), tp_vals, fp_vals, tn_vals, fn_vals),
                               key=lambda x: x[1])
                # print("3", data_type, max_vals)
                max_vals = min(zip(range(len(tp_vals)), tp_vals, fp_vals, tn_vals, fn_vals),
                               key=lambda x: ((x[1] - sum(x[1:])) ** 2 + (x[3] - sum(x[1:])) ** 2)**0.5)
                # print("4", data_type, max_vals)
                max_vals = min(zip(range(len(tp_vals)), tp_vals, fp_vals, tn_vals, fn_vals),
                               key=lambda x: ((x[1]/max(x[1] + x[4], 0.000001) - 1) ** 2 + (x[3]/max(x[3] + x[2], 0.000001) - 1) ** 2) ** 0.5)
                # print("5", data_type, max_vals)
                sum_tp += tp_vals[-1]
                sum_fp += fp_vals[-1]
                sum_tn += tn_vals[-1]
                sum_fn += fn_vals[-1]
               # print("")
            print("All", sum_tp, sum_fp, sum_tn, sum_fn)

    def test_different_confusion_matrix_tresholds(self):
        for alg_store in self.alg_stores:
            print(alg_store.alg_name)
            sum_tp = [0] * 10
            sum_fp = [0] * 10
            sum_tn = [0] * 10
            sum_fn = [0] * 10

            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            tps = evaluate_algorithm_with_metric(TP, loaded_data)
            fps = evaluate_algorithm_with_metric(FP, loaded_data)
            tns = evaluate_algorithm_with_metric(TN, loaded_data)
            fns = evaluate_algorithm_with_metric(FN, loaded_data)

            for data_type in tps:
                tp_vals = tps[data_type].compute()
                fp_vals = fps[data_type].compute()
                tn_vals = tns[data_type].compute()
                fn_vals = fns[data_type].compute()

                for i in range(len(tp_vals)):
                    sum_tp[i] += tp_vals[i]
                    sum_fp[i] += fp_vals[i]
                    sum_tn[i] += tn_vals[i]
                    sum_fn[i] += fn_vals[i]

            print("tp", sum_tp)
            print("fp", sum_fp)
            print("tn", sum_tn)
            print("fn", sum_fn)
            print("tp+tn", list(map(lambda x: x[0] + x[1], zip(sum_tp, sum_tn))))
