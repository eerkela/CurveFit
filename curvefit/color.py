from __future__ import annotations
from collections import defaultdict
from math import sqrt
from string import hexdigits
from typing import Optional, Union

import matplotlib as mpl

from . import NUMERIC, NUMERIC_TYPECHECK, error_trace


"""
TODO: Implement Sphinx documentation
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
                 color_spec: str = "rgb"):
        if not isinstance(color, (str, tuple)):
            err_msg = (f"[{error_trace(self)}] `color` must be a string "
                       f"referencing a named color ('white') or hex code of "
                       f"the form '#rrggbb[aa]', or a tuple of numeric values "
                       f"between 0 and 1, representing either an `(r, g, b)`, "
                       f"`(h, s, v)` or `(r, g, b, a)` color specification"
                       f"(received object of type: {type(color)})")
            raise TypeError(err_msg)
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
                self.named_color = color
            else:
                self.hex_code = color

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
        self._hex_code = new_hex
        self._rgb = mpl.colors.to_rgb(self._hex_code)
        self._rgba = mpl.colors.to_rgba(self._hex_code)
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code[:7] in COLORS_NAMED:
            self._named_color = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._named_color = None

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
        self._rgba = self._rgb + (1.0,)
        self._hex_code = mpl.colors.to_hex(self._rgb)
        if self._hex_code in COLORS_NAMED:
            self._named_color = COLORS_NAMED[self._hex_code][0]
        else:
            self._named_color = None

    @property
    def named_color(self) -> Optional[str]:
        return self._named_color

    @named_color.setter
    def named_color(self, new_color: str) -> None:
        if not isinstance(new_color, str):
            err_msg = (f"[{error_trace(self)}] `named_color` must be a "
                       f"string referencing a key in `NAMED_COLORS` "
                       f"(received object of type: {type(new_color)})")
            raise TypeError(err_msg)
        if new_color not in NAMED_COLORS:
            err_msg = (f"[{error_trace(self)}] `named_color` must be a "
                       f"string referencing a key in `NAMED_COLORS` "
                       f"(received: {repr(new_color)})")
            raise ValueError(err_msg)
        self._named_color = new_color
        self._hex_code = NAMED_COLORS[self._named_color]
        self._rgb = mpl.colors.to_rgb(self._hex_code)
        self._rgba = self._rgb + (1.0,)
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))

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
        self._rgba = self._rgb + (1.0,)
        self._hex_code = mpl.colors.to_hex(self._rgb)
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code in COLORS_NAMED:
            self._named_color = COLORS_NAMED[self._hex_code][0]
        else:
            self._named_color = None

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        return self._rgba

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
        self._rgba = new_rgba
        alpha = self._rgba[-1]
        self._rgb = self._rgba[:-1]
        self._hex_code = mpl.colors.to_hex(self._rgb) + hex(int(alpha * 255))
        self._hsv = tuple(mpl.colors.rgb_to_hsv(self._rgb))
        if self._hex_code[:7] in COLORS_NAMED:
            self._named_color = COLORS_NAMED[self._hex_code[:7]][0]
        else:
            self._named_color = None

    def blend(self,
              other_color: DynamicColor,
              mode: str = "multiply"
    ) -> DynamicColor:
        raise NotImplementedError()

    def difference(self,
        other_color: DynamicColor,
        mode: str = "euclidean"
    ) -> float:
        raise NotImplementedError()

    def properties(self) -> dict[str, Union[str, tuple[float, ...]]]:
        raise NotImplementedError()

    def __repr__(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()
