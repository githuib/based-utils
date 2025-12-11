from itertools import zip_longest
from typing import TYPE_CHECKING
from unicodedata import east_asian_width

from kleur import Colored
from kleur.formatting import strip_ansi_style
from more_itertools import transpose

from based_utils.data.iterators import filled_empty

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from kleur import Color


def char_len(c: str) -> int:
    return 2 if east_asian_width(c) == "W" else 1


def str_len(s: str) -> int:
    return sum(char_len(c) for c in strip_ansi_style(s))


def align_left(s: str, width: int, *, fill_char: str = " ") -> str:
    return s + fill_char * max(width - str_len(s), 0)


def align_right(s: str, width: int, *, fill_char: str = " ") -> str:
    return fill_char * max(width - str_len(s), 0) + s


def align_center(s: str, width: int, *, fill_char: str = " ") -> str:
    padding = fill_char * (max(width - str_len(s), 0) // 2)
    return align_left(padding + s + padding, width, fill_char=fill_char)


def format_table(
    *table_rows: Iterable[str | int],
    min_columns_widths: Iterable[int] = None,
    column_splits: Iterable[int] = None,
    color: Color = None,
) -> Iterator[str]:
    first, *rest = [tr for tr in table_rows if tr]
    trs: list[Iterable[str | int]] = [[], first, [], *rest, []]
    rows = list(filled_empty([[str(v) for v in tr] for tr in trs], ""))

    def max_columns_widths() -> Iterator[int]:
        for col in transpose(rows):
            yield max(str_len(s) for s in col)

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
                (t("═") * (w + 2) if r_ in (0, 2, b) else f" {align_left(s, w)} ")
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
