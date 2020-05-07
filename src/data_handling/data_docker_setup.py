import os
import shutil

import numpy as np
import wfdb

from data_handling.splice import splice_per_beat_type


class ECGData:
    __records_per_beat_type__ = 10000
    __base_data_path__ = "/mnt/dsets/physionet"
    __annotation_path__ = os.path.abspath("comparison_data/annotations")
    __signal_path__ = os.path.abspath("comparison_data/signal")

    def __init__(self, data_folder_path, ann_data_path):

        self.data_folder_path = data_folder_path
        self.ann_data_path = ann_data_path

        self.test_samples = {}
        self.test_annotations = {}
        self.test_fields = {}

    def read_all_available_data(self):
        for dirpath, subdir, filenames in os.walk(self.__base_data_path__):
            if 'mimic3wdb' in dirpath:
                continue
            if "RECORDS" in filenames:
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        ann_file_exists = os.path.exists(ann_file_name + '.atr') and os.path.isfile(
                            ann_file_name + '.atr')
                        rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        rec_file_exists = os.path.exists(ann_file_name + '.dat') and os.path.isfile(
                            ann_file_name + '.dat')
                        if ann_file_exists and rec_file_exists:
                            ann = wfdb.rdann(ann_file_name, extension='atr')

                            sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                            meta['file_name'] = r.rstrip('\n')

                            spliced_data = splice_per_beat_type(sample, ann, 7)
                            self.update_data_with_splices(spliced_data, meta)

    def update_data_with_splices(self, spliced_data, meta):
        for symbol, splices in spliced_data.items():
            for splice, rel_ann, abs_ann in splices:
                if symbol not in self.test_samples or len(self.test_samples[symbol]) < self.__records_per_beat_type__:
                    self.test_samples.setdefault(symbol, []).append(splice)
                    self.test_annotations.setdefault(symbol, []).append(rel_ann)
                    self.test_fields.setdefault(symbol, []).append(meta)

    def create_subdir_per_dataset(self):
        for key in self.test_samples.keys():
            ann_subdir_path = os.path.join(self.ann_data_path, key)
            sample_subdir_path = os.path.join(self.data_folder_path, key)
            os.makedirs(ann_subdir_path, exist_ok=True)
            os.makedirs(sample_subdir_path, exist_ok=True)

            signal_path_subdir = os.path.join(self.__signal_path__, key)
            os.makedirs(signal_path_subdir, exist_ok=True)
            os.makedirs(os.path.join(self.__annotation_path__, key), exist_ok=True)

    def setup_evaluation_data(self):
        if not os.listdir(self.__annotation_path__):
            if not self.test_samples.keys():
                self.read_all_available_data()
            self.create_subdir_per_dataset()
            for symbol, datasets in self.test_samples.items():
                print(symbol)
                for idx, samples in enumerate(datasets):
                    meta = self.test_fields[symbol][idx]
                    reshaped_data = np.array(list(map(lambda x: list(x), samples)))

                    wfdb.wrsamp(str(idx), meta['fs'], meta['units'], meta['sig_name'], reshaped_data,
                                comments=meta['comments'], base_date=meta['base_date'], base_time=meta['base_time'],
                                write_dir=os.path.join(self.__signal_path__, symbol))
                    with open(os.path.join(self.__signal_path__, symbol, "RECORDS"), 'a') as records_file:
                        records_file.writelines([str(idx) + "\n"])
                    anno = self.test_annotations[symbol][idx]

                    wfdb.wrann(str(idx), 'atr', np.array([anno]), np.array([symbol]), fs=meta['fs'],
                               write_dir=os.path.join(self.__annotation_path__, symbol))

        self.create_copy_for_algorithm()

    def create_copy_for_algorithm(self):
        self.copy_files_to_alg_folder(self.__annotation_path__, self.ann_data_path)
        self.copy_files_to_alg_folder(self.__signal_path__, self.data_folder_path)

    def copy_files_to_alg_folder(self, general_path, alg_path):
        for subdir in os.listdir(general_path):
            target_path = os.path.join(alg_path, subdir)
            shutil.rmtree(target_path, ignore_errors=True)
            shutil.copytree(os.path.join(general_path, subdir), target_path)