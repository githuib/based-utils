from itertools import zip_longest
from typing import TYPE_CHECKING, Self, SupportsIndex

from kleur import Colored
from more_itertools import transpose
from wcwidth import wcswidth

from based_utils.data.iterators import filled_empty

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from kleur import Color


class TerminalStr(str):
    _raw_value: str
    __slots__ = ("_raw_value",)

    def __new__(cls, value: object) -> Self:
        instance = super().__new__(cls, value)
        instance._raw_value = str(value)
        return instance

    @property
    def _raw_len(self) -> int:
        return len(self._raw_value)

    @property
    def _len_diff(self) -> int:
        return len(self) - self._raw_len

    def __len__(self) -> int:
        return wcswidth(self._raw_value)

    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(self._raw_value.ljust(int(width) - self._len_diff, fillchar))

    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(self._raw_value.rjust(int(width) - self._len_diff, fillchar))

    def center(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(
            self._raw_value.center(int(width) - self._len_diff, fillchar)
        )


def format_table(
    *table_rows: Iterable[str | int],
    min_columns_widths: Iterable[int] = None,
    column_splits: Iterable[int] = None,
    color: Color = None,
) -> Iterator[str]:
    first, *rest = [tr for tr in table_rows if tr]
    trs: list[Iterable[str | int]] = [[], first, [], *rest, []]
    rows = list(filled_empty([[TerminalStr(v) for v in tr] for tr in trs], ""))

    def max_columns_widths() -> Iterator[int]:
        for col in transpose(rows):
            yield max(len(s) for s in col)

    def column_widths() -> Iterator[int]:
        for col_width, min_width in zip_longest(
            max_columns_widths(), min_columns_widths or [], fillvalue=0
        ):
            yield max(col_width, min_width)

    b = len(rows) - 1

    def t(s: str) -> str:
        return str(Colored(s, color))

    def left(r: int) -> str:
        return t("╔" if r == 0 else "╠" if r == 2 else "╚" if r == b else "║")

    def right(r: int) -> str:
        return t("╗" if r == 0 else "╣" if r == 2 else "╝" if r == b else "║")

    def center(r: int) -> str:
        return t("╦" if r == 0 else "╬" if r == 2 else "╩" if r == b else "║")

    for r_, row in enumerate(rows):
        yield (
            left(r_)
            + "".join(
                (t("═") * (w + 2) if r_ in (0, 2, b) else f" {s.ljust(w)} ")
                + (
                    f"{right(r_)}  {left(r_)}"
                    if c in (column_splits or [])
                    else right(r_)
                    if c == len(row)
                    else center(r_)
                )
                for c, (s, w) in enumerate(zip(row, column_widths(), strict=True), 1)
            )
        )
