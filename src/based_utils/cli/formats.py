import os
import re
import sys
from dataclasses import dataclass
from functools import cache, cached_property
from typing import TYPE_CHECKING
from unicodedata import east_asian_width

from yachalk import chalk

if TYPE_CHECKING:
    from collections.abc import Callable

    from based_utils.colors import Color

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


def _wrap_ansi_style(*values: int) -> Callable[[str], str]:
    def wrapper(s: str) -> str:
        return f"{ansi_style(*values)}{s}{RESET_STYLE}" if has_colors() else s

    return wrapper


def strip_ansi_style(s: str) -> str:
    return _ANSI_STYLE_REGEX.sub("", s)


bright = _wrap_ansi_style(1)
dim = _wrap_ansi_style(2)

black = _wrap_ansi_style(30)
red = _wrap_ansi_style(31)
green = _wrap_ansi_style(32)
yellow = _wrap_ansi_style(33)
blue = _wrap_ansi_style(34)
magenta = _wrap_ansi_style(35)
cyan = _wrap_ansi_style(36)
gray = _wrap_ansi_style(37)

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


@dataclass(frozen=True)
class Colored:
    value: object
    color: Color | None = None
    background: Color | None = None

    def with_color(self, color: Color) -> Colored:
        return Colored(self.value, color, self.background)

    def with_background(self, background: Color) -> Colored:
        return Colored(self.value, self.color, background)

    @cached_property
    def raw(self) -> str:
        return str(self.value)

    @cached_property
    def _formatted(self) -> str:
        s = self.raw
        if self.color:
            s = chalk.hex(self.color.as_hex)(s)
        if self.background:
            s = chalk.bg_hex(self.background.as_hex)(s)
        return s

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
