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

