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
from math import sqrt
from string import hexdigits
from typing import Optional, Union

import matplotlib as mpl

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
            COLORS_NAMED[v].append(k)


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


class DynamicColor:

    """A callback-aware color object to simplify color manipulation in
    matplotlib.
    """

    callback_properties = ("alpha", "hex_code", "hsv", "name", "rgb", "rgba")

    def __init__(self,
                 color: Union[str, tuple[NUMERIC, ...]],
                 space: str = "rgb"):
        self.parse(color, space=space)

    @callback_property
    def alpha(self) -> float:
        """Getter for color alpha channel value.

        :return: Current alpha channel value, normalized to [0, 1]
        :rtype: float
        """
        return self._alpha

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
        :raises TypeError: if `new_alpha` is not `NUMERIC`
        :raises ValueError: if `new_alpha` is not in the range `[0, 1]`
        """
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `alpha` must be a numeric "
                       f"between 0 and 1 (received object of type: "
                       f"{type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[{error_trace(self)}] `alpha` must be a numeric "
                       f"between 0 and 1 (received: {repr(new_alpha)})")
            raise ValueError(err_msg)
        self._alpha = new_alpha
        self._hex_code = mpl.colors.to_hex(self.rgba, keep_alpha=True)

    @callback_property
    def hex_code(self) -> str:
        """Getter for the current color's hexadecimal representation, including
        alpha channel value, in `'#rrggbbaa'` format.

        :return: current hex code, in `'#rrggbbaa'` format
        :rtype: str
        """
        return self._hex_code

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
        :raises TypeError: if `new_hex` isn't a string
        :raises ValueError: if `new_hex` isn't a valid hex code
        """
        if not isinstance(new_hex, str):
            err_msg = (f"[{error_trace(self)}] `hex_code` must be a string "
                       f"of the form '#rrggbb' or '#rrggbbaa' (received "
                       f"object of type: {type(new_hex)})")
            raise TypeError(err_msg)
        if (not (len(new_hex) == 7 or len(new_hex) == 9) or
            not new_hex[0] == "#" or
            not all(c in hexdigits for c in new_hex[1:])):
            err_msg = (f"[{error_trace(self)}] `hex_code` must be a string "
                       f"of the form '#rrggbb' or '#rrggbbaa' (received: "
                       f"{new_hex})")
            raise ValueError(err_msg)
        if len(new_hex) == 9:
            self._hex_code = new_hex.lower()
        else:
            self._hex_code = new_hex.lower() + "ff"
        rgba = mpl.colors.to_rgba(self._hex_code)
        self._rgb = rgba[:-1]
        self._alpha = rgba[-1]
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code[:7] in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._name = None

    @callback_property
    def hsv(self) -> tuple[float, float, float]:
        """Getter for the current color's hsv (hue, saturation, value)
        representation, excluding alpha channel.

        :return: current hsv color, as a length-3 tuple of numerics
             normalized to `[0, 1]`
        :rtype: tuple[float, float, float]
        """
        return self._hsv

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
        :raises TypeError: if `new_hsv` isn't a tuple
        :raises ValueError: if `new_hsv` isn't length-3, or doesn't contain
            `NUMERIC`s in the range `[0, 1]`
        """
        if not isinstance(new_hsv, tuple):
            err_msg = (f"[{error_trace(self)}] `hsv` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received object of "
                       f"type: {type(new_hsv)})")
            raise TypeError(err_msg)
        if (len(new_hsv) != 3 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_hsv) or
            not all(0 <= v <= 1 for v in new_hsv)):
            err_msg = (f"[{error_trace(self)}] `hsv` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received: {new_hsv})")
            raise ValueError(err_msg)
        self._hsv = new_hsv
        self._rgb = tuple(mpl.colors.hsv_to_rgb(self._hsv))
        if not hasattr(self, "_alpha"):
            self._alpha = 1.0
        self._hex_code = mpl.colors.to_hex(self.rgba, keep_alpha=True)
        if self._hex_code[:7] in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._name = None

    @callback_property
    def name(self) -> Optional[str]:
        """Getter for the current color's name, as defined in
        :func:`matplotlib.colors.get_named_colors_mapping`.  If no matching
        color can be found, this defaults to `None`.

        :return: name of a recognized color, or `None`
        :rtype: Optional[str]
        """
        return self._name

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
        :raises TypeError: if `new_color` isn't a string
        :raises ValueError: if `new_color` isn't recognized as a named color
        """
        if not isinstance(new_color, str):
            err_msg = (f"[{error_trace(self)}] `name` must be a string "
                       f"referencing a key in `NAMED_COLORS` (received object "
                       f"of type: {type(new_color)})")
            raise TypeError(err_msg)
        if new_color not in NAMED_COLORS:
            err_msg = (f"[{error_trace(self)}] `name` must be a string "
                       f"referencing a key in `NAMED_COLORS` (received: "
                       f"{repr(new_color)})")
            raise ValueError(err_msg)
        self._name = new_color
        self._rgb = mpl.colors.to_rgb(NAMED_COLORS[self._name])
        if not hasattr(self, "_alpha"):
            self._alpha = 1.0
        self._hex_code = mpl.colors.to_hex(self.rgba, keep_alpha=True)
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))

    @callback_property
    def rgb(self) -> tuple[float, float, float]:
        """Getter for the current color's RGB (Red, Green, Blue)
        representation, excluding alpha channel.

        :return: length-3 tuple of current color's RGB values, normalized to
            `[0, 1]`
        :rtype: tuple[float, float, float]
        """
        return self._rgb

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
        :raises TypeError: if `new_rgb` isn't a tuple
        :raises ValueError: if `new_rgb` isn't length-3, or doesn't contain
            `NUMERIC`s in the range `[0, 1]`
        """
        if not isinstance(new_rgb, tuple):
            err_msg = (f"[{error_trace(self)}] `rgb` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received object of "
                       f"type: {type(new_rgb)})")
            raise TypeError(err_msg)
        if (len(new_rgb) != 3 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_rgb) or
            not all(0 <= v <= 1 for v in new_rgb)):
            err_msg = (f"[{error_trace(self)}] `rgb` must be a length-3 tuple "
                       f"of numerics between 0 and 1 (received: {new_rgb})")
            raise ValueError(err_msg)
        self._rgb = new_rgb
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if not hasattr(self, "_alpha"):
            self._alpha = 1.0
        self._hex_code = mpl.colors.to_hex(self.rgba, keep_alpha=True)
        if self._hex_code[:7] in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._name = None

    @callback_property
    def rgba(self) -> tuple[float, float, float, float]:
        """Getter for the current color's RGBA (Red, Green, Blue, Alpha)
        representation, including alpha channel.

        :return: length-4 tuple of RGBA values normalized to `[0, 1]`
        :rtype: tuple[float, float, float, float]
        """
        return self._rgb + (self._alpha,)

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
        :raises TypeError: if `new_rgba` isn't a tuple
        :raises ValueError: if `new_rgba` isn't length-4, or doesn't contain
            `NUMERIC`s in the range `[0, 1]`
        """
        if not isinstance(new_rgba, tuple):
            err_msg = (f"[{error_trace(self)}] `rgba` must be a length-4 "
                       f"tuple of numerics between 0 and 1 (received object "
                       f"of type: {type(new_rgba)})")
            raise TypeError(err_msg)
        if (len(new_rgba) != 4 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_rgba) or
            not all(0 <= v <= 1 for v in new_rgba)):
            err_msg = (f"[{error_trace(self)}] `rgba` must be a length-4 "
                       f"tuple of numerics between 0 and 1 (received: "
                       f"{new_rgba})")
            raise ValueError(err_msg)
        self._rgb = new_rgba[:-1]
        self._alpha = new_rgba[-1]
        self._hex_code = mpl.colors.to_hex(self.rgba, keep_alpha=True)
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code[:7] in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._name = None

    def blend(self,
              other_color: DynamicColor,
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

        :param other_color: another DynamicColor object to blend with
        :type other_color: DynamicColor
        :param mode: blend mode to use, defaults to "multiply"
        :type mode: str, optional
        :param in_place: if `True`, replace the current DynamicColor values and
            and return a reference to `self`, defaults to False
        :type in_place: bool, optional
        :param space: determines the color space to use when receiving parsable
            color-like objects.  If you want to use an HSV color rather than
            RGB, set this to `'hsv'`.
        :type space: str, optional
        :raises TypeError: if `other_color` isn't a DynamicColor and is of a
            type that cannot be coerced into one, or if `mode` isn't a string
        :raises ValueError: if `other_color` has values that prevent it from
            being coerced into a DynamicColor object, or if `mode` isn't one
            of the allowed values
        :return: A DynamicColor representing the product of the blend operation.
            If `in_place=True`, this is a reference to `self`.
        :rtype: DynamicColor
        """
        if not isinstance(other_color, DynamicColor):
            try:
                other_color = DynamicColor(other_color, space=space)
            except (TypeError, ValueError) as exc:
                err_msg = (f"[{error_trace(self)}] `other_color` must be "
                           f"either an instance of DynamicColor or a "
                           f"color-like object that can be easily converted "
                           f"into one (received: {repr(other_color)})")
                raise type(exc)(err_msg) from exc
        if not isinstance(mode, str):
            err_msg = (f"[{error_trace(self)}] `mode` must be a string with "
                       f"one of the following values: "
                       f"{list(BLEND_MODES.keys())} (received object of "
                       f"type: {type(mode)})")
            raise TypeError(err_msg)
        if mode not in BLEND_MODES:
            err_msg = (f"[{error_trace(self)}] `mode` must be a string with "
                       f"one of the following values: "
                       f"{list(BLEND_MODES.keys())} (received: "
                       f"{repr(mode)})")
            raise ValueError(err_msg)
        new_rgb = tuple(map(BLEND_MODES[mode], self.rgb, other_color.rgb))
        if in_place:
            self.rgb = new_rgb
            return self
        return DynamicColor(new_rgb)

    def distance(self,
        other_color: DynamicColor,
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

        :param other_color: DynamicColor object to measure the distance to, or
            an object which can be easily coerced into one (e.g. `'white'`,
            `(1, 1, 1)`, or `'#ffffffff'`)
        :type other_color: DynamicColor
        :param weighted: if `True`, use redmean weighted distance measure,
            defaults to False
        :type weighted: bool, optional
        :param space: determines the color space to use when receiving parsable
            color-like objects.  If you want to use an HSV color rather than
            RGB, set this to `'hsv'`.
        :type space: str, optional
        :raises TypeError: if `other_color` is of a type that can't be
            interpreted as a DynamicColor
        :raises ValueError: if `other_color` has values can't be coerced into
            a DynamicColor object
        :return: float representing the distance between the DynamicColor
            objects
        :rtype: float
        """
        if not isinstance(other_color, DynamicColor):
            try:
                other_color = DynamicColor(other_color, space=space)
            except TypeError as exc:
                err_msg = (f"[{error_trace(self)}] `other_color` must be "
                           f"either an instance of DynamicColor or a "
                           f"color-like object that can be easily converted "
                           f"into one (received object of type: "
                           f"{type(other_color)})")
                raise TypeError(err_msg) from exc
            except ValueError as exc:
                err_msg = (f"[{error_trace(self)}] `other_color` must be "
                           f"either an instance of DynamicColor or a "
                           f"color-like object that can be easily converted "
                           f"into one (received: {repr(other_color)})")
                raise ValueError(err_msg) from exc
        squares = [(v1-v2)**2 for v1, v2 in zip(self.rgb, other_color.rgb)]
        if weighted:
            redmean = (self.rgb[0] + other_color.rgb[0]) / 2
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
        color_like: Union[str, tuple[NUMERIC, ...], DynamicColor],
        space: str = "rgb") -> None:
        """Parses a color-like object, setting the current color to match.

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

        :param colorlike: a DynamicColor or color-like string or tuple of
            `NUMERICS` that can be coerced into a DynamicColor object
        :type colorlike: Union[str, tuple[NUMERIC, ...], DynamicColor]
        :raises TypeError: if `colorlike` is of a type that can't be
            interpreted as a DynamicColor
        :raises ValueError: if `colorlike` has values that can't be coerced
            into a DynamicColor
        """
        allowed_spaces = {"rgb", "hsv"}
        if not isinstance(space, str):
            err_msg = (f"[{error_trace(self)}] `space` must be a string with "
                       f"one of the following values: {allowed_spaces} "
                       f"(received object of type: {type(space)})")
            raise TypeError(err_msg)
        if space not in allowed_spaces:
            err_msg = (f"[{error_trace(self)}] `space` must be a string with "
                       f"one of the following values: {allowed_spaces} "
                       f"(received: {repr(space)})")
            raise ValueError(err_msg)
        try:
            if isinstance(color_like, DynamicColor):
                self.rgba = color_like.rgba
            elif isinstance(color_like, str):
                if color_like in NAMED_COLORS:
                    self.name = color_like
                else:
                    self.hex_code = color_like
            else:
                if space == "rgb":
                    if len(color_like) == 3:
                        self.rgb = color_like
                    else:
                        self.rgba = color_like
                else:
                    self.hsv = color_like
        except (TypeError, ValueError) as exc:
            err_msg = (f"[{error_trace(self)}] `color_like` must be a string "
                       f"referencing a named color ('white') or hex code of "
                       f"the form '#rrggbb[aa]', or a tuple of numeric values "
                       f"between 0 and 1, representing either an `(r, g, b)`, "
                       f"`(h, s, v)` or `(r, g, b, a)` color specification"
                       f"(received object of type: {type(color_like)})")
            raise type(exc)(err_msg) from exc

    def properties(self) -> dict[str, Union[str, tuple[float, ...]]]:
        """Returns a property dictionary that lists all the mutable attributes
        of this DynamicColor instance paired with their current values.

        :return: dictionary whose keys represent property names and values are
            their current settings.
        :rtype: dict[str, Union[str, tuple[float, ...]]]
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

    def __add__(self, other_color: DynamicColor) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='add'`.

        :param other_color: another DynamicColor to blend with, or a color-like
            that can be coerced into one.
        :type other_color: DynamicColor
        :return: a DynamicColor representing the product of the additive blend
        :rtype: DynamicColor
        """
        return self.blend(other_color, mode="add")

    def __eq__(self, other_color: DynamicColor) -> bool:
        """Distance-based comparison for DynamicColor equality.

        :param other_color: another DynamicColor to compare to, or a color-like
            that can be coerced into one.
        :type other_color: DynamicColor
        :return: `True` if the distance between colors is 0
        :rtype: bool
        """
        return self.distance(other_color) == 0.0

    def __hash__(self) -> int:
        return hash(id(self))

    def __ne__(self, other_color: DynamicColor) -> bool:
        return not self.__eq__(other_color)

    def __mul__(self, other_color: DynamicColor) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='multiply'`.

        :param other_color: another DynamicColor to blend with, or a color-like
            that can be coerced into one.
        :type other_color: DynamicColor
        :return: a DynamicColor representing the product of the multiplicative
            blend
        :rtype: DynamicColor
        """
        return self.blend(other_color, mode="multiply")

    def __repr__(self) -> str:
        return f"DynamicColor({self.rgba})"

    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        return self.hex_code

    def __sub__(self, other_color: DynamicColor) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='subtract'`.

        :param other_color: another DynamicColor to blend with, or a color-like
            that can be coerced into one.
        :type other_color: DynamicColor
        :return: a DynamicColor representing the product of the subtraction
            blend
        :rtype: DynamicColor
        """
        return self.blend(other_color, mode="subtract")

    def __truediv__(self, other_color: DynamicColor) -> DynamicColor:
        """An alias for :meth:`~curvefit.color.DynamicColor.blend` with
        `mode='divide'`.

        :param other_color: another DynamicColor to blend with, or a color-like
            that can be coerced into one.
        :type other_color: DynamicColor
        :return: a DynamicColor representing the product of the division blend
        :rtype: DynamicColor
        """
        return self.blend(other_color, mode="divide")
