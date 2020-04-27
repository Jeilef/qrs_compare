import json
import os
from wfdb import rdann

from metric import PositivePredictiveValue, Sensitivity


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
    min_tp, max_fp, max_fn = 100, 100, 100
    for ann_file in os.listdir(alg_store.groundtruth_dir()):
        pred_ann_file = os.path.join(alg_store.prediction_dir(), ann_file.rsplit('.')[0])
        gt_ann_file = os.path.join(alg_store.groundtruth_dir(), ann_file.rsplit('.')[0])
        if os.path.exists(pred_ann_file + "." + ann_file.rsplit('.')[1]):
            pred_ann_ref = rdann(pred_ann_file, 'atr')
            gt_ann_ref = rdann(gt_ann_file, 'atr')
            tp, fp, tn = compare_annotations(gt_ann_ref, pred_ann_ref)
            min_tp = min(min_tp, tp)
            max_fp = max(max_fp, fp)
            max_fn = max(max_fn, tn)

    with open(os.path.join(alg_store.evaluation_dir(), "metrics.json"), "w") as metrics_file:
        metrics_file.write(json.dumps({"name": alg_store.alg_name, "tp": min_tp, "fp": max_fp, "fn": max_fn}))


def compare_annotations(gt_annotations, pred_annotations):
    gt_samples = gt_annotations.sample
    pred_samples = pred_annotations.sample
    ppv = PositivePredictiveValue().match_annotations(gt_samples, gt_annotations.symbol, pred_samples, 36)
    sens = Sensitivity().match_annotations(gt_samples, gt_annotations.symbol, pred_samples, 36)
    print(ppv, sens)
    return ppv, sens, 0
