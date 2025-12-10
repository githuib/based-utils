from functools import cached_property
from math import isclose, log
from typing import TYPE_CHECKING

from .constants import FULL_CIRCLE

if TYPE_CHECKING:
    from collections.abc import Iterator


type _Bounds = tuple[float, float]


def trim(n: float, lower: float = 0, upper: float = 1) -> float:
    return min(max(lower, n), upper)


class _MappingBounds:
    def __init__(self, start: float = 0, end: float = 1) -> None:
        self._start = start
        self._end = end

    @cached_property
    def _span(self) -> float:
        return self._end - self._start

    def value_at(self, f: float) -> float:
        return self._start + self._span * f

    def position_of(self, n: float) -> float:
        try:
            return (n - self._start) / self._span
        except ZeroDivisionError:
            return 0.0


class LinearMapping(_MappingBounds):
    def position_of(self, n: float, *, inside: bool = False) -> float:
        f = super().position_of(n)
        return trim(f, 0.0, 1.0) if inside else f


class LogarithmicMapping(LinearMapping):
    def __init__(self, start: float = 0, end: float = 1, base: float = 10) -> None:
        super().__init__(log(start, base), log(end, base))
        self._base = base

    def value_at(self, f: float) -> float:
        return self._base ** super().value_at(f)

    def position_of(self, n: float, *, inside: bool = False) -> float:
        return super().position_of(log(n, self._base), inside=inside)


class CyclicMapping(_MappingBounds):
    def __init__(
        self, start: float = 0, end: float = FULL_CIRCLE, period: float = FULL_CIRCLE
    ) -> None:
        start, end = start % period, end % period

        # To ensure interpolation over the smallest angle,
        # phase shift {start} over whole periods, such that the
        # (absolute) difference between {start} <-> {end} <= 1/2 {period}.
        #
        #                          v------ period ------v
        #    -1                    0                    1                    2
        #     |                    |                    |     start < end:   |
        # Old:|                    |   B ~~~~~~~~~> E   |                    |
        # New:|                    |                E <~|~~ B' = B + period  |
        #     |    start > end:    |                    |                    |
        # Old:|                    |   E <~~~~~~~~~ B   |                    |
        # New:|  B - period =  B'~~|~> E                |                    |

        if abs(end - start) > period / 2:
            start += period if start < end else -period

        super().__init__(start, end)
        self._period = period

    def value_at(self, f: float) -> float:
        return super().value_at(f) % self._period

    def position_of(self, n: float) -> float:
        return super().position_of(n % self._period)


def mapped(f: float, bounds: _Bounds) -> float:
    return LinearMapping(*bounds).value_at(f)


def unmapped(n: float, bounds: _Bounds, *, inside: bool = False) -> float:
    return LinearMapping(*bounds).position_of(n, inside=inside)


def mapped_log(f: float, bounds: _Bounds, *, base: float = 10) -> float:
    return LogarithmicMapping(*bounds, base).value_at(f)


def unmapped_log(
    n: float, bounds: _Bounds, *, base: float = 10, inside: bool = False
) -> float:
    return LogarithmicMapping(*bounds, base).position_of(n, inside=inside)


def mapped_cyclic(f: float, bounds: _Bounds, *, period: float = FULL_CIRCLE) -> float:
    return CyclicMapping(*bounds, period).value_at(f)


def mapped_angle(f: float, bounds: _Bounds) -> float:
    """Shorthand for mapped_cyclic() for an angle (in radians) as period."""
    return mapped_cyclic(f, bounds, period=FULL_CIRCLE)


def unmapped_cyclic(n: float, bounds: _Bounds, *, period: float = FULL_CIRCLE) -> float:
    return CyclicMapping(*bounds, period).position_of(n)


def unmapped_angle(n: float, bounds: _Bounds) -> float:
    """Shorthand for unmapped_cyclic() for an angle (in radians) as period."""
    return unmapped_cyclic(n, bounds, period=FULL_CIRCLE)


class NumberMapping:
    def __init__(self, from_bounds: _MappingBounds, to_bounds: _MappingBounds) -> None:
        self._from_bounds = from_bounds
        self._to_bounds = to_bounds

    def map(self, n: float) -> float:
        return self._to_bounds.value_at(self._from_bounds.position_of(n))


def map_number(
    n: float, from_bounds: _MappingBounds, to_bounds: _MappingBounds
) -> float:
    return NumberMapping(from_bounds, to_bounds).map(n)


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
    while n < e and not isclose(n, e):
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
