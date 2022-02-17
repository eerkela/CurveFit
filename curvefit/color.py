"""A dynamic color processing module, with support for state-based callbacks.

DynamicColor objects are used for every matplotlib element that supports color
manipulation, allowing easy blending, color inversion, and distance
measurements, alongside pythonic, property-based state changes.

Callbacks can be easily added to any DynamicColor property via the
:mod:`curvefit.callback` module.

Typical usage example:

`
color = DynamicColor('white')
color.alpha = 0.5   # set opacity to 50% and invoke related callbacks
color.hex_code = '#ff0000'   # set color to pure red and invoke callbacks
color.distance((0, 0, 1))   # return distance between pure red and pure blue
color.blend('xkcd:cyan', mode='screen')   # easily blend colors
color.invert(in_place=True)   # invert color values
color.hsv   # fields are dynamically updated
color2 = color + (0.1, 0.1, 0.1)  # basic arithmetic for quick blends
`
"""
from __future__ import annotations
from functools import lru_cache
from string import hexdigits

import matplotlib as mpl
from numpy import sqrt, isclose

from curvefit import error_trace, NUMERIC, NUMERIC_TYPECHECK
from curvefit.callback import callback_property


NAMED_COLORS = {}
COLORS_NAMED = {}
for k, v in mpl.colors.get_named_colors_mapping().items():
    if isinstance(v, str):
        v = v.lower()
        NAMED_COLORS[k] = v
        if v not in COLORS_NAMED:
            COLORS_NAMED[v] = [k]
        else:
            # for python >= 3.10, bisect.insort now supports key functions
            # from bisect import insort
            # insort(COLORS_NAMED[v], k, key=len)
            COLORS_NAMED[v].append(k)
            COLORS_NAMED[v].sort(key=len)  # prefer colors without extensions


BLEND_MODES = {
    "add": lambda b, t: min(b + t, 1.0),
    "subtract": lambda b, t: max(b - t, 0.0),
    "difference": lambda b, t: abs(b - t),
    "multiply": lambda b, t: b * t,
    "divide": lambda b, t: min(b / t, 1.0) if t > 0 else 1.0,
    "burn": lambda b, t: max(1 - (1 - b) / t, 0.0) if t > 0 else 0.0,
    "dodge": lambda b, t: min(b / (1 - t), 1.0) if t < 1 else 1.0,
    "screen": lambda b, t: 1 - (1 - b) * (1 - t),
    "overlay": lambda b, t: 2*b*t if b < 0.5 else 1 - 2 * (1 - b) * (1 - t),
    "hard light": lambda b, t: 2*b*t if t < 0.5 else 1 - 2 * (1 - b) * (1 - t),
    "soft light": lambda b, t: (1 - 2 * t) * b**2 + 2 * t * b,
    "darken": min,
    "lighten": max
}


def to_rgba(
    color_like: str | tuple[NUMERIC, ...] | DynamicColor,
    space: str = "rgb") -> tuple[float, float, float]:
    """Converts a color-like object to a tuple of RGBA values.
    
    A color-like object can be any of:
        #. a previously existing DynamicColor object
        #. a named color string (e.g. `'white'`)
        #. a hex code with or without an alpha channel (e.g. `'#rrggbb'`
            or `'#rrggbbaa'`)
        #. a length-3 tuple containing HSV values with `color_spec='hsv'`
            (e.g. `(0.1, 0.2, 0.3)`)
        #. a length-3 tuple containing RGB values with `color_spec='rgb'`
            (e.g. `(1, 0, 0)`)
        #. a length-4 tuple containing RGBA values with `color_spec='rgb'`
            (e.g. `(1, 0, 0, 1)`)

    `space` can have values `{'rgb', 'hsv'}`

    :param colorlike: a DynamicColor or color-like string or tuple of
        `NUMERICS` that can be coerced into a DynamicColor object
    :type colorlike: str | tuple[NUMERIC, ...] | DynamicColor
    :param space: the color space to use when interpreting ambiguous tuples,
        defaults to "rgb"
    :type space: str, optional
    :raises ValueError: if `color_like` can't be coerced into an RGB tuple
    :raises ValueError: if `space` isn't a string or doesn't have one of the
        allowed values
    :return: a tuple of RGBA values, normalized to `[0, 1]`
    :rtype: tuple[float, float, float]
    """
    allowed_spaces = {"rgb", "hsv"}
    if not isinstance(space, str) or space not in allowed_spaces:
        err_msg = (f"[{error_trace()}] `space` must be a string with one of "
                   f"the following values: {allowed_spaces} (received: "
                   f"{repr(space)})")
        raise ValueError(err_msg)
    
    if isinstance(color_like, DynamicColor):
        return color_like.rgba
    
    if isinstance(color_like, str):
        if color_like in NAMED_COLORS:
            return hex_to_rgba(NAMED_COLORS[color_like])
        if (color_like[0] == "#" and
            all(c in hexdigits for c in color_like[1:])):
            if len(color_like) == 7:
                return hex_to_rgba(color_like, alpha=1.0)
            if len(color_like) == 9:
                return hex_to_rgba(color_like)
    
    if isinstance(color_like, tuple):
        if (all(isinstance(v, NUMERIC_TYPECHECK) for v in color_like) and
                all(0 <= v <= 1 for v in color_like)):
            if space == "rgb":
                if len(color_like) == 3:
                    return color_like + (1.,)
                if len(color_like) == 4:
                    return color_like
            else:
                if len(color_like) == 3:
                    return hsv_to_rgb(color_like) + (1.,)
    
    err_msg = (f"[{error_trace()}] `color_like` must be a string referencing "
               f"a named color ('white') or hex code of the form "
               f"'#rrggbb[aa]', or a tuple of numeric values between 0 and 1, "
               f"representing either an `(r, g, b)`, `(h, s, v)` or "
               f"`(r, g, b, a)` color specification (received: "
               f"{repr(color_like)})")
    raise ValueError(err_msg)


@lru_cache(maxsize=128)
def rgba_to_hex(
    rgba: tuple[NUMERIC, NUMERIC, NUMERIC, NUMERIC],
    keep_alpha: bool = True) -> str:
    """Convert an RGBA color to a hex code"""
    return mpl.colors.to_hex(rgba, keep_alpha=keep_alpha)


@lru_cache(maxsize=128)
def hex_to_rgba(
    hex_code: str,
    alpha: NUMERIC = None) -> tuple[float, float, float, float]:
    """Convert a hex code to RGBA color"""
    return mpl.colors.to_rgba(hex_code, alpha=alpha)


@lru_cache(maxsize=128)
def rgb_to_hsv(
    rgb: tuple[NUMERIC, NUMERIC, NUMERIC]) -> tuple[NUMERIC, NUMERIC, NUMERIC]:
    """Convert an RGB color to HSV color space"""
    return tuple(mpl.colors.rgb_to_hsv(rgb))


@lru_cache(maxsize=128)
def hsv_to_rgb(
    hsv: tuple[NUMERIC, NUMERIC, NUMERIC]) -> tuple[NUMERIC, NUMERIC, NUMERIC]:
    """Convert an HSV color to RGB color space"""
    return tuple(mpl.colors.hsv_to_rgb(hsv))


class DynamicColor:

    """A callback-aware color object to simplify color manipulation in
    matplotlib.
    """

    callback_properties = {"alpha", "hex_code", "hsv", "name", "rgb", "rgba"}

    def __init__(self,
                 color: str | tuple[NUMERIC, ...],
                 space: str = "rgb"):
        self.parse(color, space=space)

    @callback_property
    def alpha(self) -> float:
        """Getter for color alpha channel value.

        :return: Current alpha channel value, normalized to [0, 1]
        :rtype: float
        """
        return self._rgba[-1]

    @alpha.setter
    def alpha(self, new_alpha: NUMERIC) -> None:
        """Callback-enabled setter for current alpha channel value.  Changes
        are automatically propagated to :attr:`~curvefit.color.hex_code` and
        :attr:`~curvefit.color.rgba`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_alpha: new alpha channel value, normalized to `[0, 1]`
        :type new_alpha: NUMERIC
        :raises ValueError: if `new_alpha` is not `NUMERIC` or not in the range
            `[0, 1]`
        """
        if (not isinstance(new_alpha, NUMERIC_TYPECHECK) or
            not 0 <= new_alpha <= 1):
            err_msg = (f"[{error_trace(self)}] `alpha` must be a numeric "
                       f"between 0 and 1 (received: {repr(new_alpha)})")
            raise ValueError(err_msg)
        self._rgba = self._rgba[:3] + (new_alpha,)

    @callback_property
    def hex_code(self) -> str:
        """Getter for the current color's hexadecimal representation, including
        alpha channel value, in `'#rrggbbaa'` format.

        :return: current hex code, in `'#rrggbbaa'` format
        :rtype: str
        """
        return rgba_to_hex(self._rgba)

    @hex_code.setter
    def hex_code(self, new_hex: str) -> None:
        """Callback-enabled setter for the current color's hexadecimal
        representation, with or without alpha channel value.  Changes
        are automatically propagated to :attr:`~curvefit.color.hsv`,
        :attr:`~curvefit.color.name`, :attr:`~curvefit.color.rgb`,
        :attr:`~curvefit.color.rgba`, and if an alpha value is specified,
        :attr:`~curvefit.color.alpha`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_hex: new hexadecimal color code, in the form `'#rrggbb'` or
            `'#rrggbbaa'`
        :type new_hex: str
        :raises ValueError: if `new_hex` isn't a string or isn't a valid hex
            code
        """
        if (not isinstance(new_hex, str) or
            (len(new_hex) != 7 and len(new_hex) != 9) or
            new_hex[0] != "#" or
            any(c not in hexdigits for c in new_hex[1:])):
            err_msg = (f"[{error_trace(self)}] `hex_code` must be a string "
                       f"of the form '#rrggbb' or '#rrggbbaa' (received: "
                       f"{repr(new_hex)})")
            raise ValueError(err_msg)
        if hasattr(self, "_rgba") and len(new_hex) == 7:
            self._rgba = hex_to_rgba(new_hex, alpha=self._rgba[-1])
        else:
            self._rgba = hex_to_rgba(new_hex)

    @callback_property
    def hsv(self) -> tuple[float, float, float]:
        """Getter for the current color's hsv (hue, saturation, value)
        representation, excluding alpha channel.

        :return: current hsv color, as a length-3 tuple of numerics
             normalized to `[0, 1]`
        :rtype: tuple[float, float, float]
        """
        return rgb_to_hsv(self._rgba[:3])

    @hsv.setter
    def hsv(self, new_hsv: tuple[NUMERIC, NUMERIC, NUMERIC]) -> None:
        """Callback-enabled setter for the current color's HSV (Hue,
        Saturation, Value) representation, excluding alpha channel.  Changes
        are automatically propagated to :attr:`~curvefit.color.hex_code`,
        :attr:`~curvefit.color.name`, :attr:`~curvefit.color.rgb`, and
        :attr:`~curvefit.color.rgba`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_hsv: the new HSV color values
        :type new_hsv: tuple[NUMERIC, NUMERIC, NUMERIC]
        :raises ValueError: if `new_hsv` isn't a tuple, is not length-3, or
            doesn't contain `NUMERIC`s in the range `[0, 1]`
        """
        if (not isinstance(new_hsv, tuple) or
            len(new_hsv) != 3 or
            any(not isinstance(v, NUMERIC_TYPECHECK) for v in new_hsv) or
            any(not 0 <= v <= 1 for v in new_hsv)):
            err_msg = (f"[{error_trace(self)}] `hsv` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received: "
                       f"{repr(new_hsv)})")
            raise ValueError(err_msg)
        if hasattr(self, "_rgba"):
            self._rgba = hsv_to_rgb(new_hsv) + (self._rgba[-1],)
        else:
            self._rgba = hsv_to_rgb(new_hsv) + (1.,)

    @callback_property
    def name(self) -> str | None:
        """Getter for the current color's name, as defined in
        :func:`matplotlib.colors.get_named_colors_mapping`.  If no matching
        color can be found, this defaults to `None`.

        :return: name of a recognized color, or `None`
        :rtype: str | None
        """
        return COLORS_NAMED.get(self.hex_code[:7], [None])[0]

    @name.setter
    def name(self, new_color: str) -> None:
        """Callback-enabled setter for the current color's name, as defined in
        :func:`matplotlib.colors.get_named_colors_mapping`. Changes are
        automatically propagated to :attr:`~curvefit.color.hex_code`,
        :attr:`~curvefit.color.hsv`, :attr:`~curvefit.color.rgb`, and
        :attr:`~curvefit.color.rgba`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_color: the name of a recognized matplotlib color
        :type new_color: str
        :raises ValueError: if `new_color` isn't a string, or isn't recognized
            as a named color
        """
        hex_code = NAMED_COLORS.get(new_color, None)
        if not isinstance(new_color, str) or not hex_code:
            err_msg = (f"[{error_trace(self)}] `name` must be a string "
                       f"referencing a key in `NAMED_COLORS` (received: "
                       f"{repr(new_color)})")
            raise ValueError(err_msg)
        if hasattr(self, "_rgba"):
            self._rgba = hex_to_rgba(hex_code, alpha=self._rgba[-1])
        else:
            self._rgba = hex_to_rgba(hex_code)

    @callback_property
    def rgb(self) -> tuple[float, float, float]:
        """Getter for the current color's RGB (Red, Green, Blue)
        representation, excluding alpha channel.

        :return: length-3 tuple of current color's RGB values, normalized to
            `[0, 1]`
        :rtype: tuple[float, float, float]
        """
        return self._rgba[:3]

    @rgb.setter
    def rgb(self, new_rgb: tuple[NUMERIC, NUMERIC, NUMERIC]) -> None:
        """Callback-enabled setter for the current color's RGB (Red, Green,
        Blue) representation, excluding alpha channel.  Changes are
        automatically propagated to :attr:`~curvefit.color.hex_code`,
        :attr:`~curvefit.color.hsv`, :attr:`~curvefit.color.name`, and
        :attr:`~curvefit.color.rgba`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_rgb: a tuple of new RGB values to use for the current color
        :type new_rgb: tuple[NUMERIC, NUMERIC, NUMERIC]
        :raises ValueError: if `new_rgb` isn't a tuple, is not length-3, or
            doesn't contain `NUMERIC`s in the range `[0, 1]`
        """
        if (not isinstance(new_rgb, tuple) or
            len(new_rgb) != 3 or
            any(not isinstance(v, NUMERIC_TYPECHECK) for v in new_rgb) or
            any(not 0 <= v <= 1 for v in new_rgb)):
            err_msg = (f"[{error_trace(self)}] `rgb` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received: "
                       f"{repr(new_rgb)})")
            raise ValueError(err_msg)
        if hasattr(self, "_rgba"):
            self._rgba = new_rgb + (self._rgba[-1],)
        else:
            self._rgba = new_rgb + (1.,)

    @callback_property
    def rgba(self) -> tuple[float, float, float, float]:
        """Getter for the current color's RGBA (Red, Green, Blue, Alpha)
        representation, including alpha channel.

        :return: length-4 tuple of RGBA values normalized to `[0, 1]`
        :rtype: tuple[float, float, float, float]
        """
        return self._rgba

    @rgba.setter
    def rgba(
        self,
        new_rgba: tuple[NUMERIC, NUMERIC, NUMERIC, NUMERIC]) -> None:
        """Callback-enabled setter for the current color's RGBA (Red, Green,
        Blue, Alpha) representation, including alpha channel.  Changes are
        automatically propagated to :attr:`~curvefit.color.hex_code`,
        :attr:`~curvefit.color.hsv`, :attr:`~curvefit.color.name`, and
        :attr:`~curvefit.color.rgb`.

        Whenever there is a state change in this property, all attached
        callbacks are invoked with a reference to this DynamicColor instance.
        See :func:`curvefit.callback.add_callback` and
        :func:`curvefit.callback.remove_callback` for more details on
        adding/removing callbacks from
        :class:`curvefit.callback.CallbackProperties` objects.

        :param new_rgba: a tuple of new RGBA values to use for the current color
        :type new_rgba: tuple[NUMERIC, NUMERIC, NUMERIC, NUMERIC]
        :raises ValueError: if `new_rgba` isn't a tuple, is not length-4, or
            doesn't contain `NUMERIC`s in the range `[0, 1]`
        """
        if (not isinstance(new_rgba, tuple) or
            len(new_rgba) != 4 or
            any(not isinstance(v, NUMERIC_TYPECHECK) for v in new_rgba) or
            any(not 0 <= v <= 1 for v in new_rgba)):
            err_msg = (f"[{error_trace(self)}] `rgba` must be a length-4 "
                       f"tuple of numerics between 0 and 1 (received: "
                       f"{new_rgba})")
            raise ValueError(err_msg)
        self._rgba = new_rgba

    def blend(self,
              color_like: str | tuple[NUMERIC, ...] | DynamicColor,
              mode: str = "overlay",
              in_place: bool = False,
              space: str = "rgb") -> DynamicColor:
        """Blends one DynamicColor with another, treating the current color as
        the bottom layer for non-commutative operations.

        The available blend modes and their related operations on the RGB
        values of the bottom (b) and top (t) layers are as follows:
            #. `'add'`: arithmetic addition.
                :math:`f(b, t) = min(b + t, 1)`
            #. `'subtract'`: arithmetic subtraction.
                :math:`f(b, t) = max(b - t, 0)`
            #. `'difference'`: absolute value of `'subtract'`.
                :math:`f(b, t) = abs(b - t)`
            #. `'multiply'`: arithmetic multiplication.
                :math:`f(b, t) = b * t`
            #. `'divide'`: arithmetic division.
                :math:`f(b, t) = min(b / t, 1)`
            #. `'burn'`: invert bottom layer, divide by top layer, and then
                invert the result.  This tends to darken the top layer, causing
                shadows to clip and changing the overall black point.  Blending
                any color with black produces black, and blending with white
                does not change the original image.
                :math:`f(b, t) = max(1 - (1 - b) / t, 0)`
            #. `'dodge'`: divide bottom layer by inverted top layer.  This
                tends to lighten the bottom layer, causing highlights to clip
                and changing the overall white point.  Blending any color with
                white produces white, and blending with black does not change
                the original image.
                :math:`f(b, t) = min(b / (1 - t), 1)`
            #. `'screen'`: invert both layers, multiply, and then invert again.
                The result is the opposite of `'multiply'`.  Wherever either
                layer is darker than white, the composite will be brighter.
                :math:`f(b, t) = 1 - (1 - b) * (1 - t)`
            #. `'overlay'`: combines `'multiply'` and `'screen'` blend modes.
                If the top layer is darker than middle gray, multiply the
                layers and scale by a factor of 2.  If it is lighter than
                middle gray, invert both layers, multiply them, scale by a
                factor of 2, and then invert again.  This has a tendency
                to increase the contrast ratio.
                :math:`f(b, t) = 2 * b * t` if :math:`b \\lt 0.5` else
                :math:`f(b, t) = 1 - 2 * (1 - b) * (1 - t)`
            #. `'hard light'`: also combines `'multiply'` and `'screen'`, but
                in the opposite way as `'overlay'`.  Rather than comparing the
                top layer to middle gray, this compares the bottom layer.
                :math:`f(b, t) = 2 * b * t` if :math:`t \\lt 0.5` else
                :math:`f(b, t) = 1 - 2 * (1 - b) * (1 - t)`
            #. `'soft light'`: originally implemented in photoshop, this is
                related to `'hard light'` in name only.  The implementation
                used here is the 'pegtop' variation, which avoids local
                contrast discontinuities.
                :math:`f(b, t) = (1 - 2 * t) * b^2 + 2 * t * b`
            #. `'darken'`: chooses the minimum value between layers.
                :math:`f(b, t) = min(b, t)`
            #. `'lighten'`: chooses the maximum value between layers.
                :math:`f(b, t) = max(b, t)`

        :param color_like: another DynamicColor object to blend with
        :type color_like: DynamicColor
        :param mode: blend mode to use, defaults to "multiply"
        :type mode: str, optional
        :param in_place: if `True`, replace the current DynamicColor values and
            and return a reference to `self`, defaults to False
        :type in_place: bool, optional
        :param space: determines the color space to use when receiving parsable
            color-like objects.  If you want to use an HSV color rather than
            RGB, set this to `'hsv'`.
        :type space: str, optional
        :raises ValueError: if `color_like` can't be coerced into an RGB tuple,
            or if `mode` isn't one of the allowed values
        :return: A DynamicColor representing the product of the blend operation.
            If `in_place=True`, this is a reference to `self`.
        :rtype: DynamicColor
        """
        if not isinstance(mode, str) or mode not in BLEND_MODES:
            err_msg = (f"[{error_trace(self)}] `mode` must be a string with "
                       f"one of the following values: "
                       f"{list(BLEND_MODES.keys())} (received: "
                       f"{repr(mode)})")
            raise ValueError(err_msg)
        try:
            other_rgb = to_rgba(color_like, space=space)[0:3]
        except ValueError as exc:
            err_msg = f"[{error_trace(self)}] could not blend colors"
            raise ValueError(err_msg) from exc
        new_rgb = tuple(map(BLEND_MODES[mode], self.rgb, other_rgb))
        if in_place:
            self.rgb = new_rgb
            return self
        return DynamicColor(new_rgb)

    def distance(self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor,
        weighted: bool = False,
        space: str = "rgb") -> float:
        """Returns the Euclidean distance between the RGB values of two
        DynamicColor objects, ignoring relative alpha.

        If `weighted=True`, uses an approximation of human perception sometimes
        called 'redmean', which more closely matches the sensitivity of the
        human eye.  The redmean distance formula is as follows (using a color
        range of 0-255):

        .. math:

            \\bar{r} = \\frac{R_1 + R_2}{2}

            \\Delta C = \\sqrt{
                (2 + \\frac{\\bar{r}}{256}) \\times (R_1 - R_2)^2 +
                4 \\times (G_1 - G_2)^2 +
                (2 + \\frac{255 - \\bar{r}}{256}) \\times (B_1 - B_2)^2
            }

        :param color_like: DynamicColor object to measure the distance to, or
            an object which can be easily coerced into one (e.g. `'white'`,
            `(1, 1, 1)`, or `'#ffffffff'`)
        :type color_like: DynamicColor
        :param weighted: if `True`, use redmean weighted distance measure,
            defaults to False
        :type weighted: bool, optional
        :param space: determines the color space to use when receiving parsable
            color-like objects.  If you want to use an HSV color rather than
            RGB, set this to `'hsv'`.
        :type space: str, optional
        :raises ValueError: if `color_like` can't be coerced into an RGB tuple
        :return: float representing the distance between the DynamicColor
            objects
        :rtype: float
        """
        try:
            other_rgb = to_rgba(color_like, space=space)[0:3]
        except ValueError as exc:
            err_msg = f"[{error_trace(self)}] could not compute distance"
            raise ValueError(err_msg) from exc
        squares = [(v1-v2)**2 for v1, v2 in zip(self.rgb, other_rgb)]
        if weighted:
            redmean = (self.rgb[0] + other_rgb[0]) / 2
            denom = 1 + 1/255
            factors = [2 + redmean/denom, 4, 2 + (1 - redmean)/denom]
            return sqrt(sum([v1*v2 for v1, v2 in zip(factors, squares)]))
        return sqrt(sum(squares))

    def invert(self, in_place: bool = False) -> DynamicColor:
        """Inverts the current DynamicColor's RGB values, returning a new
        DynamicColor object.

        :param in_place: if `True`, replace the current DynamicColor values and
            return a reference to `self`, defaults to False
        :type in_place: bool, optional
        :return: A DynamicColor representing the product of the color inversion.
            If `in_place=True`, this is a reference to `self`.
        :rtype: DynamicColor
        """
        new_rgb = tuple(map(lambda v: 1 - v, self.rgb))
        if in_place:
            self.rgb = new_rgb
            return self
        return DynamicColor(new_rgb)

    def parse(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor,
        space: str = "rgb") -> None:
        """Parses a color-like object, setting the current color to match."""
        try:
            self.rgba = to_rgba(color_like, space=space)
        except ValueError as exc:
            err_msg = f"[{error_trace(self)}] could not parse color"
            raise ValueError(err_msg) from exc

    def properties(self) -> dict[str, str | tuple[float, ...]]:
        """Returns a property dictionary that lists all the mutable attributes
        of this DynamicColor instance paired with their current values.

        :return: dictionary whose keys represent property names and values are
            their current settings.
        :rtype: dict[str, str | tuple[float, ...]]
        """
        prop_dict = {
            "alpha": self.alpha,
            "hex_code": self.hex_code,
            "hsv": self.hsv,
            "name": self.name,
            "rgb": self.rgb,
            "rgba": self.rgba
        }
        return prop_dict

    def __add__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='add'`
        """
        return self.blend(color_like, mode="add")

    def __eq__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> bool:
        """Distance-based comparison for DynamicColor equality."""
        return isclose(self.distance(color_like), 0)

    def __hash__(self) -> int:
        return hash(id(self))

    def __ne__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> bool:
        return not self.__eq__(color_like)

    def __mul__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='multiply'`
        """
        return self.blend(color_like, mode="multiply")

    def __repr__(self) -> str:
        return f"DynamicColor({self.rgba})"

    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        return self.hex_code

    def __sub__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='subtract'`
        """
        return self.blend(color_like, mode="subtract")

    def __truediv__(
        self,
        color_like: str | tuple[NUMERIC, ...] | DynamicColor
    ) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='divide'`
        """
        return self.blend(color_like, mode="divide")
