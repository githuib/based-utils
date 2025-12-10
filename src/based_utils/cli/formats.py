import os
import re
import sys
from dataclasses import dataclass
from functools import cache, cached_property
from typing import TYPE_CHECKING
from unicodedata import east_asian_width

if TYPE_CHECKING:
    from collections.abc import Callable

    from based_utils.colors import RGB, Color

ANSI_ESCAPE = "\x1b"
_ANSI_STYLE_REGEX = re.compile(rf"{ANSI_ESCAPE}\[\d+(;\d+)*m")


def ansi(s: str) -> str:
    return f"{ANSI_ESCAPE}[{s}"


def ansi_style(*values: int) -> str:
    return ansi(f"{';'.join(str(v) for v in values)}m")


LINE_UP = ansi("A")
LINE_CLEAR = ansi("2K")

RESET_STYLE = ansi_style(0)


@cache
def has_colors() -> bool:
    no = "NO_COLOR" in os.environ
    yes = "CLICOLOR_FORCE" in os.environ
    maybe = sys.stdout.isatty()
    return not no and (yes or maybe)


def _apply_ansi_style(s: str, *values: int) -> str:
    if values and has_colors():
        return f"{ansi_style(*values)}{s}{RESET_STYLE}"
    return s


type _StringStyler = Callable[[str], str]


def _wrap_ansi_style(*values: int) -> _StringStyler:
    def wrapper(s: str) -> str:
        return _apply_ansi_style(s, *values)

    return wrapper


def strip_ansi_style(s: str) -> str:
    return _ANSI_STYLE_REGEX.sub("", s)


bold = _wrap_ansi_style(1)
faint = _wrap_ansi_style(2)
italic = _wrap_ansi_style(3)
underlined = _wrap_ansi_style(4)
inverse = _wrap_ansi_style(7)
strikethrough = _wrap_ansi_style(9)

black = _wrap_ansi_style(30)
red = _wrap_ansi_style(31)
green = _wrap_ansi_style(32)
yellow = _wrap_ansi_style(33)
blue = _wrap_ansi_style(34)
magenta = _wrap_ansi_style(35)
cyan = _wrap_ansi_style(36)
gray = _wrap_ansi_style(37)

black_background = _wrap_ansi_style(40)
red_background = _wrap_ansi_style(41)
green_background = _wrap_ansi_style(42)
yellow_background = _wrap_ansi_style(43)
blue_background = _wrap_ansi_style(44)
magenta_background = _wrap_ansi_style(45)
cyan_background = _wrap_ansi_style(46)
gray_background = _wrap_ansi_style(47)

light_gray = _wrap_ansi_style(90)
light_red = _wrap_ansi_style(91)
light_green = _wrap_ansi_style(92)
light_yellow = _wrap_ansi_style(93)
light_blue = _wrap_ansi_style(94)
light_magenta = _wrap_ansi_style(95)
light_cyan = _wrap_ansi_style(96)
white = _wrap_ansi_style(97)

OK = green("✔")
FAIL = red("✘")


def color_8bit(fg: int = None, bg: int = None) -> _StringStyler:
    values = []
    if fg:
        values += [38, 5, fg]
    if bg:
        values += [48, 5, bg]
    return _wrap_ansi_style(*values)


def color_rgb(fg: RGB = None, bg: RGB = None) -> _StringStyler:
    values = []
    if fg:
        values += [38, 2, *fg]
    if bg:
        values += [48, 2, *bg]
    return _wrap_ansi_style(*values)


@dataclass(frozen=True)
class Colored:
    value: object
    color: Color | None = None
    background: Color | None = None

    @cached_property
    def fmt(self) -> _StringStyler:
        fg, bg = self.color, self.background
        return color_rgb(fg.as_rgb if fg else None, bg.as_rgb if bg else None)

    def with_color(self, color: Color) -> Colored:
        return Colored(self.value, color, self.background)

    def with_background(self, background: Color) -> Colored:
        return Colored(self.value, self.color, background)

    @cached_property
    def raw(self) -> str:
        return str(self.value)

    @cached_property
    def _formatted(self) -> str:
        return self.fmt(self.raw)

    def __repr__(self) -> str:
        return self._formatted

    def __len__(self) -> int:
        return len(self.raw)


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
