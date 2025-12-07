import sys
import time
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from functools import reduce
from itertools import count
from os import get_terminal_size
from typing import TYPE_CHECKING, cast

from based_utils.calx import randf
from based_utils.colors import Color

from .formats import LINE_CLEAR, LINE_UP, Colored

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

type Lines = Iterable[str]


@dataclass(frozen=True)
class AnimParams:
    fps: int | None = None
    keep_last: bool = True
    only_every_nth: int = 1
    crop_to_terminal: bool = False


def refresh_lines(lines: Lines, *, crop_to_terminal: bool = True) -> int:
    block = list(lines)
    height = len(block)
    if crop_to_terminal:
        # Could be nice to crop to width as well, but it seems
        # to me vertical cropping is a bit quirky now anyway.
        _max_width, max_height = get_terminal_size()
        height = min(max_height - 1, height)
    for line in block[-height:]:
        sys.stdout.write(line + "\n")
    return height


def clear_lines(amount: int) -> None:
    for _ in range(amount):
        sys.stdout.write(LINE_UP + LINE_CLEAR)


def animate[T](
    items: Iterable[T],
    format_item: Callable[[T], Lines] | None = None,
    *,
    params: AnimParams = None,
) -> Iterator[T]:
    if params is None:
        params = AnimParams()

    def to_lines(item_: T) -> Lines:
        if format_item is None:
            # Somewhat sketchy but I can't think of a better way to
            # "do nothing" by default, that mypy would be ok with.
            return cast("Lines", item_)
        return format_item(item_)

    with suppress(KeyboardInterrupt):
        lines_written = 0
        for i, item in enumerate(items):
            yield item
            if i % params.only_every_nth != 0:
                continue

            clear_lines(lines_written)
            lines_written = refresh_lines(
                to_lines(item), crop_to_terminal=params.crop_to_terminal
            )
            if params.fps:
                time.sleep(1 / params.fps)

        if not params.keep_last:
            clear_lines(lines_written)


type Animation = Callable[[Lines, int, int], Lines]


def animated(
    lines: Lines, *animations: Animation, num_frames: int = None, fill_char: str = " "
) -> Callable[[], Iterator[Lines]]:
    def func() -> Iterator[Lines]:
        max_width, max_height = get_terminal_size()
        n_frames = max_width if num_frames is None else num_frames

        block = list(lines)
        height = min(len(block), max_height - 1)
        block = block[-height:]
        block_width = max(len(line) for line in block)

        def frame_0() -> Lines:
            for line in block:
                yield line.ljust(block_width, fill_char).center(max_width, fill_char)

        def frame_(n: int) -> Callable[[Lines, Animation], Lines]:
            def anim(frame: Lines, a: Animation) -> Lines:
                return a(frame, n, n_frames)

            return anim

        for f in count():
            yield reduce(frame_(f), animations, frame_0())

    return func


"""
Frame N functions
"""


def moving_forward(frame_0: Lines, n: int, n_frames: int) -> Lines:
    n %= n_frames
    for line in frame_0:
        yield line[-n:] + line[:-n]


def fuck_me_sideways(frame_0: Lines, n: int, n_frames: int) -> Lines:
    n %= n_frames
    lines = list(frame_0)
    h = len(lines) - 1
    hh = h // 2
    for y, line in enumerate(lines):
        x = n * -(((hh + y) % h) - hh)
        yield line[x:] + line[:x]


def _colorful(
    colors: Callable[[float, float], tuple[Color, Color]], *, amount_of_hues: int = 360
) -> Animation:
    def anim(frame_0: Lines, n: int, _n_frames: int) -> Lines:
        hue = n / amount_of_hues
        fg, bg = colors(n, hue)
        for line in frame_0:
            yield Colored(line, fg, bg).formatted

    return anim


def changing_colors(*, amount_of_hues: int = 360) -> Animation:
    def colors(_n: float, hue: float) -> tuple[Color, Color]:
        fg = Color.from_fields(hue=hue, lightness=0.75)
        bg = fg.contrasting_hue.contrasting_shade
        return fg, bg

    return _colorful(colors, amount_of_hues=amount_of_hues)


def flashing(
    *,
    amount_of_hues: int = 360,
    intensity: float = 303_909_303 / 10**10,
    fg: Color = None,
    bg: Color = None,
) -> Animation:
    def colors(n: float, hue: float) -> tuple[Color, Color]:
        flash_ratio = 3
        flash = n % flash_ratio == 0 and randf() < intensity * flash_ratio
        c_fg = Color.from_fields(hue=hue, lightness=0.5) if fg is None else fg
        c_bg = c_fg.shade(0.2) if bg is None else bg
        if flash:
            hue = hue + 0.5 if fg is None else randf()
            c_fg = c_fg.but_with(hue=hue, lightness=0.3)
            c_bg = c_bg.but_with(hue=hue, lightness=0.9)
        return c_fg, c_bg

    return _colorful(colors, amount_of_hues=amount_of_hues)
