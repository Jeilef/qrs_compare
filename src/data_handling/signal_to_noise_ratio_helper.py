import math
import numpy as np


def transform_signals_to_msa(signals, msa):
    """
    :param signals: an array of signals, e.q. noise
    :param msa: mean squared amplitude that is to be returned
    :return: a combined signal with the mean squared amplitude of msa
    """
    # if n signals are combined, each has to have a level of 1/n after squaring
    individual_level = math.sqrt(msa/len(signals))

    signal_levels = list(map(lambda s: np.mean(np.square(s)), signals))
    max_len = len(max(signals, key=lambda s: len(s)))
    modified_signals = []
    for sig_idx, sig in enumerate(signals):
        modified_signals.append(repeat_signal(sig, max_len)/math.sqrt(signal_levels[sig_idx]) * individual_level)
    return sum(modified_signals)


def repeat_signal(signal, target_len):
    if len(signal) >= target_len:
        return signal[:target_len]
    extended_signal = []
    while len(extended_signal) < target_len:
        extended_signal.extend(signal)
    return extended_signal[:target_len]
