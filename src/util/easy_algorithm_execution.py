import wfdb
from ecgdetectors import Detectors
import numpy as np
from wfdb import processing


def algs_with_name():
    return {"christov": christov_single,
            "engelze-zeelenberg": engelze_zeelenberg_single,
            "hamilton": hamilton_single,
            "two-moving-average": two_moving_average_single,
            "pan-tompkins": pan_tompkins_single,
            "gqrs": gqrs_single,
            "xqrs": xqrs_single,
            "stationary-wavelet-transform": stationary_wavelet_transform_single}


def christov(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        christov_single(fields, record, save_path, sig)


def christov_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.christov_detector(sig[:, 0])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks


def engelze_zeelenberg(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        engelze_zeelenberg_single(fields, record, save_path, sig)


def engelze_zeelenberg_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    try:
        r_peaks = detectors.engzee_detector(sig[:, 0])
    except Exception:
        r_peaks = [0]
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks

def hamilton(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        hamilton_single(fields, record, save_path, sig)


def hamilton_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.hamilton_detector(sig[:, 0])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks

def pan_tompkins(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        pan_tompkins_single(fields, record, save_path, sig)


def pan_tompkins_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.pan_tompkins_detector(sig[:, 0])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks

def stationary_wavelet_transform(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        stationary_wavelet_transform_single(fields, record, save_path, sig)


def stationary_wavelet_transform_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.swt_detector(sig[:, 0])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks

def two_moving_average(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        two_moving_average_single(fields, record, save_path, sig)


def two_moving_average_single(fields, record, save_path, sig, save=True):
    detectors = Detectors(fields['fs'])
    r_peaks = detectors.two_average_detector(sig[:, 0])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks


def gqrs(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        gqrs_single(fields, record, save_path, sig)


def gqrs_single(fields, record, save_path, sig, save=True):
    r_peaks = processing.gqrs_detect(sig[:, 0], fs=fields['fs'])
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks


def xqrs(data_path, save_path):
    records = read_records(data_path)

    for record in records:
        sig, fields = wfdb.rdsamp(data_path + record, channels=[0])
        xqrs_single(fields, record, save_path, sig)


def xqrs_single(fields, record, save_path, sig, save=True):
    r_peaks = processing.xqrs_detect(sig[:, 0], fs=fields['fs'], verbose=False)
    if save:
        save_prediction(r_peaks, record, save_path)
    else:
        return r_peaks


def save_prediction(r_peaks, record, save_path):
    if len(r_peaks) > 0:
        samples = np.array(r_peaks)
        wfdb.wrann(record, 'atr', sample=samples, write_dir=save_path, symbol=(['N'] * len(r_peaks)))


def read_records(data_path):
    with open(data_path + "RECORDS", 'r') as f:
        records = f.readlines()
        records = list(map(lambda r: r.strip("\n"), records))
    return records
