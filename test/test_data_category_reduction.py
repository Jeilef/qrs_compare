import os
import unittest
from os import listdir
from matplotlib import pyplot as plt, cm
import wfdb
from wfdb import processing
from ecgdetectors import Detectors
import numpy as np
from scipy import signal
from sklearn import decomposition

from data_handling.splice import splice_beat
from util.util import BEAT_CODE_DESCRIPTIONS


class TestLoadingData(unittest.TestCase):
    sample_freq = 250

    def test_curve_shapes_of_beats(self):
        beat_samples = {}
        for dirpath, subdir, filenames in os.walk("/mnt/dsets/physionet"):
            if "mimic" in dirpath:
                continue
            if len(beat_samples) >= len(BEAT_CODE_DESCRIPTIONS):
                break
            else:
                print(dirpath, len(beat_samples))
            if "RECORDS" in filenames:
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))

                        ann_sym = self.read_ann_file(ann_file_name)
                        if not ann_sym:
                            continue

                        for ann_idx, (label, beat) in enumerate(zip(ann_sym.symbol, ann_sym.sample)):
                            if label not in beat_samples and label in BEAT_CODE_DESCRIPTIONS:
                                sample, meta = wfdb.rdsamp(ann_file_name)
                                beat_samples[label] = (splice_beat(ann_idx, beat, 0, ann_sym, sample)[0], meta)

        for beat_type, beat_sample in beat_samples.items():
            print(beat_sample[0])
            print(beat_sample[1])
            plt.plot(beat_sample[0])
            plt.title(beat_type)
            plt.show()

    def test_correlate_beat_type(self):
        __num_samples__ = 100
        beat_samples = self.read_data_per_type(__num_samples__)
        del beat_samples["Q"]
        del beat_samples["r"]

        typed_uniform_beats, uniform_beats = self.equalize_length(beat_samples)

        pca = decomposition.PCA(n_components=2)
        uniform_beats = np.nan_to_num(uniform_beats)
        pca.fit(uniform_beats)
        colors = cm.rainbow(np.linspace(0, 1, len(typed_uniform_beats)))
        for (label, samples), c in zip(typed_uniform_beats.items(), colors):
            transf_samples = pca.transform(np.nan_to_num(samples))
            x = []
            y = []
            for s in transf_samples:
                x.append(s[0])
                y.append(s[1])
            plt.scatter(x, y, alpha=0.3, label=label, color=c)
        plt.title("Beat types")
        plt.legend(loc="right")
        plt.show()

    def test_compute_representative_beat(self):
        __num_samples__ = 5000
        beat_samples = self.read_data_per_type(__num_samples__)

        typed_uniform_beats, uniform_beats = self.equalize_length(beat_samples)

        typed_mean_beat = {}
        for label, beats in typed_uniform_beats.items():
            print("saving", label)
            beats = np.nan_to_num(beats)
            beat = np.mean(beats, axis=0)
            beat_plus = np.mean(beats, axis=0) + np.std(beats, axis=0)
            beat_minus = np.mean(beats, axis=0) - np.std(beats, axis=0)
            new_beat = []
            if label == label.lower():
                label += "-lower"
            self.save_average_beat(beat, label, new_beat)
            self.save_average_beat(beat_plus, label + "-plus-std", [])
            self.save_average_beat(beat_minus, label + "-minus-std", [])
            typed_mean_beat[label] = beat
            plt.plot(new_beat)
            plt.title(label + " mean beat")
            #plt.show()

    def save_average_beat(self, beat, label, new_beat):
        with open("data/latex_data/average-beats/average-beat-{}.dat".format(label), "w") as beat_file:
            beat_data = ""
            prev_also_zero = False
            for idx, point in enumerate(beat):
                if np.isclose(point, 0, 0.01):
                    if prev_also_zero or idx == 0:
                        prev_also_zero = True
                        continue
                    prev_also_zero = True
                else:
                    prev_also_zero = False
                beat_data += "{} {}\n".format(idx, point)
                new_beat.append(point)
            beat_file.write(beat_data)

    def equalize_length(self, beat_samples):
        uniform_beats = []
        typed_uniform_beats = {}
        for label, beat_sample in beat_samples.items():
            typed_uniform_beats[label] = []
            for sample, anno in beat_sample:
                if anno < self.sample_freq:
                    start_zeros = np.zeros((int(self.sample_freq - anno), 1), dtype=np.float64)
                    sample = np.concatenate([start_zeros, sample])
                else:
                    sample = sample[anno - self.sample_freq:]
                if len(sample) < 2 * self.sample_freq:
                    end_zeros = np.zeros((int(2 * self.sample_freq - len(sample)), 1), dtype=np.float64)
                    sample = np.concatenate([sample, end_zeros])
                else:
                    sample = sample[:2 * self.sample_freq]
                reshaped_sample = np.reshape(sample, newshape=(-1,))
                uniform_beats.append(reshaped_sample)
                typed_uniform_beats[label].append(reshaped_sample)
        return typed_uniform_beats, uniform_beats

    def read_data_per_type(self, __num_samples__):
        beat_samples = {}
        for dirpath, subdir, filenames in os.walk("/mnt/dsets/physionet"):
            if "mimic" in dirpath:
                continue
            if len(beat_samples) >= len(BEAT_CODE_DESCRIPTIONS):
                break
            else:
                print(dirpath, len(beat_samples))
            if "RECORDS" in filenames:
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        ann_sym = self.read_ann_file(ann_file_name)
                        if not ann_sym:
                            continue

                        for ann_idx, (label, beat) in enumerate(zip(ann_sym.symbol, ann_sym.sample)):
                            too_few_beats_for_label = \
                                (label not in beat_samples or len(beat_samples[label]) < __num_samples__)
                            if too_few_beats_for_label and label in BEAT_CODE_DESCRIPTIONS:
                                sample, meta = wfdb.rdsamp(ann_file_name, channels=[0])

                                beat_samples.setdefault(label, [])
                                splice = splice_beat(ann_idx, beat, 0, ann_sym, sample)

                                t = np.arange(splice[0].shape[0]).astype('float64')
                                new_length = int(splice[0].shape[0] * self.sample_freq / meta['fs'])
                                sample, sample_t = signal.resample(splice[0], num=new_length, t=t)
                                res_anno = int(splice[1][1] * self.sample_freq / meta['fs'])
                                beat_samples[label].append((sample, res_anno))
        return beat_samples

    def read_ann_file(self, ann_file_name):
        if os.path.exists(ann_file_name + '.atr') and os.path.isfile(ann_file_name + '.atr'):
            return wfdb.rdann(ann_file_name, extension='atr')

        elif os.path.exists(ann_file_name + '.qrs') and os.path.isfile(ann_file_name + '.qrs'):
            return wfdb.rdann(ann_file_name, extension='qrs')

        elif os.path.exists(ann_file_name + '.ecg') and os.path.isfile(ann_file_name + '.ecg'):
            return wfdb.rdann(ann_file_name, extension='ecg')

        elif os.path.exists(ann_file_name + '.ari') and os.path.isfile(ann_file_name + '.ari'):
            return wfdb.rdann(ann_file_name, extension='ari')
