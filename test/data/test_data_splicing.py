import os
import unittest
from collections import OrderedDict

import numpy as np

import wfdb
from wfdb import processing
from matplotlib import pyplot as plt

from data_handling.splice import splice_per_beat_type, splitup_signal_by_beat_type
from util.util import get_closest


class TestManipData(unittest.TestCase):
    def setUp(self) -> None:
        samples = []
        fields = []
        annotations = []
        for dirpath, subdir, filenames in os.walk("/mnt/dsets/physionet"):
            if 'mimic3wdb' in dirpath:
                continue
            if "RECORDS" in filenames:
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(ann_file_name + '.atr')
                        rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        rec_file_exists = os.path.exists(ann_file_name + '.dat') and os.path.isfile(
                            ann_file_name + '.dat')
                        if ann_file_exists and rec_file_exists:
                            annotations.append(wfdb.rdann(ann_file_name, extension='atr'))
                            sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                            meta['file_name'] = r.rstrip('\n')
                            samples.append(sample)
                            fields.append(meta)
            print(dirpath, len(samples))

        self.samples = samples
        self.fields = fields
        self.annotations = annotations
        print("Finished Setup")

    def test_classification_metrics_match_if_spliced_gqrs(self):
        self.classification_metrics_match_if_spliced(wfdb.processing.gqrs_detect)

    def test_classification_metrics_match_if_spliced_xqrs(self):
        self.classification_metrics_match_if_spliced(wfdb.processing.xqrs_detect)

    def classification_metrics_match_if_spliced(self, algorithm):
        skew_per_record = OrderedDict()
        fail_count = 0
        for i in range(len(self.samples)):
            if i > 30:
                break
            print(i, fail_count)
            ecg_samples = self.samples[i].flatten()
            fs = self.fields[i]['fs']
            annotations = self.annotations[i]

            no_splice_pred = algorithm(ecg_samples, fs=fs)

            spliced_data = splice_per_beat_type(ecg_samples, annotations, splice_size=7)
            for label, data in spliced_data.items():
                record_name = label
                # record_name = self.fields[i]['file_name'] + '_' + label

                for samples, rel_ann, orig_ann in data:
                    splice_pred = algorithm(samples, fs=fs)
                    special_pred = get_closest(splice_pred, rel_ann)
                    regular_pred = get_closest(no_splice_pred, orig_ann)
                    self.assertEqual(orig_ann, get_closest(annotations.sample, orig_ann))
                    try:
                        skew_per_record.setdefault(record_name, []).append(special_pred - rel_ann)
                        skew_per_record.setdefault(record_name + "_org", []).append(regular_pred - orig_ann)

                        self.assertLessEqual(abs(special_pred - rel_ann), abs(regular_pred - orig_ann))
                    except AssertionError:
                        fail_count += 1
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.set_title("Distributions of predictions for different records per interval with a special beat")
        ax.boxplot(list(skew_per_record.values()), flierprops=dict(marker="."))
        ax.set_xticklabels(skew_per_record.keys(), rotation=90)
        ax.tick_params(axis='both', which='major', labelsize=6)

        plt.show()
        self.assertGreater(500, fail_count)

    def test_gqrs_diviation_for_cut_out_beats(self):
        self.diviation_for_cut_out_beats(processing.gqrs_detect)

    def test_xqrs_diviation_for_cut_out_beats(self):
        self.diviation_for_cut_out_beats(processing.xqrs_detect)

    def diviation_for_cut_out_beats(self, algorithm):
        skew_per_record = OrderedDict()
        for i in range(len(self.samples)):
            if i > 30:
                break
            ecg_samples = self.samples[i].flatten()
            fs = self.fields[i]['fs']
            annotations = self.annotations[i]

            no_splice_pred = algorithm(ecg_samples, fs=fs)
            for p in no_splice_pred:
                gt = get_closest(annotations.sample, p)
                gt_type = annotations.symbol[np.where(annotations.sample == gt)[0][0]]
                if gt_type == 'N' or not gt_type.isalpha():
                    continue
                record_name = gt_type + "_org"
                skew_per_record.setdefault(record_name, []).append(p - gt)

            typed_signal = splitup_signal_by_beat_type(ecg_samples, annotations)

            for label, (data, rel_ann) in typed_signal.items():
                record_name = label
                skew_per_record.setdefault(record_name, [])
                print("predicting on:", label, len(data))
                typed_pred = algorithm(data, fs=fs)
                for p in typed_pred:
                    skew_per_record[record_name].append(p - get_closest(rel_ann, p))

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.set_title("Distributions of predictions for different records per type of single beat")
        ax.boxplot(list(skew_per_record.values()), flierprops=dict(marker="."))
        ax.set_xticklabels(skew_per_record.keys(), rotation=90)
        ax.tick_params(axis='both', which='major', labelsize=6)
        plt.show()

