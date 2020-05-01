import unittest
from os import listdir

import wfdb
from wfdb import processing
from ecgdetectors import Detectors
import numpy as np


class TestLoadingData(unittest.TestCase):
    def setUp(self) -> None:
        self.mitdb = "/mnt/dsets/physionet/mitdb/1.0.0/"

    def test_possible_to_create_record(self):
        wfdb.io.Record(self.mitdb + '100')

    def test_read_whole_dir(self):
        l = listdir(self.mitdb)
        with open(self.mitdb + "RECORDS", 'r') as f:
            records = list(f.readlines())
        records = [wfdb.io.Record(self.mitdb + r) for r in records]

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


if __name__ == '__main__':
    unittest.main()
