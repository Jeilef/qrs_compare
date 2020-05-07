import wfdb
from wfdb import processing

DATA_PATH = "/data/"
SAVE_PATH = "/data/"

with open(DATA_PATH + "RECORDS", 'r') as f:
    records = f.readlines()
    records = list(map(lambda r: r.strip("\n"), records))

for record in records:
    sig, fields = wfdb.rdsamp(DATA_PATH + record, channels=[0])
    res = processing.xqrs_detect(sig[:, 0], fs=fields['fs'])
    wfdb.wrann(record, 'atr', res, write_dir=SAVE_PATH, symbol=(['N'] * len(res)))
