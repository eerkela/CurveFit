from __future__ import annotations
from collections import defaultdict
from math import sqrt
from string import hexdigits
from typing import Callable, Optional, Union

import matplotlib as mpl

from curvefit import CallableList, error_trace, NUMERIC, NUMERIC_TYPECHECK


"""
TODO: Implement Sphinx documentation
TODO: Add callback decorators
https://blog.ty-porter.dev/development/2021/08/26/python-decorators-make-callbacks-simple.html
"""


NAMED_COLORS = mpl.colors.get_named_colors_mapping()
COLORS_NAMED = defaultdict(list)
for k, v in NAMED_COLORS.items():
    COLORS_NAMED[v].append(k)
COLORS_NAMED = dict(COLORS_NAMED)


def color_diff(rgb1: tuple[NUMERIC, NUMERIC, NUMERIC],
               rgb2: tuple[NUMERIC, NUMERIC, NUMERIC]) -> float:
    return sqrt(sum([(v1 - v2)**2 for v1, v2 in zip(rgb1, rgb2)]))


class DynamicColor:

    def __init__(self,
                 color: Union[str, tuple[NUMERIC, ...]],
                 color_spec: str = "rgb",
                 callbacks: Union[list[Callable], CallableList] = None):
        if not isinstance(color, (str, tuple)):
            err_msg = (f"[{error_trace(self)}] `color` must be a string "
                       f"referencing a named color ('white') or hex code of "
                       f"the form '#rrggbb[aa]', or a tuple of numeric values "
                       f"between 0 and 1, representing either an `(r, g, b)`, "
                       f"`(h, s, v)` or `(r, g, b, a)` color specification"
                       f"(received object of type: {type(color)})")
            raise TypeError(err_msg)
        # self.callbacks = CallableList()
        # if callbacks:
        #     try:
        #         self.callbacks.extend(callbacks)
        #     except (TypeError, ValueError) as exc:
        #         err_msg = (f"[{error_trace(self)}] `callbacks` must either be "
        #                    f"a list of callable functions or a CallableList ")
        #         raise type(exc)(err_msg) from exc
        if isinstance(color, tuple):
            allowed_specs = {"rgb", "hsv"}
            if not isinstance(color_spec, str):
                err_msg = (f"[{error_trace(self)}] `color_spec` must be a "
                           f"string with one of the following values: "
                           f"{allowed_specs} (received object of type: "
                           f"{type(color_spec)})")
                raise TypeError(err_msg)
            if color_spec not in allowed_specs:
                err_msg = (f"[{error_trace(self)}] `color_spec` must be a "
                           f"string with one of the following values: "
                           f"{allowed_specs} (received: {repr(color_spec)})")
                raise ValueError(err_msg)
            if color_spec == "rgb":
                if len(color) == 3:
                    self.rgb = color
                else:
                    self.rgba = color
            else:
                self.hsv = color
        else:
            if color in NAMED_COLORS:
                self.name = color
            else:
                self.hex_code = color

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, new_alpha: NUMERIC) -> None:
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
        # for func in self.callbacks:
        #     func(self)

    @property
    def hex_code(self) -> str:
        return self._hex_code

    @hex_code.setter
    def hex_code(self, new_hex: str) -> None:
        if not isinstance(new_hex, str):
            err_msg = (f"[{error_trace(self)}] `hex_code` must be a string "
                       f"of the form '#rrggbb' or '#rrggbbaa' (received "
                       f"object of type: {type(new_hex)})")
            raise TypeError(err_msg)
        if (not len(new_hex) == 7 or len(new_hex) == 9 or
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
        # for func in self.callbacks:
        #     func(self)

    @property
    def hsv(self) -> tuple[float, float, float]:
        return self._hsv

    @hsv.setter
    def hsv(self, new_hsv: tuple[NUMERIC, NUMERIC, NUMERIC]) -> None:
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
        # for func in self.callbacks:
        #     func(self)

    @property
    def name(self) -> Optional[str]:
        return self._name

    @name.setter
    def name(self, new_color: str) -> None:
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
        # for func in self.callbacks:
        #     func(self)

    @property
    def rgb(self) -> tuple[float, float, float]:
        return self._rgb

    @rgb.setter
    def rgb(self, new_rgb: tuple[NUMERIC, NUMERIC, NUMERIC]) -> None:
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
        # for func in self.callbacks:
        #     func(self)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        return self._rgb + (self._alpha,)

    @rgba.setter
    def rgba(
        self,
        new_rgba: tuple[NUMERIC, NUMERIC, NUMERIC, NUMERIC]
    ) -> None:
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
        # for func in self.callbacks:
        #     func(self)

    def blend(self,
              other_color: DynamicColor,
              mode: str = "multiply",
              in_place: bool = False,
              keep_alpha: bool = True) -> DynamicColor:
        """Blends one DynamicColor with another, treating the current color as
        the 'top' layer for non-commutative operations.
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
        """Defaults to euclidean distance.  If `weighted=True`, uses an
        approximation of human perception sometimes called 'redmean'.
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
        new_rgb = tuple(map(lambda v: 1 - v, self.rgb))
        if in_place:
            self.rgb = new_rgb
            if not keep_alpha:
                self.alpha = 1.0
            return self
        if keep_alpha:
            return DynamicColor(new_rgb + (self.alpha,))
        return DynamicColor(new_rgb)

    def properties(self) -> dict[str, Union[str, tuple[float, ...]]]:
        prop_dict = {
            "alpha": self.alpha,
            "hex_code": self.hex_code,
            "hsv": self.hsv,
            "name": self.name,
            "rgb": self.rgb
        }
        return prop_dict

    def __add__(self, other_color: DynamicColor) -> DynamicColor:
        return self.blend(other_color, mode="add")

    def __eq__(self, other_color: DynamicColor) -> bool:
        return self.difference(other_color) == 0.0

    def __ne__(self, other_color: DynamicColor) -> bool:
        return self.difference(other_color) != 0.0

    def __mul__(self, other_color: DynamicColor) -> DynamicColor:
        return self.blend(other_color, mode="multiply")

    def __repr__(self) -> str:
        return f"DynamicText({self.rgba})"

    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        return self.hex_code

    def __sub__(self, other_color: DynamicColor) -> DynamicColor:
        return self.blend(other_color, mode="subtract")

    def __truediv__(self, other_color: DynamicColor) -> DynamicColor:
        return self.blend(other_color, mode="divide")
