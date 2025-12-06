import re
import unicodedata
from typing import TYPE_CHECKING

from more_itertools import transpose

from based_utils.data.iterators import equalized

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

PRE_a = ord("a") - 1
PRE_A = ord("A") - 1

_ansi_regex = re.compile(r"\x1b\[\d+(;\d+)*m")


def strip_ansi(s: str) -> str:
    return _ansi_regex.sub("", s)


def strlen(s: str) -> int:
    return sum(
        (2 if unicodedata.east_asian_width(c) == "W" else 1) for c in strip_ansi(s)
    )


def align_left(s: str, width: int, *, fill_char: str = " ") -> str:
    return s + fill_char * max(width - strlen(s), 0)


def align_right(s: str, width: int, *, fill_char: str = " ") -> str:
    return fill_char * max(width - strlen(s), 0) + s


def align_center(s: str, width: int, *, fill_char: str = " ") -> str:
    padding = fill_char * (max(width - strlen(s), 0) // 2)
    return align_left(padding + s + padding, width, fill_char=fill_char)


def equalized_lines(
    lines: Iterable[str], *, fill_char: str = " ", max_length: int = None
) -> Iterator[str]:
    for line in equalized(lines, fill_char, max_length=max_length):
        yield "".join(line)


def transposed_lines(lines: Iterable[str]) -> Iterator[str]:
    for col in transpose(lines):
        yield "".join(col)


def split_at(s: str, pos: int) -> tuple[str, str]:
    return s[:pos], s[pos:]


def split_conditional[T](
    collection: list[T], condition: Callable[[T], bool]
) -> tuple[list[T], list[T]]:
    left = [item for item in collection if condition(item)]
    right = [item for item in collection if item not in left]
    return left, right
