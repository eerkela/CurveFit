from __future__ import annotations
from math import sqrt

import matplotlib as mpl

from . import NUMERIC


"""
TODO: Implement Sphinx documentation
"""


def color_diff(rgb1: tuple[NUMERIC, NUMERIC, NUMERIC],
               rgb2: tuple[NUMERIC, NUMERIC, NUMERIC]) -> float:
    return sqrt(sum([(v1 - v2)**2 for v1, v2 in zip(rgb1, rgb2)]))
