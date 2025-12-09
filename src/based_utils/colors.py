from dataclasses import dataclass, replace
from functools import cached_property
from typing import TYPE_CHECKING, Self

from hsluv import hex_to_hsluv, hsluv_to_hex

from .calx import fractions, trim

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class RGB:
    red: int
    green: int
    blue: int


type HSLuv = tuple[float, float, float]


@dataclass(frozen=True)
class _HSLuvColor:
    hue: float = 0  # 0 - 1 (full circle angle)
    saturation: float = 1  # 0 - 1 (ratio)
    lightness: float = 0.5  # 0 - 1 (ratio)

    def __repr__(self) -> str:
        hue, sat, li = self._hsluv
        return f"Color(hue={hue:.2f}°, saturation={sat:.2f}%, lightness={li:.2f}%)"

    @classmethod
    def _from_hsluv(cls, hsluv: HSLuv) -> Self:
        hue, sat, li = hsluv
        return cls(hue / 360, sat / 100, li / 100)

    @cached_property
    def _hsluv(self) -> HSLuv:
        return self.hue * 360, self.saturation * 100, self.lightness * 100

    @classmethod
    def from_hex(cls, rgb_hex: str) -> Self:
        """
        Create a Color from an RGB hex string.

        :param rgb_hex: RGB hex string (may start with '#') or None
        :return: Color instance

        >>> Color.from_hex("3").hex
        '333333'
        >>> Color.from_hex("03").hex
        '030303'
        >>> Color.from_hex("303").hex
        '330033'
        >>> c = Color.from_hex("808303")
        >>> c.hex
        '808303'
        >>> c.rgb
        RGB(red=128, green=131, blue=3)
        >>> c2 = Color.from_hex("0af")
        >>> c2.hex
        '00aaff'
        >>> c2.rgb
        RGB(red=0, green=170, blue=255)
        """
        rgb_hex = rgb_hex.removeprefix("#").lower()

        if len(rgb_hex) == 1:
            # 3 -> r=33, g=33, b=33
            r = g = b = rgb_hex * 2

        elif len(rgb_hex) == 2:
            # 03 -> r=03, g=03, b=03
            r = g = b = rgb_hex

        elif len(rgb_hex) == 3:
            # 303 -> r=33, g=00, b=33
            r1, g1, b1 = iter(rgb_hex)
            r, g, b = r1 * 2, g1 * 2, b1 * 2

        elif len(rgb_hex) == 6:
            # 808303 -> r=80, g=83, b=03
            r1, r2, g1, g2, b1, b2 = iter(rgb_hex)
            r, g, b = r1 + r2, g1 + g2, b1 + b2

        else:
            raise ValueError(rgb_hex)

        return cls._from_hsluv(hex_to_hsluv(f"#{r}{g}{b}"))

    @cached_property
    def hex(self) -> str:
        return hsluv_to_hex(self._hsluv)[1:]

    @classmethod
    def from_rgb(cls, rgb: RGB) -> Self:
        """
        Create a Color from RGB values.

        :param rgb: RGB instance or None
        :return: Color instance

        >>> c = Color.from_rgb(RGB(128, 131, 3))
        >>> c.hex
        '808303'
        >>> c.rgb
        RGB(red=128, green=131, blue=3)
        >>> c2 = Color.from_rgb(RGB(0, 170, 255))
        >>> c2.hex
        '00aaff'
        >>> c2.rgb
        RGB(red=0, green=170, blue=255)
        """
        return cls.from_hex(f"{rgb.red:02x}{rgb.green:02x}{rgb.blue:02x}")

    @cached_property
    def rgb(self) -> RGB:
        r1, r2, g1, g2, b1, b2 = iter(self.hex)
        return RGB(int(r1 + r2, 16), int(g1 + g2, 16), int(b1 + b2, 16))


class Color(_HSLuvColor):
    def __post_init__(self) -> None:
        super().__init__(trim(self.lightness), trim(self.saturation), self.hue % 1)

    def _copy(
        self, *, hue: float = None, saturation: float = None, lightness: float = None
    ) -> Color:
        kwargs = {"lightness": lightness, "saturation": saturation, "hue": hue}
        return replace(self, **{k: v for k, v in kwargs.items() if v is not None})

    def shade(self, lightness: float) -> Color:
        return self._copy(lightness=lightness)

    def saturated(self, saturation: float) -> Color:
        return self._copy(saturation=saturation)

    def shades(self, n: int, *, inclusive: bool = False) -> Iterator[Color]:
        """
        Generate n shades of this color.

        :param n: amount of shades generated
        :param inclusive: if we want to include 0 and 1 or not
        :return: iterator of shades

        >>> [c.hex for c in Color.from_hex("08f").shades(5)]
        ['002955', '004e97', '0076e0', '6ca2ff', 'bccfff']
        >>> [c.hex for c in Color.from_hex("08f").shades(5, inclusive=True)]
        ['000000', '002955', '004e97', '0076e0', '6ca2ff', 'bccfff', 'ffffff']
        """
        for lightness in fractions(n, inclusive=inclusive):
            yield self.shade(lightness)

    def adjust(
        self, *, hue: float = None, saturation: float = None, lightness: float = None
    ) -> Color:
        return Color(
            self.hue + (hue or 0),
            self.saturation * (saturation or 1),
            self.lightness * (lightness or 1),
        )

    def brighter(self, relative_amount: float) -> Color:
        return self.adjust(lightness=relative_amount)

    def darker(self, relative_amount: float) -> Color:
        return self.brighter(1 / relative_amount)

    @cached_property
    def contrasting_shade(self) -> Color:
        """
        Color with a lightness that contrasts with the current color.

        Color with a 50% lower or higher lightness than the current color,
        while maintaining the same hue and saturation (so it can for example
        be used as background color).

        :return: Color representation of the contrasting shade

        >>> Color.from_hex("08f").contrasting_shade.hex
        '001531'
        >>> Color.from_hex("0f8").contrasting_shade.hex
        '006935'
        >>> Color.from_hex("80f").contrasting_shade.hex
        'ebe4ff'
        >>> Color.from_hex("8f0").contrasting_shade.hex
        '366b00'
        >>> Color.from_hex("f08").contrasting_shade.hex
        '2b0012'
        >>> Color.from_hex("f80").contrasting_shade.hex
        '4a2300'
        """
        return self.shade((self.lightness + 0.5) % 1)

    @cached_property
    def contrasting_hue(self) -> Color:
        """
        Color with a hue that contrasts with the current color.

        Color with a 180° different hue than the current color,
        while maintaining the same saturation and perceived lightness.

        :return: Color representation of the contrasting hue

        >>> Color.from_hex("08f").contrasting_hue.hex
        '9c8900'
        >>> Color.from_hex("0f8").contrasting_hue.hex
        'ffd1f5'
        >>> Color.from_hex("80f").contrasting_hue.hex
        '5c6900'
        >>> Color.from_hex("8f0").contrasting_hue.hex
        'f6d9ff'
        >>> Color.from_hex("f08").contrasting_hue.hex
        '009583'
        >>> Color.from_hex("f80").contrasting_hue.hex
        '00b8d1'
        """
        return self.adjust(hue=0.5)


def c(h: int) -> Color:
    return Color(h / 360)


@dataclass(frozen=True)
class ColorTheme:
    """
    Helper class to make a Colors class return Color objects.

    Can be overridden by specifying a custom anum with
    a different set of hues (in degrees):
    >>> class MyColors(ColorTheme):
    ...     tomato = c(15)
    ...     turquoise = c(175)
    >>> MyColors.tomato
    Color(hue=15.00°, saturation=100.00%, lightness=50.00%)
    >>> MyColors.grey
    Color(hue=0.00°, saturation=0.00%, lightness=50.00%)
    """

    grey = Color(saturation=0)
    black = grey.shade(0)
    white = grey.shade(1)


@dataclass(frozen=True)
class Colors(ColorTheme):
    """Highly opinionated (though carefully selected) color theme."""

    red = c(12)
    orange = c(29)
    yellow = c(68)
    poison = c(101)
    green = c(127)
    ocean = c(182)
    blue = c(244)
    indigo = c(267)
    purple = c(281)
    pink = c(329)

    brown = orange.saturated(0.35)


@dataclass(frozen=True)
class AltColors(ColorTheme):
    """Alternative color theme."""

    red = c(10)
    orange = c(35)
    yellow = c(75)
    poison = c(100)
    green = c(126)
    ocean = c(184)
    blue = c(242)
    indigo = c(268)
    purple = c(280)
    pink = c(325)

    brown = orange.saturated(0.35)
