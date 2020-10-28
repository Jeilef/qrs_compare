import bisect
from itertools import chain, combinations

BEAT_CODE_DESCRIPTIONS = {
    "N": "Normal beat",
    "L": "Left bundle branch block beat",
    "R": "Right bundle branch block beat",
    "B": "Bundle branch block beat (unspecified)",
    "A": "Atrial premature beat",
    "a": "Aberrated atrial premature beat",
    "J": "Nodal (junctional) premature beat",
    "S": "Supraventricular premature or ectopic beat (atrial or nodal)",
    "V": "Premature ventricular contraction",
    "r": "R-on-T premature ventricular contraction",
    "F": "Fusion of ventricular and normal beat",
    "e": "Atrial escape beat",
    "j": "Nodal (junctional) escape beat",
   "n": "Supraventricular escape beat (atrial or nodal)",
    "E": "Ventricular escape beat",
   "f": "Fusion of paced and normal beat",
    "Q": "Unclassifiable beat"
}


def get_closest(a, x):
    """
    :param a: sorted array
    :param x: value
    :return: closest value to x in a
    """
    if len(a) == 0:
        return -1
    idx = bisect.bisect_left(a, x)
    if idx == len(a):
        return a[-1]
    if idx == 0:
        return a[0]
    if abs(x - a[idx - 1]) < abs(x - a[idx]):
        return a[idx - 1]
    else:
        return a[idx]


def mapper_beat_code_to_desciption(code):
    return BEAT_CODE_DESCRIPTIONS[code]


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
