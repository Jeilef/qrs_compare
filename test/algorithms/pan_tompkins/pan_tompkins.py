import wfdb
from ecgdetectors import Detectors
import numpy as np

DATA_PATH = "/data/"
SAVE_PATH = "/data/"

with open(DATA_PATH + "RECORDS", 'r') as f:
    records = f.readlines()
    records = list(map(lambda r: r.strip("\n"), records))

for record in records:
    sig, fields = wfdb.rdsamp(DATA_PATH + record, channels=[0])
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.pan_tompkins_detector(sig[:, 0])
    samples = np.array(r_peaks)
    wfdb.wrann(record, 'atr', sample=samples, write_dir=SAVE_PATH, symbol=(['N'] * len(r_peaks)))
