import os
from wfdb import rdann


def evaluate_algorithm(alg_name):
    gt_data_path = os.path.join("algorithms", alg_name, "data", "gt")
    pred_data_path = os.path.join("algorithms", alg_name, "data", "pred")
    for ann_file in os.listdir(gt_data_path):
        pred_ann_file = os.path.join(pred_data_path, ann_file.rsplit('.')[0])
        gt_ann_file = os.path.join(gt_data_path, ann_file.rsplit('.')[0])
        if os.path.exists(pred_ann_file):
            pred_ann_ref = rdann(pred_ann_file, 'atr')
            gt_ann_ref = rdann(gt_ann_file, 'atr')
            compare_annotations(gt_ann_ref, pred_ann_ref)


def compare_annotations(gt_annotations, pred_annotations):
    print(dir(gt_annotations))
    gt_samples = gt_annotations.sample
    pred_samples = pred_annotations.sample
    print(match_annotations(gt_samples, gt_annotations.symbol, pred_samples, 36))


def match_annotations(true_samples, true_symbols, test_samples, tolerance):
    """Tries to match two lists of (supposed) QRS positions.

    Args:
        true_samples: List of samples representing the actual QRS positions.
        true_symbols: Annotation symbols for the samples in true_samples.
        test_samples: List of samples representing the detected QRS positions.
        tolerance: Maximum allowed distance between actual and detected QRS
            position.

    Returns:
        Tuple (tp, fp, fn) whereas tp is a list of true positives characterized
        as tripel (true_sample, test_sample, symbol), fp is a list of false
        positives characterized as tuple (test_sample, symbol?), and fn is a
        list of false negatives characterized as list of tuples (true_sample,
        symbol).
    """

    tp, fp, fn = [], [], []

    for true_sample, true_symbol in zip(true_samples, true_symbols):
        matches = [test_sample
                   for test_sample in test_samples
                   if abs(test_sample - true_sample) <= tolerance]
        matches.sort(key=lambda m: abs(m - true_sample))
        if len(matches) == 0:
            fn.append((true_sample, true_symbol))
        if len(matches) > 0:
            tp.append((true_sample, matches[0], true_symbol))
        if len(matches) > 1:
            fp.extend([(match, true_symbol) for match in matches[1:]])

    for test_sample in test_samples:
        matches = [true_sample
                   for true_sample in true_samples
                   if abs(true_sample - test_sample) <= tolerance]
        if len(matches) == 0:
            fp.append((test_sample, ''))

    return tp, fp, fn
