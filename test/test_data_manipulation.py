import os
import unittest
import numpy as np

import wfdb


class TestManipData(unittest.TestCase):
    def setUp(self) -> None:
        self.mitdb = "/mnt/dsets/physionet/mitdb/1.0.0/"

    def test_save_read_sample(self):
        record_name = self.mitdb + '100'
        sig, fields = wfdb.rdsamp(record_name, channels=[0])
        print(sig)
        sig = list(map(lambda x: list(x), list(sig)))
        sig = np.array(sig)
        wfdb.wrsamp('m_100', fields['fs'], fields['units'], fields['sig_name'], sig,
                    comments=fields['comments'], base_date=fields['base_date'],
                    base_time=fields['base_time'], write_dir='data/samples/')

    def test_save_read_record(self):
        record_name = self.mitdb + '100'
        record_read = wfdb.rdrecord(record_name, physical=False)
        record_read.wrsamp(write_dir='data/samples/', expanded=False)

    def test_manip_save_record(self):
        record_name = self.mitdb + '102'
        record_read = wfdb.rdrecord(record_name, physical=False)
        record_read.d_signal += 1
        record_read.wrsamp(write_dir='data/samples/', expanded=False)

    def test_save_annotation(self):
        wfdb.wrann("test_record_save_ann", 'atr', np.array([1]), np.array(["N"]), fs=360,
                   write_dir="data/ann")
        a = [1, 2, 4, 4, 5, 6, 7, 8, 1, 5, 3, 5, 6, 6]
        a = list(map(lambda x: list([x]), a))
        wfdb.wrsamp("test_record_save_ann", 360, ["mV"], ["I"], np.array(a, np.float64),
                    comments=None, base_date=None, base_time=None,
                    write_dir="data/ann")
        wfdb.rdann("data/ann/test_record_save_ann_fs", "atr")

    def test_fs_is_kept_when_saving(self):
        wfdb.wrann("test_record_save_ann_fs", 'atr', np.array([1]), np.array(["N"]), fs=360,
                   write_dir="data/ann")

        ann = wfdb.rdann("data/ann/test_record_save_ann_fs", "atr")
        self.assertEqual(360, ann.fs)
