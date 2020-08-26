import os
import re
from functools import reduce
import numpy as np
import concurrent.futures as cf
import sys
import wfdb
from func_timeout import func_timeout, FunctionTimedOut

sys.path.append("../src")

from algorithm_evaluation import read_ann_files, evaluate_algorithm_with_metric, create_evaluation_format, \
    match_for_metric_on_data_part
from algorithm_store import AlgorithmStore
from data_handling.data_docker_setup import ECGData
from metrics.adapted_fixed_window_metric import AdTP, AdFP, AdFN, AdTN
from metrics.metric import MeanError, join
from util.easy_algorithm_execution import algs_with_name


class MockAlgStore(AlgorithmStore):
    def __init__(self, pred_alg_dir, gt_alg_dir="../comparison_data/annotations"):
        self.pred_alg_dir = pred_alg_dir
        self.gt_alg_dir = gt_alg_dir

    def groundtruth_dir(self):
        return self.gt_alg_dir

    def prediction_dir(self):
        return self.pred_alg_dir


def create_all_data():
    base_path = "../comparison_data_large_slices"
    ecg = ECGData(base_path + "/signal",
                  base_path + "/annotations", min_noise=0, max_noise=2, num_noise=5)

    ecg.read_noise_data()
    ecg.__records_per_beat_type__ = 10000
    ecg.__splice_size_start__ = 10
    ecg.__splice_size_end__ = 21
    ecg.__splice_size_step_size__ = 2
    ecg.__stepping_beat_position__ = False
    ecg.setup_evaluation_data()
    print(ecg.failed_writes)


def generate_predictions(base_save_path, comp_data_path="../comparison_data_noise/"):
    p = re.compile('.*N_[0-9].[0-9]+[a-zA-Z_]*_[0-9]+.*')
    for dirpath, subdir, filenames in os.walk(comp_data_path + "signal"):
        print("Scanning: ", dirpath)
        if p.match(dirpath) and "RECORDS" in filenames:
            print(dirpath, "confirmed")
            with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                records = list(f.readlines())
            for r in records:
                print("Processing", r)
                ann_file_name = os.path.join(comp_data_path + "annotations", r.rstrip('\n'))
                ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(
                    ann_file_name + '.atr')
                rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                rec_file_exists = os.path.exists(rec_file_name + '.dat') and os.path.isfile(
                    rec_file_name + '.dat')
                print("Exist check", ann_file_name, ann_file_exists, rec_file_name, rec_file_exists)
                if ann_file_exists and rec_file_exists:
                    try:
                        sample, meta = func_timeout(5, wfdb.rdsamp, args=(rec_file_name,), kwargs={"channels": [0]})
                    except:
                        print("Failed reading sample", r)
                        continue
                    # sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                    rec_name = rec_file_name.split(os.sep)[-1]

                    # 150 is a restriction for some qrs detectors
                    if len(sample) > 150:
                        for alg_name, alg_func in algs_with_name().items():
                            print(alg_name)
                            save_path = base_save_path + alg_name
                            os.makedirs(save_path, exist_ok=True)
                            alg_func(meta, rec_name, save_path, sample)
                            print("Done", alg_name)


def generate_metric_values(prediction_dir, splice_save_dir):
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
                    alg_splice_size[alg_name][noise_level][splice_size][
                        metrics[met_idx].__abbrev__] = reduced_metric.compute()
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
                with open(splice_save_dir + "/{}-{}-{}.dat".format(metrics_abbrev, alg, noise_level),
                          "w") as splice_file:
                    splice_file.write(write_str)


def generate_predictions_with_metrics(comp_data_path="../comparison_data_noise/",
                                      metric_path="data/latex_data/direct-metrics"):
    p = re.compile('.*N_[0-9].[0-9]+[a-zA-Z_]*_[0-9]+.*')
    metrics = [MeanError, AdTP, AdFP, AdTN, AdFN]
    typed_metrics = {}

    for dirpath, subdir, filenames in os.walk(comp_data_path + "signal"):
        print("Scanning: ", dirpath)
        if p.match(dirpath) and "RECORDS" in filenames:
            print(dirpath, "confirmed")
            with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                records = list(f.readlines())
            current_folder = dirpath.split(os.sep)[-1]
            typed_metrics[current_folder] = {}
            for r in records:
                print("Processing", r)
                ann_file_name = os.path.join(comp_data_path + "annotations", r.rstrip('\n'))
                ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(
                    ann_file_name + '.atr')
                rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                rec_file_exists = os.path.exists(rec_file_name + '.dat') and os.path.isfile(
                    rec_file_name + '.dat')
                if ann_file_exists and rec_file_exists:
                    try:
                        annotation = wfdb.rdann(ann_file_name, 'atr')
                        sample, meta = func_timeout(5, wfdb.rdsamp, args=(rec_file_name,), kwargs={"channels": [0]})
                    except:
                        print("Failed reading sample", r)
                        continue
                    # sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                    rec_name = rec_file_name.split(os.sep)[-1]

                    # 150 is a restriction for some qrs detectors
                    if len(sample) > 150:
                        for alg_name, alg_func in algs_with_name().items():
                            typed_metrics[current_folder].setdefault(alg_name, {})
                            r_peaks = alg_func(meta, rec_name, "", sample, save=False)
                            if len(r_peaks) == 0:
                                eval_tuple = [annotation.sample[1]], [annotation.symbol[1]], [], meta['fs'], r[0]
                            else:
                                eval_tuple = create_evaluation_format(annotation.symbol[1], annotation.sample,
                                                                      r[0], r_peaks, meta['fs'])
                            for m_idx, m in enumerate(metrics):
                                beat_type, metric = match_for_metric_on_data_part(eval_tuple, m)
                                typed_metrics[current_folder][alg_name].setdefault(m_idx, []).append(metric)

    print("Saving Metrics per folder")
    os.makedirs(metric_path, exist_ok=True)
    for folder in typed_metrics:
        for alg_name in typed_metrics[folder]:
            for metric_idx in typed_metrics[folder][alg_name]:
                combined_metric = reduce(join, typed_metrics[folder][alg_name][metric_idx])
                with open(metric_path + "/{}--{}--{}.dat".format(folder, alg_name, combined_metric.__abbrev__),
                          "w") as splice_file:
                    splice_file.write(str(combined_metric.compute()))


if __name__ == "__main__":
    # generate_predictions("data/algorithm_prediction/", "../comparison_data/")
    # N_0-5_em_ma_3_2177, S_0-0_3_264

    generate_predictions_with_metrics("../comparison_data_large_slices/", "data/latex_data/large-slices")
    #create_all_data()
