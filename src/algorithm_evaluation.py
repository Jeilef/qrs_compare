import json
import os

import dill as dill
from wfdb import rdann
import concurrent.futures as cf
import multiprocessing as mp

from metrics.classification_metric import PositivePredictiveValue, Sensitivity, F1, RoCCurve
from metrics.metric import MeanSquaredError, MeanAbsoluteError, MeanError, DynamicThreshold


def read_evaluated_algorithms():
    algorithm_metrics = []
    for alg_subdir in os.listdir("algorithms"):
        m_file_path = os.path.join("algorithms", alg_subdir, "evaluation", "metrics.json")
        if os.path.isdir(os.path.join("algorithms", alg_subdir)) and os.path.exists(m_file_path):
            with open(m_file_path) as m_file:
                algorithm_metrics.append(json.load(m_file))
    return algorithm_metrics


def evaluate_algorithm(alg_store):
    print("Evaluating...")
    acc_metrics = [RoCCurve, PositivePredictiveValue, Sensitivity, F1, MeanSquaredError, MeanAbsoluteError, MeanError,
                   DynamicThreshold]

    loaded_data = list(read_ann_files(alg_store))

    print("Loaded Eval Data", dill.pickles(loaded_data))
    with cf.ProcessPoolExecutor(max_workers=len(acc_metrics)) as pool:
        computed_metrics = pool.map(evaluate_algorithm_with_metric, list([alg_store] * len(acc_metrics)),
                                    acc_metrics,
                                    list([loaded_data] * len(acc_metrics)))
    print("Saving Evaluation Results to JSON")
    convert_metrics_to_json(alg_store, list(computed_metrics))


def read_ann_files(alg_store):
    file_names = os.listdir(alg_store.groundtruth_dir())
    with cf.ProcessPoolExecutor(max_workers=10) as pool:
        prepared_ann_tuples = pool.map(read_ann_file, [alg_store] * len(file_names), file_names)
    return prepared_ann_tuples


def read_ann_file(alg_store, ann_file):
    pred_ann_file = os.path.join(alg_store.prediction_dir(), ann_file.rsplit('.')[0])
    gt_ann_file = os.path.join(alg_store.groundtruth_dir(), ann_file.rsplit('.')[0])
    ann_file_type = ann_file.split("_")[0]
    if os.path.exists(pred_ann_file + "." + ann_file.rsplit('.')[1]):
        pred_ann_ref = rdann(pred_ann_file, 'atr')
        gt_ann_ref = rdann(gt_ann_file, 'atr')
        anno = gt_ann_ref.sample
        samples = list(filter(lambda s: (anno[0] + anno[1]) / 2 <= s <= (anno[1] + anno[2]) / 2, pred_ann_ref.sample))
        return [anno[1]], [gt_ann_ref.symbol[1]], samples, gt_ann_ref.fs, ann_file_type
    else:
        # occurs if algorithm does not output any annotation
        pred_ann_ref_sample = [-1]
        gt_ann_ref = rdann(gt_ann_file, 'atr')
        anno = gt_ann_ref.sample
        return [anno[1]], [gt_ann_ref.symbol[1]], pred_ann_ref_sample, gt_ann_ref.fs, ann_file_type


def evaluate_algorithm_with_metric(alg_store, metric, loaded_data):
    print("Starting:", metric.__abbrev__)
    typed_metrics = create_metric_for_each_data_type(metric, alg_store.groundtruth_dir())
    for idx, ann_tuple in enumerate(loaded_data):
        print("{} currently at: {}%".format(metric.__abbrev__, ((idx * 100000 // len(loaded_data)) / 1000)))
        typed_metric = typed_metrics[ann_tuple[4]]
        typed_metric.match_annotations(*ann_tuple[0:4])

    print("Finished:", metric.__abbrev__)
    return typed_metrics


def create_metric_for_each_data_type(metric_class, data_directory):
    files = os.listdir(data_directory)
    types = list(set(map(lambda x: x.split("_")[0], files)))
    typed_metrics = {}
    for data_type in types:
        typed_metrics[data_type] = metric_class()
    return typed_metrics


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

