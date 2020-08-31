import math
import os
import multiprocessing as mp

import numpy as np
import wfdb
from scipy import signal

from data_handling.signal_to_noise_ratio_helper import repeat_signal
from data_handling.splice import splice_per_beat_type
from util.util import powerset


class ECGData:
    __records_per_beat_type__ = 10000
    __base_data_path__ = "/mnt/dsets/physionet"
    __noise_path__ = __base_data_path__ + "/nstdb/1.0.0/"
    __annotation_path__ = os.path.abspath("comparison_data/annotations")
    __signal_path__ = os.path.abspath("comparison_data/signal")
    __target_frequency__ = 500  # Hz
    __splice_size_start__ = 3
    __splice_size_end__ = 11
    __splice_size_step_size__ = 2
    __stepping_beat_position__ = False
    __num_noises__ = 3

    def __init__(self, data_folder_path=__signal_path__, ann_data_path=__annotation_path__,
                 min_noise=0, max_noise=2, num_noise=5):

        self.data_folder_path = data_folder_path
        self.ann_data_path = ann_data_path

        self.test_samples = {}
        self.test_annotations = {}
        self.test_fields = {}

        self.baseline_wander_noise = []
        self.electrode_movement_noise = []
        self.muscle_artifact_noise = []
        self.powerline_noise = []
        self.last_noise_idx = 0

        self.collected_data = {}
        self.last_written_idx = {}

        self.read_noise_data()
        self.min_noise = min_noise
        self.max_noise = max_noise
        self.num_noise = num_noise
        self.failed_writes = {}

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

                print(self.collected_data)
        self.summarize_data_of_underrepresented_types()

    def summarize_data_of_underrepresented_types(self):
        type_mapping = {'R': ['E', 'j', 'F'],
                        'L': ['J', 'e'],
                        'N': ['a']}
        useless_keys = []
        possible_keys = list(self.test_samples.keys())
        for summ, maps in type_mapping.items():
            for m in maps:
                for k in possible_keys:
                    if k[0] == m:
                        summ_ad = summ + k[1:]
                        useless_keys.append((summ_ad, k))

        for summ_ad, k in useless_keys:
            self.test_samples.setdefault(summ_ad, []).extend(self.test_samples[k])
            self.test_annotations.setdefault(summ_ad, []).extend(self.test_annotations[k])
            self.test_fields.setdefault(summ_ad, []).extend(self.test_fields[k])
            del self.test_samples[k]
            del self.test_annotations[k]
            del self.test_fields[k]

    def read_data_for_single_type(self, beat_type):
        for dirpath, subdir, filenames in os.walk(self.__base_data_path__):
            if 'mimic3wdb' in dirpath:
                continue
            if "RECORDS" in filenames:
                print(dirpath, subdir)
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        self.process_record(dirpath, r)
                        for k in self.collected_data:
                            if beat_type == k[0] and k in self.collected_data:
                                if list(self.collected_data[k].values())[0] >= self.__records_per_beat_type__:
                                    print(self.collected_data)
                                    print(self.last_written_idx)
                                    return

                for k in self.collected_data:
                    print(k, self.collected_data[k])

    def read_noise_data(self):
        self.muscle_artifact_noise, ma_meta = wfdb.rdsamp(self.__noise_path__ + "ma", channels=[0])
        self.baseline_wander_noise, bs_meta = wfdb.rdsamp(self.__noise_path__ + "bw", channels=[0])
        self.electrode_movement_noise, em_meta = wfdb.rdsamp(self.__noise_path__ + "em", channels=[0])

        self.muscle_artifact_noise = self.resample_record(ma_meta, self.muscle_artifact_noise,
                                                          self.__target_frequency__)
        self.baseline_wander_noise = self.resample_record(bs_meta, self.baseline_wander_noise,
                                                          self.__target_frequency__)
        self.electrode_movement_noise = self.resample_record(em_meta, self.electrode_movement_noise,
                                                             self.__target_frequency__)

        self.powerline_noise = self.create_powerline_noise()
        max_len = max(len(self.muscle_artifact_noise), len(self.baseline_wander_noise),
                      len(self.electrode_movement_noise), len(self.powerline_noise))

        self.muscle_artifact_noise = np.array(repeat_signal(self.muscle_artifact_noise, max_len))
        self.baseline_wander_noise = np.array(repeat_signal(self.baseline_wander_noise, max_len))
        self.electrode_movement_noise = np.array(repeat_signal(self.electrode_movement_noise, max_len))
        self.powerline_noise = np.array(repeat_signal(self.powerline_noise, max_len))

    def create_powerline_noise(self):
        signal_frequency = 50
        offset = 0.1
        noise_length = 20  # seconds

        x = np.linspace(0, noise_length, noise_length * self.__target_frequency__)
        y = np.sin(2 * math.pi * signal_frequency * x + offset)
        y = np.reshape(y, (noise_length * self.__target_frequency__, 1))
        return y

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
        print("processed", dirpath, r)
        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
        ann = self.read_ann_file(ann_file_name)

        rec_file_name = os.path.join(dirpath, r.rstrip('\n'))
        rec_file_exists = os.path.exists(ann_file_name + '.dat') and os.path.isfile(ann_file_name + '.dat')

        if ann and rec_file_exists:
            try:
                sample, meta = wfdb.rdsamp(rec_file_name, channels=[0])
                meta['file_name'] = r.rstrip('\n')
                sample, ann = self.resample_record_and_annotation(sample, ann, meta, self.__target_frequency__)

                for splice_size in range(self.__splice_size_start__, self.__splice_size_end__, self.__splice_size_step_size__):
                    if self.__stepping_beat_position__:
                        for i in np.linspace(0.2, 1, 5):
                            spliced_data = splice_per_beat_type(sample, ann, splice_size, i)
                            self.update_data_with_splices(spliced_data, meta, splice_size, i)
                    else:
                        spliced_data = splice_per_beat_type(sample, ann, splice_size)
                        self.update_data_with_splices(spliced_data, meta, splice_size)
            except ValueError as v:
                print("Could not parse", rec_file_name, "because", str(v))
            self.save_and_reset_created_beats()

    def save_and_reset_created_beats(self):
        self.summarize_data_of_underrepresented_types()
        for k in self.test_samples:
            if len(self.test_samples[k]) > 0:
                self.save_beat_type(k)
        del self.test_samples
        del self.test_fields
        del self.test_annotations
        self.test_samples = {}
        self.test_fields = {}
        self.test_annotations = {}

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

    def update_data_with_splices(self, spliced_data, meta, splice_size, beat_pos=0.5):
        for symbol, splices in spliced_data.items():
            for splice, rel_ann, abs_ann in splices:
                if symbol not in self.collected_data or splice_size not in self.collected_data[symbol] or \
                        self.collected_data[symbol][splice_size] < self.__records_per_beat_type__:
                    adapted_symbols, adapted_splices = self.create_all_noise_versions(splice, symbol)
                    self.collected_data.setdefault(symbol, {}).setdefault(splice_size, 0)
                    self.collected_data[symbol][splice_size] += 1
                    self.process_adapted_splices(adapted_splices, adapted_symbols, meta, rel_ann, splice_size, beat_pos)

    def process_adapted_splices(self, adapted_splices, adapted_symbols, meta, rel_ann, splice_size, beat_pos):
        for sym, spli in zip(adapted_symbols, adapted_splices):
            sym += "_" + str(beat_pos) + "_" + str(splice_size)
            self.test_samples.setdefault(sym, []).append(spli)
            self.test_annotations.setdefault(sym, []).append(rel_ann)
            self.test_fields.setdefault(sym, []).append(meta)

    def create_all_noise_versions(self, splice, symbol):
        symbols = []
        splices = []
        noise_data = self.get_noise_samples(len(splice))
        noise_names = ["em", "ma", "bw"]
        ps = list(powerset(range(len(noise_data))))
        for scaling_factor in np.linspace(self.min_noise, self.max_noise, self.num_noise):
            for n_idx, noises in enumerate(ps):
                if scaling_factor == 0 and n_idx > 0:
                    continue
                current_splice = splice.astype("float64")
                splice_symbol = "{}_{}".format(symbol, scaling_factor)
                for noise_idx in noises:
                    scaled_noise = self.scale_noise(noise_data, noise_idx, scaling_factor, splice)
                    current_splice += scaled_noise.astype("float64")
                    splice_symbol += "_" + noise_names[noise_idx]
                symbols.append(splice_symbol)
                splices.append(current_splice)
        return symbols, splices

    def scale_noise(self, noise_data, noise_idx, scaling_factor, splice):
        scaled_noise = np.multiply(noise_data[noise_idx], scaling_factor).reshape(splice.shape)
        return scaled_noise

    def get_noise_samples(self, duration, num_noises=__num_noises__):
        if self.last_noise_idx + duration < len(self.electrode_movement_noise):
            noise_data = [self.electrode_movement_noise[self.last_noise_idx: self.last_noise_idx + duration],
                          self.muscle_artifact_noise[self.last_noise_idx: self.last_noise_idx + duration],
                          self.baseline_wander_noise[self.last_noise_idx: self.last_noise_idx + duration]
                          ]
            self.last_noise_idx = self.last_noise_idx + duration
        else:
            overhang = self.last_noise_idx + duration - len(self.electrode_movement_noise)
            noise_data = [np.concatenate([self.electrode_movement_noise[self.last_noise_idx:],
                                          self.electrode_movement_noise[:overhang]]),
                          np.concatenate([self.muscle_artifact_noise[self.last_noise_idx:],
                                          self.muscle_artifact_noise[:overhang]]),
                          np.concatenate([self.baseline_wander_noise[self.last_noise_idx:],
                                          self.baseline_wander_noise[:overhang]])
                          ]
            self.last_noise_idx = overhang
        return noise_data[:num_noises]

    def create_subdir_per_dataset(self):
        for key in self.test_samples.keys():
            self.create_subdir_for_beat_type(key)

    def create_subdir_for_beat_type(self, key):
        sample_subdir_path = os.path.join(self.data_folder_path, key)
        os.makedirs(self.ann_data_path, exist_ok=True)
        os.makedirs(sample_subdir_path, exist_ok=True)
        signal_path_subdir = os.path.join(self.__signal_path__, key)
        os.makedirs(signal_path_subdir, exist_ok=True)
        os.makedirs(self.__annotation_path__, exist_ok=True)

    def setup_evaluation_data(self):
        if not os.path.exists(self.ann_data_path) or not os.listdir(self.ann_data_path):
            if not self.test_samples.keys():
                self.read_all_available_data()
            self.create_subdir_per_dataset()
            for beat_type, datasets in self.test_samples.items():
                self.save_typed_datasets(beat_type, datasets)
            print("failed: ", self.failed_writes)
        return self.data_folder_path

    def save_beat_type(self, beat_type):
        self.create_subdir_for_beat_type(beat_type)
        self.save_typed_datasets(beat_type, self.test_samples[beat_type])

    def save_typed_datasets(self, symbol, datasets):
        for idx, samples in enumerate(datasets):
            anno = self.test_annotations[symbol][idx]
            meta = self.test_fields[symbol][idx]

            self.last_written_idx.setdefault(symbol, 0)
            corrected_idx = self.last_written_idx[symbol] + idx
            record_name = "{}_{}".format(symbol.replace(".", "-"), corrected_idx)
            try:
                reshaped_data = np.reshape(samples, (-1, 1)).astype(np.float64)
                max_min = max(np.max(reshaped_data), abs(np.min(reshaped_data)))
                if max_min != 0:
                    reshaped_data = reshaped_data / max_min
                np.nan_to_num(reshaped_data)
                sig_names = [sn.replace(" ", "") for sn in meta['sig_name']]
                wfdb.wrsamp(record_name, self.__target_frequency__, meta['units'], sig_names,
                            p_signal=reshaped_data, fmt=["32"],
                            comments=meta['comments'], base_date=meta['base_date'], base_time=meta['base_time'],
                            write_dir=os.path.join(self.data_folder_path, symbol))

                wfdb.wrann(record_name, 'atr', np.array(anno), np.array([symbol[0]] * len(anno)),
                           fs=self.__target_frequency__, write_dir=os.path.join(self.ann_data_path))
                with open(os.path.join(self.data_folder_path, symbol, "RECORDS"), 'a') as records_file:
                    records_file.writelines([record_name + "\n"])

            except ValueError as v:
                print("Failed to write", record_name, "because", str(v))
                self.clean_up_wrong_writes(symbol, record_name)
                print(symbol[0], int(symbol.split("_")[-1]))
                self.collected_data[symbol[0]][int(symbol.split("_")[-1])] -= 1
                self.failed_writes.setdefault(symbol, 0)
                self.failed_writes[symbol] += 1

        self.last_written_idx[symbol] += len(datasets)

    def clean_up_wrong_writes(self, symbol, record_name):
        try:
            os.remove(os.path.join(self.data_folder_path, symbol, record_name + ".dat"))
            os.remove(os.path.join(self.data_folder_path, symbol, record_name + ".hea"))
        except OSError:
            pass
        try:
            os.remove(os.path.join(self.ann_data_path, record_name + ".atr"))
        except OSError:
            pass

    def save_log(self, meta, record_name, reshaped_data):
        with open("save_file_" + record_name + ".log", "w") as save_file:
            s = ""
            for x in reshaped_data:
                s += str(x[0]) + ","
            save_file.write(s[:-1])
        with open("meta_log_" + record_name + ".log", "w") as meta_log:
            s = ""
            for k, v in meta.items():
                s += "{},{}\n".format(k, v)
            meta_log.write(s)
        print("saved error")
