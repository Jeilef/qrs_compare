from functools import reduce

import numpy as np

def splice_per_beat_type(samples, annotations, splice_size=10):
    splices = {}
    for ann_idx, (beat, label) in enumerate(zip(annotations.sample, annotations.symbol)):
        if label == 'N' or not label.isalpha():
            continue
        start_idx = max(ann_idx - (2 * splice_size // 3), 0)
        end_idx = min(start_idx + splice_size, len(annotations.sample) - 1)

        start_sample = annotations.sample[start_idx]
        end_sample = annotations.sample[end_idx]

        splices.setdefault(label, []).append((samples[start_sample:end_sample], beat - start_sample, beat))
    return splices


def splitup_signal_by_beat_type(samples, annotations):
    parts = {}
    for ann_idx, (beat, label) in enumerate(zip(annotations.sample, annotations.symbol)):
        if label == 'N' or not label.isalpha():
            continue
        special_beat, rel_ann = cut_out_beat_from_annotation(samples, annotations, beat)
        parts.setdefault(label, []).append(special_beat)
    for label, special_beats in parts.items():
        parts[label] = reduce(join_sample_parts, special_beats)
    return parts


def cut_out_beat_from_annotation(samples, annotations, ann_idx):
    prev_beat = 0 if ann_idx == 0 else annotations.sample[ann_idx - 1]
    next_beat = annotations.sample[-1] if ann_idx >= len(annotations.sample) else annotations.sample[ann_idx + 1]

    current_beat = annotations.sample[ann_idx]
    part_begin = (current_beat - prev_beat) // 2
    rel_ann = annotations.sample[ann_idx] - part_begin
    return cut_out_beat_at(samples, prev_beat, current_beat, next_beat), rel_ann


def cut_out_beat_at(samples, prev_beat, beat, next_beat):
    return samples[(beat - prev_beat) // 2: (next_beat - beat) // 2]


def join_sample_parts(sp1, sp2):
    sp2 = sp2 - np.mean(sp2)
    return np.concatenate((sp1, sp2))
