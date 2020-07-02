import os
import unittest
from os import listdir

import wfdb
from wfdb import processing
from ecgdetectors import Detectors
import numpy as np

from util.util import BEAT_CODE_DESCRIPTIONS


class TestLoadingData(unittest.TestCase):
    def setUp(self) -> None:
        self.mitdb = "/mnt/dsets/physionet/mitdb/1.0.0/"

    def test_possible_to_create_record(self):
        wfdb.io.Record(self.mitdb + '100')

    def test_read_whole_dir(self):
        with open(self.mitdb + "RECORDS", 'r') as f:
            records = list(f.readlines())
        records = [wfdb.io.Record(self.mitdb + r) for r in records]
        self.assertEqual(48, len(records))

    def test_detect(self):
        record_name = self.mitdb + "100"
        sig, fields = wfdb.rdsamp(record_name, channels=[0])
        ann_ref = wfdb.rdann(record_name, 'atr')
        xqrs = processing.XQRS(sig=sig[:, 0], fs=fields['fs'])
        xqrs.detect()

    def test_plot(self):
        record_name = self.mitdb + "100"
        sig, fields = wfdb.rdsamp(record_name, channels=[0])
        print(sig.__class__, sig)
        print(fields.__class__, fields)
        ann_ref = wfdb.rdann(record_name, 'atr')
        xqrs = processing.XQRS(sig=sig[:, 0], fs=fields['fs'])
        print(xqrs)
        xqrs.detect()
        comparitor = processing.compare_annotations(ann_ref.sample[1:],
                                                    xqrs.qrs_inds,
                                                    int(0.1 * fields['fs']),
                                                    sig[:, 0])
        comparitor.print_summary()
        comparitor.plot()

    def test_pure_prediction(self):
        record_name = self.mitdb + "100"
        sig, fields = wfdb.rdsamp(record_name, channels=[0])
        res = processing.gqrs_detect(sig, fs=fields['fs'])
        wfdb.wrann("100", 'atr', res, write_dir="data", symbol=(['N']*len(res)))
        print(res)
        self.assertIsNotNone(res)

    def test_ecg_detectors_package(self):
        for i in range(100, 300):
            try:
                record_name = self.mitdb + str(i)
                sig, fields = wfdb.rdsamp(record_name, channels=[0])
                detectors = Detectors(fields['fs'])
                r_peaks = detectors.pan_tompkins_detector(sig[:, 0])
                samples = np.array(r_peaks)
                wfdb.wrann(str(i), 'atr', sample=samples, write_dir="data/ann", symbol=(['N'] * len(r_peaks)))
                print(i)
            except Exception as e:
                print(i, e)

    def test_amount_of_data_in_mit_ar(self):
        with open(self.mitdb + "RECORDS", 'r') as f:
            records = list(f.readlines())
        annotations = [wfdb.rdann(self.mitdb + r.rstrip('\n'), extension='atr') for r in records]
        print(sum(map(lambda x: len(x.sample), annotations)))
        self.assertLess(10000, sum(map(lambda x: len(x.sample), annotations)))
        self.assertLess(100000, sum(map(lambda x: len(x.sample), annotations)))

    def test_amount_of_certain_beats_in_mit_ar(self):
        num_beats = {}
        for dirpath, subdir, filenames in os.walk("/mnt/dsets/physionet"):
            if "RECORDS" in filenames:
                with open(os.path.join(dirpath, "RECORDS"), 'r') as f:
                    records = list(f.readlines())
                    for r in records:
                        ann_file_name = os.path.join(dirpath, r.rstrip('\n'))
                        ann_sym = []
                        if os.path.exists(ann_file_name + '.atr') and os.path.isfile(ann_file_name + '.atr'):
                            ann_sym = wfdb.rdann(ann_file_name, extension='atr').symbol

                        elif os.path.exists(ann_file_name + '.qrs') and os.path.isfile(ann_file_name + '.qrs'):
                            ann_sym = wfdb.rdann(ann_file_name, extension='qrs').symbol

                        elif os.path.exists(ann_file_name + '.ecg') and os.path.isfile(ann_file_name + '.ecg'):
                            ann_sym = wfdb.rdann(ann_file_name, extension='ecg').symbol

                        elif os.path.exists(ann_file_name + '.ari') and os.path.isfile(ann_file_name + '.ari'):
                            ann_sym = wfdb.rdann(ann_file_name, extension='ari').symbol

                        for label in ann_sym:
                            num_beats.setdefault(label, 0)
                            num_beats[label] += 1

        print(num_beats)
        self.assertLess(10000, num_beats['N'])

    def save_beat_type_occurrences(self, base=None):
        if not base:
            base = {'N': 13792777, 'S': 84670, '~': 18076, '|': 72610, 'V': 140458, 'F': 3069, 'Q': 734, 'a': 558,
                    '+': 4451, 'B': 88722, 'J': 7631, 'A': 15072, '/': 98670, 'f': 1289, 'x': 7743, 'j': 334, 'L': 9616,
                    'R': 25113, '[': 6, '!': 472, ']': 6, 'E': 177, '"': 4833, 'e': 91, 's': 1334, 'T': 1476, 'n': 42,
                    'r': 489, '?': 967, None: 1946, 'p': 1032, '=': 763, 'D': 421, ')': 30345, '(': 30354, 't': 15246}
        file_content = ""
        for k in base:
            if k in BEAT_CODE_DESCRIPTIONS:
                file_content += "{} {}\n".format(k, base[k])
        with open("data/latex_data/beat-occurrences.dat", "w") as occ_file:
            occ_file.write(file_content)

    def test_save_base(self):
        self.save_beat_type_occurrences(None)


if __name__ == '__main__':
    unittest.main()
