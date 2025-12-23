import re
import sys
import time
from os import get_terminal_size
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


type Lines = Iterable[str]


ANSI_ESCAPE = "\x1b"

_ANSI_STYLE_REGEX = re.compile(rf"{ANSI_ESCAPE}\[\d+(;\d+)*m")


def ansi(s: str) -> str:
    return f"{ANSI_ESCAPE}[{s}"


def ansi_style(*values: int) -> str:
    return ansi(f"{';'.join(str(v) for v in values)}m")


def strip_ansi_style(s: str) -> str:
    return _ANSI_STYLE_REGEX.sub("", s)


LINE_UP = ansi("A")
LINE_CLEAR = ansi("2K")

RESET_STYLE = ansi_style(0)


def write_lines(lines: Iterable, *, crop_to_terminal: bool = False) -> int:
    block = [str(line) for line in lines]
    height = len(block)
    if crop_to_terminal:
        # Could be nice to crop to width as well, but it seems
        # to me vertical cropping is a bit quirky now anyway.
        _max_width, max_height = get_terminal_size()
        height = min(max_height - 1, height)
    for line in block[-height:]:
        sys.stdout.write(f"{line}\n")
    return height


def clear_lines(amount: int) -> None:
    for _ in range(amount):
        sys.stdout.write(LINE_UP + LINE_CLEAR)


def refresh_lines(
    lines: Iterable, *, fps: float = None, crop_to_terminal: bool = False
) -> None:
    lines_written = write_lines(lines, crop_to_terminal=crop_to_terminal)
    if fps:
        time.sleep(1 / fps)
    clear_lines(lines_written)
