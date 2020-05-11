import wfdb
from wfdb import processing
import numpy as np

DATA_PATH = "/data/"
SAVE_PATH = "/pred/"

with open(DATA_PATH + "RECORDS", 'r') as f:
    records = f.readlines()
    records = list(map(lambda r: r.strip("\n"), records))

for record in records:
    sig, fields = wfdb.rdsamp(DATA_PATH + record, channels=[0])
    res = processing.gqrs_detect(sig[:, 0], fs=fields['fs'])
    if len(res) > 0:
        wfdb.wrann(record, 'atr', res, write_dir=SAVE_PATH, symbol=(['N'] * len(res)))
