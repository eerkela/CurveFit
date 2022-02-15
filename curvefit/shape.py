from __future__ import annotations
from typing import Union

import matplotlib as mpl

from curvefit import NUMERIC, NUMERIC_TYPECHECK, error_trace
from curvefit.callback import add_callback
from curvefit.color import DynamicColor


"""
TODO: Implement Sphinx documentation
TODO: allow DynamicPatch/DynamicRectangle to accept border_*/face_* kwargs
TODO: change properties() to display these ^
"""


class DynamicPatch:

    def __init__(self, patch_obj: mpl.patches.Patch, **kwargs):
        if not issubclass(type(patch_obj), mpl.patches.Patch):
            err_msg = (f"[{error_trace(self)}] `patch_obj` must be an "
                       f"instance/subclass of matplotlib.patches.Patch "
                       f"(received  object of type: {type(patch_obj)})")
            raise TypeError(err_msg)
        self.obj = patch_obj
        self._border = DynamicPatch.Border(self)
        self._face = DynamicPatch.Face(self)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def border(self) -> DynamicPatch.Border:
        return self._border

    @property
    def face(self) -> DynamicPatch.Face:
        return self._face

    @property
    def fill(self) -> bool:
        return self.obj.get_fill()

    @fill.setter
    def fill(self, new_fill: bool) -> None:
        if not isinstance(new_fill, bool):
            err_msg = (f"[{error_trace(self)}] `fill` must be a boolean "
                       f"(received object of type: {type(new_fill)})")
            raise TypeError(err_msg)
        self.obj.set_fill(new_fill)

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

    def properties(self):
        prop_dict = {
            "fill": self.fill,
            "visible": self.visible
        }
        return prop_dict

    def __repr__(self) -> str:
        props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
        return f"DynamicPatch({repr(self.obj)}, {', '.join(props)})"

    class Border:

        def __init__(self, parent: DynamicPatch):
            if not issubclass(type(parent), DynamicPatch):
                err_msg = (f"[{error_trace(self)}] `parent` must be an "
                           f"instance/subclass of DynamicPatch (received "
                           f"object of type: {type(parent)})")
                raise TypeError(err_msg)
            self.parent = parent
            self._color = DynamicColor(self.parent.obj.get_edgecolor())
            add_callback(self._color,
                         DynamicColor.callback_properties,
                         self.update_color)

        @property
        def alpha(self) -> float:
            return self._color.alpha

        @alpha.setter
        def alpha(self, new_alpha: NUMERIC) -> None:
            self._color.alpha = new_alpha

        @property
        def color(self) -> DynamicColor:
            return self._color

        @color.setter
        def color(
            self,
            new_color: Union[str, tuple[NUMERIC, ...], DynamicColor]) -> None:
            self._color.parse(new_color)

        @property
        def style(self) -> str:
            return self.parent.obj.get_linestyle()

        @style.setter
        def style(self, new_style: str) -> None:
            # allowed values found at matplotlib.patches.Patch.set_linestyle
            allowed = {"-", "solid", "--", "dashed", "-.", "dashdot", ":",
                       "dotted", "none", "None", " ", ""}
            if not isinstance(new_style, str):
                err_msg = (f"[{error_trace(self.parent, self)}] `style` must "
                           f"be a string with one of the following values: "
                           f"{allowed} (received object of type: "
                           f"{type(new_style)})")
                raise TypeError(err_msg)
            if new_style not in allowed:
                err_msg = (f"[{error_trace(self.parent, self)}] `style` must "
                           f"be a string with one of the following values: "
                           f"{allowed} (received: {new_style})")
                raise ValueError(err_msg)
            self.parent.obj.set_linestyle(new_style)

        @property
        def width(self) -> float:
            return self.parent.obj.get_linewidth()

        @width.setter
        def width(self, new_width: NUMERIC) -> None:
            if not isinstance(new_width, NUMERIC_TYPECHECK):
                err_msg = (f"[{error_trace(self.parent, self)}] `width` must "
                           f"be a numeric value >= 0 (received object of "
                           f"type: {type(new_width)})")
                raise TypeError(err_msg)
            if new_width < 0:
                err_msg = (f"[{error_trace(self.parent, self)}] `width` must "
                           f"be a numeric value >= 0 (received: {new_width})")
                raise ValueError(err_msg)
            self.parent.obj.set_linewidth(new_width)

        def properties(self):
            prop_dict = {
                "alpha": self.alpha,
                "color": self.color,
                "style": self.style,
                "width": self.width
            }
            return prop_dict

        def update_color(self, color: DynamicColor) -> None:
            self.parent.obj.set_edgecolor(color.rgba)

        def __repr__(self) -> str:
            props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
            return (f"DynamicPatch.Border({repr(self.parent)}, "
                    f"{', '.join(props)})")

    class Face:

        def __init__(self, parent: DynamicPatch):
            if not issubclass(type(parent), DynamicPatch):
                err_msg = (f"[{error_trace(self)}] `parent` must be an "
                           f"instance/subclass of DynamicPatch (received "
                           f"object of type: {type(parent)})")
                raise TypeError(err_msg)
            self.parent = parent
            self._color = DynamicColor(self.parent.obj.get_facecolor())
            add_callback(self._color,
                         DynamicColor.callback_properties,
                         self.update_color)

        @property
        def alpha(self) -> float:
            return self._color.alpha

        @alpha.setter
        def alpha(self, new_alpha: NUMERIC) -> None:
            self._color.alpha = new_alpha

        @property
        def color(self) -> DynamicColor:
            return self._color

        @color.setter
        def color(
            self,
            new_color: Union[str, tuple[NUMERIC, ...], DynamicColor]) -> None:
            self._color.parse(new_color)

        @property
        def hatch(self) -> str:
            return self.parent.obj.get_hatch()

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
                err_msg = (f"[{error_trace(self.parent, self)}] `hatch` must "
                           f"be a string with one or more of the following "
                           f"values: {allowed} (received object of type: "
                           f"{type(new_hatch)})")
                raise TypeError(err_msg)
            if not all(v in allowed for v in new_hatch):
                err_msg = (f"[{error_trace(self.parent, self)}] `hatch` must "
                           f"be a string with one or more of the following "
                           f"values: {allowed} (received: {new_hatch})")
                raise ValueError(err_msg)
            self.parent.obj.set_hatch(new_hatch)

        def properties(self):
            prop_dict = {
                "alpha": self.alpha,
                "color": self.color,
                "hatch": self.hatch
            }
            return prop_dict

        def update_color(self, color: DynamicColor) -> None:
            self.parent.obj.set_facecolor(color.rgba)

        def __repr__(self) -> str:
            props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
            return (f"DynamicPatch.Face({repr(self.parent)}, "
                    f"{', '.join(props)})")


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
                       f"tuple `(x, y)` of numerics between 0 and 1 (received "
                       f"object of type: {type(new_anchor)})")
            raise TypeError(err_msg)
        if (len(new_anchor) != 2 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_anchor) or
            not all(0 <= v <= 1 for v in new_anchor)):
            err_msg = (f"[{error_trace(self)}] `anchor` must be a length 2 "
                       f"tuple `(x, y)` of numerics between 0 and 1 "
                       f"(received: {new_anchor})")
            raise ValueError(err_msg)
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
                f"{self.height}), RGB color: {self.face.color}")
