import os
import unittest
import bisect

import wfdb
from wfdb import processing
from matplotlib import pyplot as plt

from data_handling.splice import splice_per_beat_type
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
            print(dirpath)

        self.samples = samples
        self.fields = fields
        self.annotations = annotations
        print("Finished Setup")

    def test_classification_metrics_match_if_spliced_gqrs(self):
        self.classification_metrics_match_if_spliced(wfdb.processing.gqrs_detect)

    def test_classification_metrics_match_if_spliced_xqrs(self):
        self.classification_metrics_match_if_spliced(wfdb.processing.xqrs_detect)

    def classification_metrics_match_if_spliced(self, algorithm):
        skew_per_record = {}
        fail_count = 0
        for i in range(len(self.samples)):

            print(i, fail_count)
            # TODO: remove
            if i > 20:
                continue
            ecg_samples = self.samples[i].flatten()
            fs = self.fields[i]['fs']
            annotations = self.annotations[i]

            no_splice_pred = algorithm(ecg_samples, fs=fs)

            spliced_data = splice_per_beat_type(ecg_samples, annotations, splice_size=7)
            for label, data in spliced_data.items():
                record_name = self.fields[i]['file_name'] + '_' + label
                skew_per_record.setdefault(record_name, [])
                for samples, rel_ann, orig_ann in data:
                    splice_pred = algorithm(samples, fs=fs)
                    special_pred = get_closest(splice_pred, rel_ann)
                    regular_pred = get_closest(no_splice_pred, orig_ann)
                    self.assertEqual(orig_ann, get_closest(annotations.sample, orig_ann))
                    try:
                        skew_per_record[record_name].append((special_pred - rel_ann) - (regular_pred - orig_ann))
                        self.assertLessEqual(abs(special_pred - rel_ann), abs(regular_pred - orig_ann))
                    except AssertionError:
                        fail_count += 1
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.set_title("Distributions of predictions for different records")
        ax.boxplot(list(skew_per_record.values()), flierprops=dict(marker="."))
        ax.set_xticklabels(skew_per_record.keys(), rotation=90)
        ax.tick_params(axis='both', which='major', labelsize=6)

        plt.show()
        self.assertGreater(500, fail_count)
