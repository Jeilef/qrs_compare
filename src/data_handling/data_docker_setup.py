import os
import shutil
import multiprocessing as mp

import numpy as np
import wfdb
from scipy import signal

from data_handling.splice import splice_per_beat_type


class ECGData:
    __records_per_beat_type__ = 10000
    __base_data_path__ = "/mnt/dsets/physionet"
    __annotation_path__ = os.path.abspath("comparison_data/annotations")
    __signal_path__ = os.path.abspath("comparison_data/signal")
    __target_frequency__ = 500  # Hz
    __splice_size__ = 10

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
                print(dirpath, subdir)
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        self.process_record(dirpath, r)

                for k in self.test_samples:
                    print(k, len(self.test_samples[k]))

    def read_ann_file(self, ann_file_name):
        if os.path.exists(ann_file_name + '.atr') and os.path.isfile(ann_file_name + '.atr'):
            return wfdb.rdann(ann_file_name, extension='atr')

        elif os.path.exists(ann_file_name + '.qrs') and os.path.isfile(ann_file_name + '.qrs'):
            return wfdb.rdann(ann_file_name, extension='qrs')

        elif os.path.exists(ann_file_name + '.ecg') and os.path.isfile(ann_file_name + '.ecg'):
            return wfdb.rdann(ann_file_name, extension='ecg')

        elif os.path.exists(ann_file_name + '.ari') and os.path.isfile(ann_file_name + '.ari'):
            return wfdb.rdann(ann_file_name, extension='ari')

    def process_record(self, dirpath, r):
        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
        ann = self.read_ann_file(ann_file_name)

        rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
        rec_file_exists = os.path.exists(ann_file_name + '.dat') and os.path.isfile(ann_file_name + '.dat')

        if ann and rec_file_exists:
            sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
            meta['file_name'] = r.rstrip('\n')
            sample, ann = self.resample_record_and_annotation(sample, ann, meta, self.__target_frequency__)

            spliced_data = splice_per_beat_type(sample, ann, self.__splice_size__)
            self.update_data_with_splices(spliced_data, meta)

    def resample_record_and_annotation(self, record, annotation, meta, target_freqency):
        sample = self.resample_record(meta, record, target_freqency)
        res_anno = self.resample_annotation(annotation, meta, target_freqency)
        return sample, res_anno

    def resample_annotation(self, annotation, meta, target_freqency):
        samples = []
        for s in annotation.sample:
            new_s = int(s * target_freqency / meta['fs'])
            samples.append(new_s)
        annotation.sample = samples
        return annotation

    def resample_record(self, meta, record, target_freqency):
        t = np.arange(record.shape[0]).astype('float64')
        new_length = int(record.shape[0] * target_freqency / meta['fs'])
        sample, sample_t = signal.resample(record, num=new_length, t=t)
        return sample

    def update_data_with_splices(self, spliced_data, meta):
        for symbol, splices in spliced_data.items():
            for splice, rel_ann, abs_ann in splices:
                if symbol not in self.test_samples or len(self.test_samples[symbol]) < self.__records_per_beat_type__:
                    self.test_samples.setdefault(symbol, []).append(splice)
                    self.test_annotations.setdefault(symbol, []).append(rel_ann)
                    self.test_fields.setdefault(symbol, []).append(meta)

    def create_subdir_per_dataset(self):
        for key in self.test_samples.keys():
            sample_subdir_path = os.path.join(self.data_folder_path, key)
            os.makedirs(self.ann_data_path, exist_ok=True)
            os.makedirs(sample_subdir_path, exist_ok=True)

            signal_path_subdir = os.path.join(self.__signal_path__, key)
            os.makedirs(signal_path_subdir, exist_ok=True)
            os.makedirs(self.__annotation_path__, exist_ok=True)

    def setup_evaluation_data(self):
        if not os.path.exists(self.__annotation_path__) or not os.listdir(self.__annotation_path__):
            if not self.test_samples.keys():
                self.read_all_available_data()
            self.create_subdir_per_dataset()
            with mp.Pool(processes=len(self.test_samples)) as pool:
                pool.starmap(self.save_typed_datasets, list(self.test_samples.items()))

        return self.__signal_path__

    def save_typed_datasets(self, symbol, datasets):
        for idx, samples in enumerate(datasets):
            anno = self.test_annotations[symbol][idx]
            meta = self.test_fields[symbol][idx]
            reshaped_data = np.array(list(map(lambda x: list(x), samples)))

            record_name = "{}_{}".format(symbol, idx)
            wfdb.wrsamp(record_name, meta['fs'], meta['units'], meta['sig_name'], reshaped_data,
                        comments=meta['comments'], base_date=meta['base_date'], base_time=meta['base_time'],
                        write_dir=os.path.join(self.__signal_path__, symbol))
            with open(os.path.join(self.__signal_path__, symbol, "RECORDS"), 'a') as records_file:
                records_file.writelines([record_name + "\n"])

            wfdb.wrann(record_name, 'atr', np.array(anno), np.array([symbol] * len(anno)), fs=meta['fs'],
                       write_dir=os.path.join(self.__annotation_path__))
