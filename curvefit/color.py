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
from collections import defaultdict
from math import sqrt
from string import hexdigits
from typing import Callable, Optional, Union

import matplotlib as mpl

from curvefit import error_trace, NUMERIC, NUMERIC_TYPECHECK
from curvefit.callback import callback_property


NAMED_COLORS = mpl.colors.get_named_colors_mapping()
COLORS_NAMED = defaultdict(list)
for k, v in NAMED_COLORS.items():
    COLORS_NAMED[v].append(k)
COLORS_NAMED = dict(COLORS_NAMED)


class DynamicColor:

    """A callback-aware color object to simplify color manipulation in
    matplotlib.
    """

    callback_properties = ("alpha", "hex_code", "hsv", "name", "rgb", "rgba")

    def __init__(self,
                 color: Union[str, tuple[NUMERIC, ...]],
                 color_spec: str = "rgb"):
        self.color_spec = color_spec
        self.parse(color)

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
        hex_alpha = hex(round(255 * self._alpha))
        self._hex_code = self._hex_code[:-2] + hex_alpha

    @property
    def color_spec(self) -> str:
        """Getter for current color specification, which determines how tuple
        color values are interpreted.  Allowed values are `{'rgb', 'hsv'}`.

        :return: current color specification
        :rtype: str
        """
        return self._color_spec

    @color_spec.setter
    def color_spec(self, new_color_spec: str) -> None:
        """Setter for current color specification, which determines how tuple
        color values are interpreted.  Allowed values are `{'rgb', 'hsv'}`.

        :param new_color_spec: new color specification
        :type new_color_spec: str
        :raises TypeError: if `new_color_spec` isn't a string
        :raises ValueError: if `new_color_spec` isn't in `{'rgb', 'hsv'}`
        """
        allowed_specs = {"rgb", "hsv"}
        if not isinstance(new_color_spec, str):
            err_msg = (f"[{error_trace(self)}] `color_spec` must be a "
                        f"string with one of the following values: "
                        f"{allowed_specs} (received object of type: "
                        f"{type(new_color_spec)})")
            raise TypeError(err_msg)
        if new_color_spec not in allowed_specs:
            err_msg = (f"[{error_trace(self)}] `color_spec` must be a "
                        f"string with one of the following values: "
                        f"{allowed_specs} (received: {repr(new_color_spec)})")
            raise ValueError(err_msg)
        self._color_spec = new_color_spec

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
            self._hex_code = new_hex
        else:
            self._hex_code = new_hex + "ff"
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
        if hasattr(self, "_alpha"):
            hex_alpha = hex(round(255 * self._alpha))[-2:]
            self._hex_code = mpl.colors.to_hex(self._rgb) + hex_alpha
        else:
            self._hex_code = mpl.colors.to_hex(self._rgb) + "ff"
            self._alpha = 1.0
        if self._hex_code in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code][0]
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
        if hasattr(self, "_alpha"):
            hex_alpha = hex(round(255 * self._alpha))[-2:]
            self._hex_code = NAMED_COLORS[self._name] + hex_alpha
        else:
            self._hex_code = NAMED_COLORS[self._name] + "ff"
            self._alpha = 1.0
        self._rgb = mpl.colors.to_rgb(self._hex_code)
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
        if hasattr(self, "_alpha"):
            hex_alpha = hex(round(255 * self._alpha))[-2:]
            self._hex_code = mpl.colors.to_hex(self._rgb) + hex_alpha
        else:
            self._hex_code = mpl.colors.to_hex(self._rgb) + "ff"
            self._alpha = 1.0
        if self._hex_code in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code][0]
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
        hex_alpha = hex(round(self._alpha))[-2:]
        self._hex_code = mpl.colors.to_hex(self._rgb) + hex_alpha
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code[:7] in COLORS_NAMED:
            self._name = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._name = None

    def blend(self,
              other_color: DynamicColor,
              mode: str = "multiply",
              in_place: bool = False,
              keep_alpha: bool = True) -> DynamicColor:
        """Blends one DynamicColor with another, treating the current color as
        the 'top' layer for non-commutative operations.

        :param other_color: another DynamicColor object to blend with
        :type other_color: DynamicColor
        :param mode: blend mode to use, defaults to "multiply"
        :type mode: str, optional
        :param in_place: if `True`, replace the current DynamicColor in-place,
            defaults to False
        :type in_place: bool, optional
        :param keep_alpha: if `True`, preserve this color's alpha channel,
            defaults to True
        :type keep_alpha: bool, optional
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
                other_color = DynamicColor(other_color)
            except (TypeError, ValueError) as exc:
                err_msg = (f"[{error_trace(self)}] `other_color` must be "
                           f"either an instance of DynamicColor or a "
                           f"color-like object that can be easily converted "
                           f"into one (received: {repr(other_color)})")
                raise type(exc)(err_msg) from exc
        allowed_modes = {
            "add": lambda a, b: min(a + b, 1.0),
            "subtract": lambda a, b: max(a-b, 0.0),
            "difference": lambda a, b: abs(a-b),
            "multiply": lambda a, b: a*b,
            "burn": lambda a, b: 1/min((1-b)/a, 1.0) if a > 0 else 1.0,
            "divide": lambda a, b: min(a/b, 1.0) if b > 0 else 1.0,
            "dodge": lambda a, b: min((1-a)/b, 1.0) if b > 0 else 1.0,
            "screen": lambda a, b: 1-(1-a)*(1-b),
            "overlay": lambda a, b: 2*a*b if a < 0.5 else 1-2*(1-a)*(1-b),
            "hard light": lambda a, b: 2*a*b if b < 0.5 else 1-2*(1-a)*(1-b),
            "soft light": lambda a, b: max(min((1-2*b)*a**2+2*b*a, 1.0), 0.0),
            "darken": min,
            "lighten": max
        }
        if not isinstance(mode, str):
            err_msg = (f"[{error_trace(self)}] `mode` must be a string with "
                       f"one of the following values: "
                       f"{list(allowed_modes.keys())} (received object of "
                       f"type: {type(mode)})")
            raise TypeError(err_msg)
        if mode not in allowed_modes:
            err_msg = (f"[{error_trace(self)}] `mode` must be a string with "
                       f"one of the following values: "
                       f"{list(allowed_modes.keys())} (received: "
                       f"{repr(mode)})")
            raise ValueError(err_msg)

        def do_blend(func: Callable) -> DynamicColor:
            new_rgb = tuple(map(func, self.rgb, other_color.rgb))
            if in_place:
                self.rgb = new_rgb
                if not keep_alpha:
                    self.alpha = 1.0
                return self
            if keep_alpha:
                return DynamicColor(new_rgb + (self.alpha,))
            return DynamicColor(new_rgb)

        return do_blend(allowed_modes[mode])

    def difference(self,
        other_color: DynamicColor,
        weighted: bool = False) -> float:
        """Returns the Euclidean distance between the RGB values of two
        DynamicColor objects, ignoring alpha channel values.

        If `weighted=True`, uses an approximation of human perception sometimes
        called 'redmean', which more closely matches the subjective difference
        between colors as they appear to the human eye.  The redmean distance
        formula is as follows (using a color range of 0-255):

        :math:`
        \\begin{array}{l}
            \\bar{r} = \\frac{R_1 + R_2}{2} &\\\\
            \\Delta C = \\sqrt{
                (2 + \\frac{\\bar{r}}{256}) \\times (R_1 - R_2)^2 +
                4 \\times (G_1 - G_2)^2 +
                (2 + \\frac{255 - \\bar{r}}{256}) \\times (B_1 - B_2)^2
            } &\\\\
        \\end{array}
        `

        :param other_color: DynamicColor object to measure the distance to, or
            an object which can be easily coerced into one (e.g. `'white'`,
            `(1, 1, 1)`, or `'#ffffffff'`)
        :type other_color: DynamicColor
        :param weighted: if `True`, use redmean weighted distance measure,
            defaults to False
        :type weighted: bool, optional
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
                other_color = DynamicColor(other_color)
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

    def invert(self,
               in_place: bool = False,
               keep_alpha: bool = True) -> DynamicColor:
        """Inverts the current DynamicColor's RGB values, returning a new
        DynamicColor object.

        :param in_place: if `True`, replace the current DynamicColor in-place,
            defaults to False
        :type in_place: bool, optional
        :param keep_alpha: if `True`, preserve this color's alpha channel,
            defaults to True
        :type keep_alpha: bool, optional
        :return: A DynamicColor representing the product of the color inversion.
            If `in_place=True`, this is a reference to `self`.
        :rtype: DynamicColor
        """
        new_rgb = tuple(map(lambda v: 1 - v, self.rgb))
        if in_place:
            self.rgb = new_rgb
            if not keep_alpha:
                self.alpha = 1.0
            return self
        if keep_alpha:
            return DynamicColor(new_rgb + (self.alpha,))
        return DynamicColor(new_rgb)

    def parse(
        self,
        colorlike: Union[str, tuple[NUMERIC, ...], DynamicColor]) -> None:
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
        if not isinstance(colorlike, (str, tuple, DynamicColor)):
            err_msg = (f"[{error_trace(self)}] `color` must be a string "
                       f"referencing a named color ('white') or hex code of "
                       f"the form '#rrggbb[aa]', or a tuple of numeric values "
                       f"between 0 and 1, representing either an `(r, g, b)`, "
                       f"`(h, s, v)` or `(r, g, b, a)` color specification"
                       f"(received object of type: {type(colorlike)})")
            raise TypeError(err_msg)
        if isinstance(colorlike, tuple):
            if self.color_spec == "rgb":
                if len(colorlike) == 3:
                    self.rgb = colorlike
                else:
                    self.rgba = colorlike
            else:
                self.hsv = colorlike
        elif isinstance(colorlike, str):
            if colorlike in NAMED_COLORS:
                self.name = colorlike
            else:
                self.hex_code = colorlike
        else:  # colorlike is DynamicColor
            self.rgba = colorlike.rgba

    def properties(self) -> dict[str, Union[str, tuple[float, ...]]]:
        """Returns a property dictionary that lists all the mutable attributes
        of this DynamicColor instance paired with their current values.

        :return: dictionary whose keys represent property names and values are
            their current settings.
        :rtype: dict[str, Union[str, tuple[float, ...]]]
        """
        prop_dict = {
            "alpha": self.alpha,
            "color_spec": self.color_spec,
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
        return self.difference(other_color) == 0.0

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
        return f"DynamicText({self.rgba})"

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
