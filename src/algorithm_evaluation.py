import json
import os
from wfdb import rdann

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
    acc_metrics = [PositivePredictiveValue(), Sensitivity(), F1(), MeanSquaredError(), MeanAbsoluteError(), MeanError(),
                   DynamicThreshold(), RoCCurve()]
    for ann_file in os.listdir(alg_store.groundtruth_dir()):
        pred_ann_file = os.path.join(alg_store.prediction_dir(), ann_file.rsplit('.')[0])
        gt_ann_file = os.path.join(alg_store.groundtruth_dir(), ann_file.rsplit('.')[0])
        if os.path.exists(pred_ann_file + "." + ann_file.rsplit('.')[1]):
            for metric in acc_metrics:
                pred_ann_ref = rdann(pred_ann_file, 'atr')
                gt_ann_ref = rdann(gt_ann_file, 'atr')
                metric.match_annotations(gt_ann_ref.sample, gt_ann_ref.symbol, pred_ann_ref.sample)
        else:
            # occurs if algorithm does not output any annotation
            for metric in acc_metrics:
                pred_ann_ref_sample = [-1]
                gt_ann_ref = rdann(gt_ann_file, 'atr')
                metric.match_annotations(gt_ann_ref.sample, gt_ann_ref.symbol, pred_ann_ref_sample)

    convert_metrics_to_json(alg_store, acc_metrics)


def convert_metrics_to_json(alg_store, acc_metrics):
    json_dict = {"Name": alg_store.alg_name}
    for metric in acc_metrics:
        json_dict[metric.__abbrev__] = metric.compute()

    with open(os.path.join(alg_store.evaluation_dir(), "metrics.json"), "w") as metrics_file:
        metrics_file.write(json.dumps(json_dict))

