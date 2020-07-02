import concurrent.futures as cf
import multiprocessing as mp
import json
import os
from functools import reduce

from wfdb import rdann

from metrics.classification_metric import PositivePredictiveValue, Sensitivity, F1, RoCCurve, PPVSpec
from metrics.metric import MeanSquaredError, MeanAbsoluteError, MeanError, DynamicThreshold, join
from metrics.fixed_window_classification_metric import WindowedF1Score, WindowedSpecificity, WindowedPPV, \
    WindowedPPVSpec


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
    acc_metrics = [WindowedF1Score, PositivePredictiveValue, Sensitivity, F1, MeanSquaredError, MeanAbsoluteError,
                   MeanError, DynamicThreshold, PPVSpec, WindowedPPVSpec]

    loaded_data = list(read_ann_files(alg_store))

    print("Loaded Eval Data")
    with cf.ProcessPoolExecutor(max_workers=len(acc_metrics)) as pool:
        computed_metrics = pool.map(evaluate_algorithm_with_metric,
                                    acc_metrics,
                                    list([loaded_data] * len(acc_metrics)))
    print("Saving Evaluation Results to JSON")
    convert_metrics_to_json(alg_store, list(computed_metrics))


def read_ann_files(alg_store):
    file_names = os.listdir(alg_store.groundtruth_dir())
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
        anno = gt_ann_ref.sample
        adapted_start = (anno[0] + anno[1]) / 2 if anno[0] != anno[1] else 0
        adapted_end = (anno[1] + anno[2]) / 2 if anno[1] != anno[2] else pred_ann_ref.sample[-1]
        samples = list(filter(lambda s: adapted_start <= s <= adapted_end, pred_ann_ref.sample))
        #if not samples:
            # print("Filtered", anno, pred_ann_ref.sample, len(pred_ann_ref.sample))
        #    samples = [max(0, anno[1] - gt_ann_ref.fs)]
        return [anno[1]], [gt_ann_ref.symbol[1]], samples, gt_ann_ref.fs, ann_file_type
    else:
        # occurs if algorithm does not output any annotation
        # print("No Output")
        gt_ann_ref = rdann(gt_ann_file, 'atr')
        anno = gt_ann_ref.sample
        pred_ann_ref_sample = []  # [[max(0, anno[1] - gt_ann_ref.fs)]]
        return [anno[1]], [gt_ann_ref.symbol[1]], pred_ann_ref_sample, gt_ann_ref.fs, ann_file_type


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
    json_dict = {"Name": alg_store.alg_name}
    print(acc_metrics.__class__, acc_metrics)
    for typed_metrics in acc_metrics:
        computed_metrics = {}
        abbreviation = ""
        for data_type in typed_metrics:
            abbreviation = typed_metrics[data_type].__abbrev__
            computed_metrics[data_type] = typed_metrics[data_type].compute()
        json_dict[abbreviation] = computed_metrics

    with open(os.path.join(alg_store.evaluation_dir(), "metrics.json"), "w") as metrics_file:
        metrics_file.write(json.dumps(json_dict))
