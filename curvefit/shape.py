from __future__ import annotations
from typing import Union

import matplotlib as mpl

from . import NUMERIC, NUMERIC_TYPECHECK, error_trace


"""
TODO: Implement Sphinx documentation
"""


class DynamicPatch:

    def __init__(self, patch_obj: mpl.patches.Patch, **kwargs):
        if not issubclass(type(patch_obj), mpl.patches.Patch):
            err_msg = (f"[{error_trace(self)}] `patch_obj` must be an "
                       f"instance/subclass of matplotlib.patches.Patch "
                       f"(received  object of type: {type(patch_obj)})")
            raise TypeError(err_msg)
        self.obj = patch_obj
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def border_alpha(self) -> float:
        return self.obj.get_edgecolor()[-1]

    @border_alpha.setter
    def border_alpha(self, new_alpha: NUMERIC) -> None:
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `border_alpha` must be a "
                       f"numeric between 0 and 1 (received object of type: "
                       f"{type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[{error_trace(self)}] `border_alpha` must be a "
                       f"numeric between 0 and 1 (received: {new_alpha})")
            raise ValueError(err_msg)
        self.obj.set_edgecolor(self.border_color + (new_alpha,))

    @property
    def border_color(self) -> tuple[float, float, float]:
        # matplotlib.colors.to_rgb converts named colors, drops alpha channel
        return mpl.colors.to_rgb(self.obj.get_edgecolor())

    @border_color.setter
    def border_color(
        self,
        new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
    ) -> None:
        if not isinstance(new_color, (str, tuple)):
            err_msg = (f"[{error_trace(self)}] `border_color` must be either "
                       f"a string specifying a named color or a tuple of "
                       f"numeric RGB values between 0 and 1 (received "
                       f"object of type: {type(new_color)})")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[{error_trace(self)}] `border_color` must be "
                           f"either a string specifying a named color or a "
                           f"tuple of numeric RGB values between 0 and 1 "
                           f"(received: {new_color})")
                raise ValueError(err_msg)
            self.obj.set_edgecolor(new_color + (self.border_alpha,))
        else:
            self.obj.set_edgecolor(new_color)

    @property
    def border_style(self) -> str:
        return self.obj.get_linestyle()

    @border_style.setter
    def border_style(self, new_style: str) -> None:
        # allowed values can be found at matplotlib.patches.Patch.set_linestyle
        allowed = {"-", "solid", "--", "dashed", "-.", "dashdot", ":",
                   "dotted", "none", "None", " ", ""}
        if not isinstance(new_style, str):
            err_msg = (f"[{error_trace(self)}] `border_style` must be a "
                       f"string with one of the following values: {allowed} "
                       f"(received object of type: {type(new_style)})")
            raise TypeError(err_msg)
        if new_style not in allowed:
            err_msg = (f"[{error_trace(self)}] `border_style` must be a "
                       f"string with one of the following values: {allowed} "
                       f"(received: {new_style})")
            raise ValueError(err_msg)
        self.obj.set_linestyle(new_style)

    @property
    def border_width(self) -> float:
        return self.obj.get_linewidth()

    @border_width.setter
    def border_width(self, new_width: NUMERIC) -> None:
        if not isinstance(new_width, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `border_width` must be a "
                       f"numeric value >= 0 (received object of type: "
                       f"{type(new_width)})")
            raise TypeError(err_msg)
        if new_width < 0:
            err_msg = (f"[{error_trace(self)}] `border_width` must be a "
                       f"numeric value >= 0 (received: {new_width})")
            raise ValueError(err_msg)
        self.obj.set_linewidth(new_width)

    @property
    def face_alpha(self) -> float:
        return self.obj.get_facecolor()[-1]

    @face_alpha.setter
    def face_alpha(self, new_alpha: NUMERIC) -> None:
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `face_alpha` must be a numeric "
                       f"between 0 and 1 (received object of type: "
                       f"{type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[{error_trace(self)}] `face_alpha` must be a numeric "
                       f"between 0 and 1 (received: {new_alpha})")
            raise ValueError(err_msg)
        self.obj.set_facecolor(self.face_color + (new_alpha,))

    @property
    def face_color(self) -> tuple[float, float, float]:
        # matplotlib.colors.to_rgb converts named colors, drops alpha channel
        return mpl.colors.to_rgb(self.obj.get_facecolor())

    @face_color.setter
    def face_color(
        self,
        new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
    ) -> None:
        if not isinstance(new_color, (str, tuple)):
            err_msg = (f"[{error_trace(self)}] `face_color` must be either a "
                       f"string specifying a named color or a tuple of "
                       f"numeric RGB values between 0 and 1 (received object "
                       f"of type: {type(new_color)})")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[{error_trace(self)}] `face_color` must be "
                           f"either  a string specifying a named color or a "
                           f"tuple of numeric RGB values between 0 and 1 "
                           f"(received: {new_color})")
                raise ValueError(err_msg)
            self.obj.set_facecolor(new_color + (self.face_alpha,))
        else:
            self.obj.set_facecolor(new_color)

    @property
    def hatch(self) -> str:
        return self.obj.get_hatch()

    @hatch.setter
    def hatch(self, new_hatch: str) -> None:
        """
        hatch values (from matplotlib.patches.Rectangle.set_hatch):
            /    - diagonal hatching
            \\   - back diagonal
            -    - horizontal
            +    - crossed
            x    - crossed diagonal
            o    - small circle
            O    - large circle
            .    - dots
            *    - stars

        Letters can be combined to mix styles.  Repeating the same symbol
        increases its density.

        Only supported in the PostScript, PDF, SVG, and Agg backends.
        """
        allowed = {"/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"}
        if not isinstance(new_hatch, str):
            err_msg = (f"[{error_trace(self)}] `hatch` must be a string with "
                       f"one or more of the following values: {allowed} "
                       f"(received object of type: {type(new_hatch)})")
            raise TypeError(err_msg)
        if not all(v in allowed for v in new_hatch):
            err_msg = (f"[{error_trace(self)}] `hatch` must be a string with "
                       f"one or more of the following values: {allowed} "
                       f"(received: {new_hatch})")
            raise ValueError(err_msg)
        self.obj.set_hatch(new_hatch)

    @property
    def visible(self) -> bool:
        return self.obj.get_visible()

    @visible.setter
    def visible(self, new_visible: bool) -> None:
        if not isinstance(new_visible, bool):
            err_msg = (f"[{error_trace(self)}] `visible` must be a boolean "
                       f"(received object of type: {type(new_visible)})")
            raise TypeError(err_msg)
        self.obj.set_visible(new_visible)


class DynamicRectangle(DynamicPatch):

    def __init__(self, rect_obj: mpl.patches.Rectangle, **kwargs):
        if not isinstance(rect_obj, mpl.patches.Rectangle):
            err_msg = (f"[{error_trace(self)}] `rect_obj` must be an instance "
                       f"of matplotlib.patches.Rectangle (received object of "
                       f"type: {type(rect_obj)})")
            raise TypeError(err_msg)
        super().__init__(rect_obj, **kwargs)

    @property
    def anchor(self) -> tuple[float, float]:
        return self.obj.get_xy()

    @anchor.setter
    def anchor(self, new_anchor: tuple[NUMERIC, NUMERIC]) -> None:
        if not isinstance(new_anchor, tuple):
            err_msg = (f"[{error_trace(self)}] `anchor` must be a length 2 "
                       f"tuple `(x, y)` of numerics (received object of type: "
                       f"{type(new_anchor)})")
            raise TypeError(err_msg)
        # if  # value check
        self.obj.set_xy(new_anchor)

    @property
    def height(self) -> float:
        return self.obj.get_height()

    @height.setter
    def height(self, new_height: NUMERIC) -> None:
        if not isinstance(new_height, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `height` must be a numeric "
                       f"!= 0 (received object of type: {type(new_height)})")
            raise TypeError(err_msg)
        if new_height == 0:
            err_msg = (f"[{error_trace(self)}] `height` must be a numeric "
                       f"!= 0 (received: {new_height})")
            raise ValueError(err_msg)
        self.obj.set_height(new_height)

    @property
    def rotation(self) -> float:
        return self.obj.get_angle()

    @rotation.setter
    def rotation(self, new_rotation: NUMERIC) -> None:
        if not isinstance(new_rotation, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `rotation` must be a numeric "
                       f"(received object of type: {type(new_rotation)})")
            raise TypeError(err_msg)
        self.obj.set_angle(new_rotation)

    @property
    def width(self) -> float:
        return self.obj.get_width()

    @width.setter
    def width(self, new_width: NUMERIC) -> None:
        if not isinstance(new_width, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `width` must be a numeric != 0 "
                       f"(received object of type: {type(new_width)})")
            raise TypeError(err_msg)
        if new_width == 0:
            err_msg = (f"[{error_trace(self)}] `width` must be a numeric != 0 "
                       f"(received: {new_width})")
            raise ValueError(err_msg)
        self.obj.set_width(new_width)

    def properties(
        self
    ) -> dict[str, Union[str, NUMERIC, bool, tuple[NUMERIC, ...]]]:
        prop_dict = {
            "anchor": self.anchor,
            "border_alpha": self.border_alpha,
            "border_color": self.border_color,
            "border_style": self.border_style,
            "border_width": self.border_width,
            "face_alpha": self.face_alpha,
            "face_color": self.face_color,
            "hatch": self.hatch,
            "height": self.height,
            "rotation": self.rotation,
            "width": self.width
        }
        return prop_dict

    def __repr__(self) -> str:
        props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
        return f"DynamicRectangle({repr(self.obj)}, {', '.join(props)})"

    def __str__(self) -> str:
        return (f"DynamicRectangle: {self.anchor} + ({self.width}, "
                f"{self.height}), RGB color: {self.face_color}")
