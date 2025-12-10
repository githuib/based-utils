from dataclasses import astuple, dataclass, replace
from functools import cached_property, total_ordering

from hsluv import hex_to_hsluv, hsluv_to_hex, hsluv_to_rgb, rgb_to_hsluv

from .calx import mapped, mapped_cyclic, trim

_INCREASE_FACTOR = 2**0.5


def _normalize_rgb_hex(rgb_hex: str) -> str:
    """
    Try to normalize a hex string into a rrggbb hex.

    :param rgb_hex: RGB hex string (may start with '#')
    :return: rrggbb hex

    >>> _normalize_rgb_hex("3")
    '333333'
    >>> _normalize_rgb_hex("03")
    '030303'
    >>> _normalize_rgb_hex("303")
    '330033'
    >>> _normalize_rgb_hex("808303")
    '808303'
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

    return f"{r}{g}{b}"


type _RGB = tuple[int, int, int]


@dataclass(frozen=True)
class _HSLuv:
    hue: float
    saturation: float
    lightness: float

    def __repr__(self) -> str:
        hue = f"hue={self.hue:.2f}°"
        saturation = f"saturation={self.saturation:.2f}%"
        lightness = f"lightness={self.lightness:.2f}%"
        return f"Color({hue}, {saturation}, {lightness})"

    @classmethod
    def from_hex(cls, rgb_hex: str) -> _HSLuv:
        return cls(*hex_to_hsluv(f"#{rgb_hex}"))

    @cached_property
    def as_hex(self) -> str:
        return hsluv_to_hex(astuple(self))[1:]

    @classmethod
    def from_rgb(cls, rgb: _RGB) -> _HSLuv:
        r, g, b = rgb
        return cls(*rgb_to_hsluv((r / 255, g / 255, b / 255)))

    @cached_property
    def as_rgb(self) -> _RGB:
        r, g, b = hsluv_to_rgb(astuple(self))
        return round(r * 255), round(g * 255), round(b * 255)


@dataclass(frozen=True)
class _Color:
    """Party trick to allow __post_init__() to set the attributes."""

    hue: float = 0  # 0 - 1 (full circle angle)
    saturation: float = 1  # 0 - 1 (ratio)
    lightness: float = 0.5  # 0 - 1 (ratio)


@total_ordering
@dataclass(frozen=True)
class Color(_Color):
    def __post_init__(self) -> None:
        super().__init__(self.hue % 1, trim(self.saturation), trim(self.lightness))

    def __repr__(self) -> str:
        return repr(self._as_hsluv)

    def __lt__(self, other: Color) -> bool:
        return self.as_sortable_tuple < other.as_sortable_tuple

    @cached_property
    def as_sortable_tuple(self) -> tuple[float, float, float]:
        return self.lightness, self.saturation, self.hue

    @classmethod
    def _from_hsluv(cls, hsluv: _HSLuv) -> Color:
        return cls(hsluv.hue / 360, hsluv.saturation / 100, hsluv.lightness / 100)

    @cached_property
    def _as_hsluv(self) -> _HSLuv:
        return _HSLuv(self.hue * 360, self.saturation * 100, self.lightness * 100)

    @classmethod
    def from_hex(cls, rgb_hex: str) -> Color:
        """
        Create a Color from an RGB hex string.

        :param rgb_hex: RGB hex string (may start with '#')
        :return: Color instance

        >>> c1 = Color.from_hex("808303")
        >>> c1.as_hex
        '808303'
        >>> c1.as_rgb
        (128, 131, 3)
        >>> c2 = Color.from_hex("0af")
        >>> c2.as_hex
        '00aaff'
        >>> c2.as_rgb
        (0, 170, 255)
        """
        return cls._from_hsluv(_HSLuv.from_hex(_normalize_rgb_hex(rgb_hex)))

    @cached_property
    def as_hex(self) -> str:
        return self._as_hsluv.as_hex

    @classmethod
    def from_rgb(cls, rgb: _RGB) -> Color:
        """
        Create a Color from RGB values.

        :param rgb: RGB instance
        :return: Color instance

        >>> c1 = Color.from_rgb((128, 131, 3))
        >>> c1.as_hex
        '808303'
        >>> c1.as_rgb
        (128, 131, 3)
        >>> c2 = Color.from_rgb((0, 170, 255))
        >>> c2.as_hex
        '00aaff'
        >>> c2.as_rgb
        (0, 170, 255)
        """
        return cls._from_hsluv(_HSLuv.from_rgb(rgb))

    @cached_property
    def as_rgb(self) -> _RGB:
        return self._as_hsluv.as_rgb

    def adjust(
        self, *, hue: float = None, saturation: float = None, lightness: float = None
    ) -> Color:
        return Color(
            self.hue + (hue or 0),
            self.saturation * (saturation or 1),
            self.lightness * (lightness or 1),
        )

    def shade(self, lightness: float) -> Color:
        return replace(self, lightness=lightness)

    def saturated(self, saturation: float) -> Color:
        return replace(self, saturation=saturation)

    @cached_property
    def very_bright(self) -> Color:
        return self.shade(5 / 6)

    @cached_property
    def bright(self) -> Color:
        return self.shade(4 / 6)

    @cached_property
    def dark(self) -> Color:
        return self.shade(2 / 6)

    @cached_property
    def very_dark(self) -> Color:
        return self.shade(1 / 6)

    def brighter(self, relative_amount: float = _INCREASE_FACTOR) -> Color:
        return self.adjust(lightness=relative_amount)

    @cached_property
    def slightly_brighter(self) -> Color:
        return self.brighter(_INCREASE_FACTOR**0.5)

    @cached_property
    def much_brighter(self) -> Color:
        return self.brighter(_INCREASE_FACTOR**2)

    def darker(self, relative_amount: float = _INCREASE_FACTOR) -> Color:
        return self.brighter(1 / relative_amount)

    @cached_property
    def slightly_darker(self) -> Color:
        return self.darker(_INCREASE_FACTOR**0.5)

    @cached_property
    def much_darker(self) -> Color:
        return self.darker(_INCREASE_FACTOR**2)

    def blend(self, other: Color, amount: float = 0.5) -> Color:
        return Color(
            mapped_cyclic(amount, (self.hue, other.hue), period=1),
            mapped(amount, (self.saturation, other.saturation)),
            mapped(amount, (self.lightness, other.lightness)),
        )

    @cached_property
    def contrasting_shade(self) -> Color:
        """
        Color with a lightness that contrasts with the current color.

        Color with a 50% lower or higher lightness than the current color,
        while maintaining the same hue and saturation (so it can for example
        be used as background color).

        :return: Color representation of the contrasting shade

        >>> Color.from_hex("08f").contrasting_shade.as_hex
        '001531'
        >>> Color.from_hex("0f8").contrasting_shade.as_hex
        '006935'
        >>> Color.from_hex("80f").contrasting_shade.as_hex
        'ebe4ff'
        >>> Color.from_hex("8f0").contrasting_shade.as_hex
        '366b00'
        >>> Color.from_hex("f08").contrasting_shade.as_hex
        '2b0012'
        >>> Color.from_hex("f80").contrasting_shade.as_hex
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

        >>> Color.from_hex("08f").contrasting_hue.as_hex
        '9c8900'
        >>> Color.from_hex("0f8").contrasting_hue.as_hex
        'ffd1f5'
        >>> Color.from_hex("80f").contrasting_hue.as_hex
        '5c6900'
        >>> Color.from_hex("8f0").contrasting_hue.as_hex
        'f6d9ff'
        >>> Color.from_hex("f08").contrasting_hue.as_hex
        '009583'
        >>> Color.from_hex("f80").contrasting_hue.as_hex
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


class Colors(ColorTheme):
    """Highly opinionated (though carefully selected) color theme."""

    red = c(12)
    orange = c(33)
    yellow = c(69)
    poison = c(101)
    green = c(127)
    ocean = c(190)
    blue = c(248)
    indigo = c(267)
    purple = c(281)
    pink = c(329)

    brown = orange.blend(yellow, 0.25).saturated(0.5)


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

    brown = orange.blend(yellow, 0.3).saturated(0.5)
