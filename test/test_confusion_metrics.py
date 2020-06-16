import os
import unittest

from algorithm_evaluation import evaluate_algorithm, read_ann_files, evaluate_algorithm_with_metric
from algorithm_store import AlgorithmStore
from metrics.classification_metric import TP, FP, FN, TN
from metrics.hopping_window_metric import HopTP, HopFP, HopTN, HopFN
from metrics.window_based_classification_metric import WinTP, WinTN, WinFN, WinFP


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
        for alg_num, alg_store in enumerate(self.alg_stores):
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
            grouped = list(map(sum, zip(sum_tp, sum_tn, sum_fn, sum_fp)))
            self.save_sliding_window_metrics(sum_tp, grouped, alg_num, "TP")
            self.save_sliding_window_metrics(sum_fp, grouped, alg_num, "FP")
            self.save_sliding_window_metrics(sum_tn, grouped, alg_num, "TN")
            self.save_sliding_window_metrics(sum_fn, grouped, alg_num, "FN")
            # print("tp", self.print_array_in_pgf_plots(sum_tp))
            # print("fp", self.print_array_in_pgf_plots(sum_fp))
            # print("tn", self.print_array_in_pgf_plots(sum_tn))
            # print("fn", self.print_array_in_pgf_plots(sum_fn))

    def save_sliding_window_metrics(self, met, grouped, alg_num=None, metric_name=None):
        printed_vals = ""
        prints = ""
        for i in range(len(met)):
            prints += "{} {}\n".format(21.88888889 * i + 3, met[i] / grouped[i])
            printed_vals += "{} ".format(met[i] / grouped[i])
        print(printed_vals)

        with open("data/latex_data/sli-al{}-{}.dat".format(alg_num, metric_name), "w+") as data_file:
            data_file.write(prints)

    def test_different_confusion_matrix_tresholds_fixed_window(self):
        for alg_num, alg_store in enumerate(self.alg_stores):
            print(alg_store.alg_name)
            sum_tp = [0] * 10
            sum_fp = [0] * 10
            sum_tn = [0] * 10
            sum_fn = [0] * 10

            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            tps = evaluate_algorithm_with_metric(WinTP, loaded_data)
            fps = evaluate_algorithm_with_metric(WinFP, loaded_data)
            tns = evaluate_algorithm_with_metric(WinTN, loaded_data)
            fns = evaluate_algorithm_with_metric(WinFN, loaded_data)

            for data_type in tps:
                tp_vals = tps[data_type].compute()
                fp_vals = fps[data_type].compute()
                tn_vals = tns[data_type].compute()
                fn_vals = fns[data_type].compute()

                for i in range(len(tp_vals)):
                    self.assertLessEqual(0, tp_vals[i])
                    self.assertLessEqual(0, fp_vals[i])
                    self.assertLessEqual(0, tn_vals[i])
                    self.assertLessEqual(0, fn_vals[i])
                    sum_tp[i] += tp_vals[i]
                    sum_fp[i] += fp_vals[i]
                    sum_tn[i] += tn_vals[i]
                    sum_fn[i] += fn_vals[i]

            grouped = list(map(sum, zip(sum_tp, sum_tn, sum_fn, sum_fp)))
            self.save_fixed_window_metrics(sum_tp, grouped, alg_num, "TP")
            self.save_fixed_window_metrics(sum_fp, grouped, alg_num, "FP")
            self.save_fixed_window_metrics(sum_tn, grouped, alg_num, "TN")
            self.save_fixed_window_metrics(sum_fn, grouped, alg_num, "FN")

    def save_fixed_window_metrics(self, met, grouped, alg_num=None, metric_name=None):
        prints = ""
        for i in range(len(met)):
            prints += "{} {}\n".format(21.88888889 * i + 3, met[i] / grouped[i])

        with open("data/latex_data/fix-al{}-{}.dat".format(alg_num, metric_name), "w+") as data_file:
            data_file.write(prints)

    def print_array_in_pgf_plots(self, a):
        s = ""
        for i, x in enumerate(a):
            s += "({}, {})".format((2*i + 1) * 10, x)
        return s

    def test_different_confusion_matrix_tresholds_hopping_window(self):
        for alg_idx, alg_store in enumerate(self.alg_stores):
            print(alg_store.alg_name)
            steps = 6
            sum_tp = [[0 for _ in range(steps)] for _ in range(10)]
            sum_fp = [[0 for _ in range(steps)] for _ in range(10)]
            sum_tn = [[0 for _ in range(steps)] for _ in range(10)]
            sum_fn = [[0 for _ in range(steps)] for _ in range(10)]

            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            tps = evaluate_algorithm_with_metric(HopTP, loaded_data)
            fps = evaluate_algorithm_with_metric(HopFP, loaded_data)
            tns = evaluate_algorithm_with_metric(HopTN, loaded_data)
            fns = evaluate_algorithm_with_metric(HopFN, loaded_data)

            for data_type in tps:
                tp_vals = tps[data_type].compute()
                fp_vals = fps[data_type].compute()
                tn_vals = tns[data_type].compute()
                fn_vals = fns[data_type].compute()
                for i in range(len(tp_vals)):
                    for j in range(len(tp_vals[i])):
                        sum_tp[i][j] += tp_vals[i][j]
                        sum_fp[i][j] += fp_vals[i][j]
                        sum_tn[i][j] += tn_vals[i][j]
                        sum_fn[i][j] += fn_vals[i][j]

            a = [0] * len(sum_tp[0])
            for j in range(len(sum_tp[0])):
                a[j] += max(sum_tp[0][j] + sum_fp[0][j] + sum_tn[0][j] + sum_fn[0][j], 0.000001)
            print("TP")
            self.save_hopping_metrics(sum_tp, a, alg_idx, "TP")
            print("FP")
            self.save_hopping_metrics(sum_fp, a, alg_idx, "FP")
            print("TN")
            self.save_hopping_metrics(sum_tn, a, alg_idx, "TN")
            print("FN")
            self.save_hopping_metrics(sum_fn, a, alg_idx, "FN")

    def save_hopping_metrics(self, met, grouped, alg_num=None, metric_name=None, save_data=True):
        prints = ["" for _ in range(len(met[0]))]
        for i in range(len(met)):
            for j in range(len(met[i])):
                prints[j] += "{} {}\n".format(21.88888889 * i + 3, met[i][j] / grouped[j])
                if j == 0:
                    print(i, met[i][j] / grouped[j])
        if save_data:
            for i, s in enumerate(prints):
                with open("data/latex_data/hop-al{}-{}-{}.dat".format(alg_num, metric_name, i), "w+") as data_file:
                    data_file.write(s)

    def print_for_pgf_with_step_sizes(self, a):
        s = ""
        for i, x in enumerate(a):
            s += "({}, {})".format(9.6 * i + 3, x)
        return s

    def test_gqrs_hopping_window(self):
        for alg_idx, alg_store in enumerate(self.alg_stores):
            if alg_store.alg_name != "gqrs":
                continue
            print(alg_store.alg_name)
            steps = 6
            sum_tp = [[0 for _ in range(steps)] for _ in range(10)]
            sum_fp = [[0 for _ in range(steps)] for _ in range(10)]
            sum_tn = [[0 for _ in range(steps)] for _ in range(10)]
            sum_fn = [[0 for _ in range(steps)] for _ in range(10)]

            loaded_data = list(read_ann_files(alg_store))
            print(len(loaded_data), "loaded data")
            tps = evaluate_algorithm_with_metric(HopTP, loaded_data)
            fps = evaluate_algorithm_with_metric(HopFP, loaded_data)
            tns = evaluate_algorithm_with_metric(HopTN, loaded_data)
            fns = evaluate_algorithm_with_metric(HopFN, loaded_data)

            for data_type in tps:
                tp_vals = tps[data_type].compute()
                fp_vals = fps[data_type].compute()
                tn_vals = tns[data_type].compute()
                fn_vals = fns[data_type].compute()
                for i in range(len(tp_vals)):
                    for j in range(len(tp_vals[i])):
                        sum_tp[i][j] += tp_vals[i][j]
                        sum_fp[i][j] += fp_vals[i][j]
                        sum_tn[i][j] += tn_vals[i][j]
                        sum_fn[i][j] += fn_vals[i][j]

            a = [0] * len(sum_tp[0])
            for j in range(len(sum_tp[0])):
                a[j] += max(sum_tp[0][j] + sum_fp[0][j] + sum_tn[0][j] + sum_fn[0][j], 0.000001)
            print("TP")
            self.save_hopping_metrics(sum_tp, a, alg_idx, "TP", False)
            print("FP")
            self.save_hopping_metrics(sum_fp, a, alg_idx, "FP", False)
            print("TN")
            self.save_hopping_metrics(sum_tn, a, alg_idx, "TN", False)
            print("FN")
            self.save_hopping_metrics(sum_fn, a, alg_idx, "FN", False)
