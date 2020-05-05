import bisect


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
