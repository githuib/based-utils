from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, Literal, Self, overload

from hsluv import hex_to_hsluv, hsluv_to_hex, hsluv_to_rgb, rgb_to_hsluv

from .calx import fractions, trim

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class RGB:
    red: int
    green: int
    blue: int


type ColorName = Literal[
    "red",
    "orange",
    "yellow",
    "poison",
    "green",
    "ocean",
    "blue",
    "indigo",
    "purple",
    "pink",
]

COLORS: list[ColorName] = [
    "red",
    "orange",
    "yellow",
    "poison",
    "green",
    "ocean",
    "blue",
    "indigo",
    "purple",
    "pink",
]


type Hues = dict[ColorName, int]


"""
Highly opinionated (though carefully selected) color theme.

Can be overridden by specifying a custom Color class with
a different set of hues (in degrees):
>>> my_hues: Hues = {
...    "red": 9,
...    "orange": 36,
...    "yellow": 78,
...    ...
... }
...
... class MyColor(Color):
...     hues = my_hues
"""
HUES: Hues = {
    "red": 12,
    "orange": 29,
    "yellow": 68,
    "poison": 101,
    "green": 127,
    "ocean": 182,
    "blue": 244,
    "indigo": 267,
    "purple": 281,
    "pink": 329,
}
HUES_2: Hues = {
    "red": 10,
    "orange": 35,
    "yellow": 75,
    "poison": 100,
    "green": 126,
    "ocean": 184,
    "blue": 242,
    "indigo": 268,
    "purple": 280,
    "pink": 325,
}


@dataclass(frozen=True, order=True)
class Color:
    lightness: float  # 0 - 1 (ratio)
    saturation: float  # 0 - 1 (ratio)
    hue: float  # 0 - 1 (full circle angle)

    hues: ClassVar[Hues] = HUES

    def __repr__(self) -> str:
        h, s, li = self.hsluv_tuple
        return f"Color(hue={h:.2f}°, saturation={s:.2f}%, lightness={li:.2f}%)"

    @classmethod
    def from_fields(
        cls, *, lightness: float = 0.5, saturation: float = 1, hue: float = 0
    ) -> Self:
        return cls(trim(lightness), trim(saturation), hue % 1)

    def but_with(
        self, *, lightness: float = None, saturation: float = None, hue: float = None
    ) -> Self:
        return self.__class__.from_fields(
            lightness=self.lightness if lightness is None else lightness,
            saturation=self.saturation if saturation is None else saturation,
            hue=self.hue if hue is None else hue,
        )

    def with_changed(
        self, *, lightness: float = None, saturation: float = None, hue: float = None
    ) -> Self:
        return self.but_with(
            lightness=None if lightness is None else self.lightness * lightness,
            saturation=None if saturation is None else self.saturation * saturation,
            hue=None if hue is None else (self.hue + hue),
        )

    @classmethod
    def from_name(
        cls, name: ColorName, *, lightness: float = 0.5, saturation: float = 1
    ) -> Self:
        return cls.from_fields(
            lightness=lightness, saturation=saturation, hue=cls.hues[name] / 360
        )

    @classmethod
    def grey(cls, lightness: float = 0.5) -> Self:
        return cls.from_fields(lightness=lightness, saturation=0)

    @classmethod
    def from_hsluv_tuple(cls, hsluv: tuple[float, float, float]) -> Self:
        hue, saturation, lightness = hsluv
        return cls(lightness / 100, saturation / 100, hue / 360)

    @cached_property
    def hsluv_tuple(self) -> tuple[float, float, float]:
        return self.hue * 360, self.saturation * 100, self.lightness * 100

    @overload
    @classmethod
    def from_hex(cls, rgb_hex: str) -> Self: ...

    @overload
    @classmethod
    def from_hex(cls, rgb_hex: None) -> None: ...

    @classmethod
    def from_hex(cls, rgb_hex: str | None) -> Self | None:
        """
        Create a Color from an RGB hex string.

        :param rgb_hex: RGB hex string (may start with '#') or None
        :return: Color instance

        >>> Color.from_hex(None) is None
        True
        >>> Color.from_hex("3").hex
        '333333'
        >>> Color.from_hex("03").hex
        '030303'
        >>> Color.from_hex("303").hex
        '330033'
        >>> Color.from_hex("808303").hex
        '808303'
        """
        if rgb_hex is None:
            return None

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

        return cls.from_hsluv_tuple(hex_to_hsluv(f"#{r}{g}{b}"))

    @cached_property
    def hex(self) -> str:
        return hsluv_to_hex(self.hsluv_tuple)[1:]

    @overload
    @classmethod
    def from_rgb(cls, rgb: RGB) -> Self: ...

    @overload
    @classmethod
    def from_rgb(cls, rgb: None) -> None: ...

    @classmethod
    def from_rgb(cls, rgb: RGB | None) -> Self | None:
        """
        Create a Color from RGB values.

        :param rgb: RGB instance or None
        :return: Color instance

        >>> Color.from_rgb(None) is None
        True
        >>> Color.from_rgb(RGB(128, 131, 3)).rgb
        RGB(red=128, green=131, blue=3)
        """
        if rgb is None:
            return None
        return cls.from_hsluv_tuple(
            rgb_to_hsluv((rgb.red / 255, rgb.green / 255, rgb.blue / 255))
        )

    @cached_property
    def rgb(self) -> RGB:
        r, g, b = hsluv_to_rgb(self.hsluv_tuple)
        return RGB(round(r * 255), round(g * 255), round(b * 255))

    @cached_property
    def contrasting_shade(self) -> Self:
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
        return self.but_with(lightness=(self.lightness + 0.5) % 1)

    @cached_property
    def contrasting_hue(self) -> Self:
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
        return self.with_changed(hue=0.5)

    def shade(self, lightness: float) -> Self:
        return self.but_with(lightness=lightness)

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
