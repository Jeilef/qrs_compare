import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import re
from functools import reduce
import numpy as np

from wfdb import rdann

from metrics.adapted_fixed_window_metric import AdPositivePredictiveValue, AdSensitivity, AdSpecificity
from metrics.metric import MeanError, join
from util.util import powerset


def read_evaluated_algorithms():
    algorithm_metrics = []
    for alg_subdir in os.listdir("algorithms"):
        metric_results = read_single_algorithm_results(alg_subdir)
        if metric_results:
            algorithm_metrics.append(metric_results)
    return algorithm_metrics


def read_single_algorithm_results(alg_subdir):
    m_file_path = os.path.join("algorithms", alg_subdir, "evaluation", "metrics.json")
    if os.path.isdir(os.path.join("algorithms", alg_subdir)) and os.path.exists(m_file_path):
        with open(m_file_path) as m_file:
            return json.load(m_file)


def evaluate_algorithm(alg_store):
    print("Evaluating...")
    acc_metrics = [MeanError, AdPositivePredictiveValue, AdSensitivity, AdSpecificity]
    metric_values = {}
    noise_names = ["em", "ma", "bw"]
    ps = list(powerset(noise_names))
    # need to be adapted to the available values
    for noise_comb in ps:
        noises = "_".join(noise_comb)
        metric_values[noises] = {}
        reg = "[a-zA-Z][0-9-_]+{}[0-9-_]+[.]atr".format(noises)
        loaded_data = list(read_ann_files(alg_store, reg))
        print("Loaded Eval Data")
        with cf.ProcessPoolExecutor(max_workers=len(acc_metrics)) as pool:
            computed_metrics = pool.map(evaluate_algorithm_with_metric,
                                        acc_metrics,
                                        list([loaded_data] * len(acc_metrics)))
        for met_idx, met_per_beat in enumerate(computed_metrics):
            for k in met_per_beat:
                met_per_beat[k] = met_per_beat[k].compute()
            metric_values[noises][acc_metrics[met_idx].__abbrev__] = met_per_beat

    print("Saving Evaluation Results to JSON")
    convert_metrics_to_json(alg_store, metric_values)


def read_ann_files(alg_store, file_name_regex=".*"):
    p = re.compile(file_name_regex)
    file_names = os.listdir(alg_store.groundtruth_dir())
    file_names = [f for f in file_names if p.match(f)]
    print(len(file_names), "file names")
    with cf.ProcessPoolExecutor(max_workers=10) as pool:
        prepared_ann_tuples = list(pool.map(read_ann_file, [alg_store] * len(file_names), file_names))
    return prepared_ann_tuples


def read_ann_file(alg_store, ann_file):
    pred_ann_file = os.path.join(alg_store.prediction_dir(), ann_file.rsplit('.')[0])
    gt_ann_file = os.path.join(alg_store.groundtruth_dir(), ann_file.rsplit('.')[0])
    ann_file_type = ann_file.split("_")[0]
    if os.path.exists(pred_ann_file + "." + ann_file.rsplit('.')[1]):
        pred_ann_ref = rdann(pred_ann_file, 'atr')
        gt_ann_ref = rdann(gt_ann_file, 'atr')
        pred_beats = pred_ann_ref.sample
        anno = gt_ann_ref.sample
        sampling_frequency = gt_ann_ref.fs
        gt_beat_type = gt_ann_ref.symbol[1]

        return create_evaluation_format(ann_file_type, anno, gt_beat_type, pred_beats, sampling_frequency)
    else:
        # occurs if algorithm does not output any annotation
        # print("No Output")
        gt_ann_ref = rdann(gt_ann_file, 'atr')
        anno = gt_ann_ref.sample
        pred_ann_ref_sample = []  # [[max(0, anno[1] - gt_ann_ref.fs)]]
        return [anno[1]], [gt_ann_ref.symbol[1]], pred_ann_ref_sample, gt_ann_ref.fs, ann_file_type


def create_evaluation_format(ann_file_type, anno, gt_beat_type, pred_beats, sampling_frequency):
    adapted_start = (anno[0] + anno[1]) / 2 if anno[0] != anno[1] else 0
    adapted_end = (anno[1] + anno[2]) / 2 if anno[1] != anno[2] else pred_beats[-1]
    samples = list(filter(lambda s: adapted_start <= s <= adapted_end, pred_beats))
    return [anno[1]], [gt_beat_type], samples, sampling_frequency, ann_file_type


def evaluate_algorithm_with_metric(metric, loaded_data):
    workers = mp.cpu_count() // 2
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        calc_metrics = list(pool.map(match_for_metric_on_data_part,
                                     loaded_data,
                                     list([metric]*len(loaded_data)),
                                     chunksize=(len(loaded_data) // workers) + 1))

        collected_metrics = {}
        for symbol, metric in calc_metrics:
            collected_metrics.setdefault(symbol, []).append(metric)

    typed_metrics = {}
    for symbol, metrics in collected_metrics.items():
        red_metric = reduce(join, metrics)
        typed_metrics[symbol] = red_metric
    return typed_metrics


def match_for_metric_on_data_part(ann_tuple, metric_class):
    typed_metric = metric_class()
    typed_metric.match_annotations(*ann_tuple[0:4])
    return ann_tuple[4], typed_metric


def convert_metrics_to_json(alg_store, acc_metrics):
    for key in acc_metrics:
        acc_metrics[key]["Name"] = alg_store.alg_name

    with open(os.path.join(alg_store.evaluation_dir(), "metrics.json"), "w") as metrics_file:
        metrics_file.write(json.dumps(acc_metrics))
