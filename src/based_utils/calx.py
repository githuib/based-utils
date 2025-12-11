import cmath
import math
from secrets import randbelow
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def randf(exclusive_upper_bound: float = 1, precision: int = 8) -> float:
    epb = 10 ** (math.ceil(math.log10(exclusive_upper_bound)) + precision)
    return randbelow(epb) * exclusive_upper_bound / epb


def solve_quadratic(a: float, b: float, c: float) -> tuple[float, float]:
    """
    Find x where ax^2 + bx + c = 0.

    >>> solve_quadratic(20.6, -10.3, 8.7)
    (0.25, 0.25)
    >>> solve_quadratic(2.5, 25.0, 20.0)
    (-9.12310562561766, -0.8768943743823392)
    """
    r = cmath.sqrt(b**2 - 4 * a * c).real

    def root(f: int) -> float:
        return (-b + r * f) / (2 * a)

    left, right = sorted([root(-1), root(1)])
    return left, right


def mods(x: int, y: int, shift: int = 0) -> int:
    return (x - shift) % y + shift


def compare(v1: int, v2: int) -> int:
    return (v1 < v2) - (v1 > v2)


# TODO(githuib): more_itertools seems to have something similar
def frange(
    step: float, start_or_end: float = None, end: float = None
) -> Iterator[float]:
    """
    Generate a range of numbers within the given range increasing with the given step.

    :param step: difference between two successive numbers in the range
    :param start_or_end: start of range (or end of range, if end not given)
    :param end: end of range
    :return: generated numbers

    >>> " ".join(f"{n:.2f}" for n in frange(0))
    Traceback (most recent call last):
    ...
    ValueError: 0
    >>> " ".join(f"{n:.3f}" for n in frange(1))
    '0.000'
    >>> " ".join(f"{n:.3f}" for n in frange(0.125))
    '0.000 0.125 0.250 0.375 0.500 0.625 0.750 0.875'
    >>> " ".join(f"{n:.2f}" for n in frange(0.12))
    '0.00 0.12 0.24 0.36 0.48 0.60 0.72 0.84 0.96'
    >>> " ".join(f"{n:.2f}" for n in frange(0.13))
    '0.00 0.13 0.26 0.39 0.52 0.65 0.78 0.91'
    >>> " ".join(f"{n:.2f}" for n in frange(0.13, 0.51))
    '0.00 0.13 0.26 0.39'
    >>> " ".join(f"{n:.2f}" for n in frange(0.13, 0.52))
    '0.00 0.13 0.26 0.39'
    >>> " ".join(f"{n:.2f}" for n in frange(0.13, 0.53))
    '0.00 0.13 0.26 0.39 0.52'
    >>> " ".join(f"{n:.2f}" for n in frange(1.13, -3.4, 4.50))
    '-3.40 -2.27 -1.14 -0.01 1.12 2.25 3.38'
    >>> " ".join(f"{n:.2f}" for n in frange(1.13, -3.4, 4.51))
    '-3.40 -2.27 -1.14 -0.01 1.12 2.25 3.38'
    >>> " ".join(f"{n:.2f}" for n in frange(1.13, -3.4, 4.52))
    '-3.40 -2.27 -1.14 -0.01 1.12 2.25 3.38 4.51'
    """
    if not step:
        raise ValueError(step)
    s: float
    e: float
    if end is None:
        s, e = 0, start_or_end or 1
    else:
        s, e = start_or_end or 0, end

    yield s
    n = s + step
    while n < e and not math.isclose(n, e):
        yield n
        n += step


def fractions(n: int, *, inclusive: bool = False) -> Iterator[float]:
    """
    Generate a range of n fractions from 0 to 1.

    :param n: amount of numbers generated
    :param inclusive: do we want to include 0 and 1 or not?
    :return: generated numbers

    >>> " ".join(f"{n:.3f}" for n in fractions(0))
    ''
    >>> " ".join(f"{n:.3f}" for n in fractions(0, inclusive=True))
    '0.000 1.000'
    >>> " ".join(f"{n:.3f}" for n in fractions(1))
    '0.500'
    >>> " ".join(f"{n:.3f}" for n in fractions(1, inclusive=True))
    '0.000 0.500 1.000'
    >>> " ".join(f"{n:.3f}" for n in fractions(7))
    '0.125 0.250 0.375 0.500 0.625 0.750 0.875'
    >>> " ".join(f"{n:.3f}" for n in fractions(7, inclusive=True))
    '0.000 0.125 0.250 0.375 0.500 0.625 0.750 0.875 1.000'
    """
    if inclusive:
        yield 0
    end = n + 1
    for i in range(1, end):
        yield i / end
    if inclusive:
        yield 1
