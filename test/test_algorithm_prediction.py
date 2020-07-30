import os
import sys
sys.path.append('../src')
import unittest
import re

import wfdb

from util.easy_algorithm_execution import algs_with_name
import matplotlib.pyplot as plt


def generate_predictions_with_dirs(base_save_path, comp_data_path="../comparison_data_noise/"):
    p = re.compile('.*[a-zA-Z]_[0-9].[0-9]+[a-zA-Z_]*_[0-9]+.*')
    for dirpath, subdir, filenames in os.walk(comp_data_path + "signal"):
        if p.match(dirpath) and "RECORDS" in filenames:
            with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                records = list(f.readlines())
            for r in records:
                ann_file_name = os.path.join(comp_data_path + "annotations", r.rstrip('\n'))
                ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(
                    ann_file_name + '.atr')
                rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                rec_file_exists = os.path.exists(rec_file_name + '.dat') and os.path.isfile(
                    rec_file_name + '.dat')
                if ann_file_exists and rec_file_exists:
                    splice_size = int(r.split("_")[-2])

                    sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                    rec_name = rec_file_name.split(os.sep)[-1]

                    # 150 is a restriction for some qrs detectors
                    if len(sample) > 150:
                        for alg_name, alg_func in algs_with_name().items():
                            save_path = base_save_path + alg_name
                            os.makedirs(save_path, exist_ok=True)
                            alg_func(meta, rec_name, save_path, sample)

class TestAlgorithmPrediction(unittest.TestCase):
    def test_generate_predictions(self) -> None:
        generate_predictions_with_dirs("data/algorithm_prediction/", "../comparison_data/")

    def test_generate_predictions_noise(self) -> None:
        generate_predictions_with_dirs("data/algorithm_prediction_noise/", "../comparison_data_noise/")



    def test_correct_base_data(self):
        comp_data_path = "../comparison_data/"
        self.beats_per_splice_size = {}

        p = re.compile('.*[a-zA-Z]_[0-9].[0-9]_[0-9]+.*')
        for dirpath, subdir, filenames in os.walk(comp_data_path + "signal"):
            if p.match(dirpath):
                if "RECORDS" in filenames:
                    with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                        records = list(f.readlines())
                        for r in records:
                            splice_size = int(r.split("_")[-2])

                            ann_file_name = os.path.join(comp_data_path + "annotations", r.rstrip('\n'))
                            ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(
                                ann_file_name + '.atr')
                            rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                            rec_file_exists = os.path.exists(rec_file_name + '.dat') and os.path.isfile(
                                rec_file_name + '.dat')
                            if ann_file_exists and rec_file_exists:
                                sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                                plt.plot(sample)
                                plt.show()
                                return


if __name__ == "__main__":
    generate_predictions_with_dirs("data/algorithm_prediction/", "../comparison_data/")
