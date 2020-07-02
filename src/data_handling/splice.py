import os
from functools import reduce

import numpy as np
import wfdb

from util.util import BEAT_CODE_DESCRIPTIONS


def splice_per_beat_type(samples, annotations, splice_size=10):
    splices = {}
    for ann_idx, (beat, label) in enumerate(zip(annotations.sample, annotations.symbol)):
        if label not in BEAT_CODE_DESCRIPTIONS:
            continue

        splice = splice_beat(ann_idx, beat, splice_size, annotations, samples)
        splices.setdefault(label, []).append(splice)
    return splices


def splice_beat(ann_idx, beat, splice_size, annotation, samples):

    start_idx = max(ann_idx - (2 * splice_size // 3), 0)
    end_idx = min(start_idx + splice_size, len(annotation.sample) - 1)

    # split data between beats or else the algorithm gets confused - even with it gets confused
    if start_idx > 0:
        start_sample = (annotation.sample[start_idx] + annotation.sample[start_idx - 1]) // 2
    else:
        start_sample = 0
    if end_idx < len(annotation.sample) - 1:
        end_sample = (annotation.sample[end_idx] + annotation.sample[end_idx + 1]) // 2
    else:
        end_sample = len(samples)

    beat_annotations = [annotation.sample[max(ann_idx - 1, 0)] - start_sample,
                        annotation.sample[ann_idx] - start_sample,
                        annotation.sample[min(ann_idx + 1, len(annotation.sample) - 1)] - start_sample]

    splice = (samples[start_sample:end_sample], beat_annotations, beat)
    return splice


def splitup_signal_by_beat_type(samples, annotations):
    parts = {}
    for ann_idx, (beat, label) in enumerate(zip(annotations.sample, annotations.symbol)):
        if label not in BEAT_CODE_DESCRIPTIONS:
            continue
        special_beat, rel_ann = cut_out_beat_from_annotation(samples, annotations, ann_idx)
        parts.setdefault(label, []).append((special_beat, [rel_ann]))
    for label, special_beats in parts.items():
        parts[label] = reduce(join_sample_parts, special_beats)
    return parts


def cut_out_beat_from_annotation(samples, annotations, ann_idx):
    prev_beat = 0 if ann_idx == 0 else annotations.sample[ann_idx - 1]
    next_beat = len(samples) if ann_idx >= len(annotations.sample) - 1 else annotations.sample[ann_idx + 1]

    current_beat = annotations.sample[ann_idx]
    part_begin = (current_beat + prev_beat) // 2 if prev_beat != 0 else 0
    rel_ann = annotations.sample[ann_idx] - part_begin
    return cut_out_beat_at(samples, prev_beat, current_beat, next_beat), rel_ann


def cut_out_beat_at(samples, prev_beat, beat, next_beat):
    if prev_beat == 0:
        return samples[: (next_beat + beat) // 2]
    if next_beat == len(samples):
        return samples[(beat + prev_beat) // 2:]
    return samples[(beat + prev_beat) // 2: (next_beat + beat) // 2]


def join_sample_parts(sp1, sp2):
    s1, a1 = sp1
    s2, a2 = sp2
    s2 = s2 - np.mean(s2)
    concat_samples = np.concatenate((s1, s2))
    adapted_a2 = [i + len(s1) for i in a2]
    a1.extend(adapted_a2)
    return concat_samples, a1


def splitup_signal_from_file(file_path, splice_size=None):
    ann_file_name = os.path.join(file_path)
    ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(ann_file_name + '.atr')
    rec_file_name = os.path.join(file_path)
    rec_file_exists = os.path.exists(ann_file_name + '.dat') and os.path.isfile(ann_file_name + '.dat')
    if ann_file_exists and rec_file_exists:
        annotations = wfdb.rdann(ann_file_name, extension='atr')
        sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
        meta['file_name'] = file_path.rsplit(os.path.sep, 1)[1]
    else:
        return None, None, None
    if splice_size:
        return meta, splice_per_beat_type(sample, annotations, splice_size)
    else:
        return meta, splitup_signal_by_beat_type(sample, annotations)
