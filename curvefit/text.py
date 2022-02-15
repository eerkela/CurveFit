from __future__ import annotations
from typing import Union

import matplotlib as mpl

from curvefit import NUMERIC, NUMERIC_TYPECHECK, error_trace
from curvefit.callback import add_callback
from curvefit.color import DynamicColor


"""
TODO: Implement Sphinx documentation
TODO: if not visible, have getters return None
"""


def available_fonts() -> set[str]:
    # matplotlib.font_manager.findSystemFonts() is a bit greedy and often
    # returns fonts that cannot actually be used by
    # matplotlib.text.Text.set_fontfamily()
    available = set()
    for fpath in mpl.font_manager.findSystemFonts():
        try:
            font_family = mpl.font_manager.get_font(fpath).family_name
            font_prop = mpl.font_manager.FontProperties(font_family)
            mpl.font_manager.findfont(font_prop, fallback_to_default=False)
            available.add(font_family)
        except ValueError:
            continue
    return available


class DynamicText:

    def __init__(self, text_obj: mpl.text.Text, **kwargs):
        if not isinstance(text_obj, mpl.text.Text):
            err_msg = (f"[{error_trace(self)}] `text_obj` must be an instance "
                       f"of matplotlib.text.Text (received object of type: "
                       f"{type(text_obj)})")
            raise TypeError(err_msg)
        self.obj = text_obj
        # matplotlib.text.Text apparently doesn't have a get_linespacing method
        # see matplotlib.text.Text.set_linespacing if default changes in future
        self._line_spacing = 1.2  # matplotlib default value (02/07/2022)
        self._color = DynamicColor(self.obj.get_color())
        add_callback(self._color,
                     DynamicColor.callback_properties,
                     self.update_color)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def alpha(self) -> float:
        return self._color.alpha

    @alpha.setter
    def alpha(self, new_alpha: NUMERIC) -> None:
        self._color.alpha = new_alpha

    @property
    def autowrap(self) -> bool:
        return self.obj.get_wrap()

    @autowrap.setter
    def autowrap(self, new_wrap: bool) -> None:
        if not isinstance(new_wrap, bool):
            err_msg = (f"[{error_trace(self)}] `autowrap` must be a boolean "
                       f"(received object of type: {type(new_wrap)})")
            raise TypeError(err_msg)
        self.obj.set_wrap(new_wrap)
        self.obj.get_figure().tight_layout()

    @property
    def color(self) -> DynamicColor:
        return self._color

    @color.setter
    def color(
        self,
        new_color: Union[str, tuple[NUMERIC, ...], DynamicColor]) -> None:
        self._color.parse(new_color)

    @property
    def font(self) -> str:
        return self.obj.get_fontfamily()[0]  # should only ever have 1 font

    @font.setter
    def font(self, new_font: str) -> None:
        allowed = available_fonts()
        if not isinstance(new_font, str):
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[{error_trace(self)}] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}\n(received object of type: "
                       f"{type(new_font)})")
            raise TypeError(err_msg)
        if new_font not in allowed:
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[{error_trace(self)}] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}\n(received: {repr(new_font)})")
            raise ValueError(err_msg)
        self.obj.set_fontfamily(new_font)
        self.obj.get_figure().tight_layout()

    """TODO: replace *_alignment fields with generic alignment field"""
    @property
    def horizontal_alignment(self) -> str:
        return self.obj.get_horizontalalignment()

    @horizontal_alignment.setter
    def horizontal_alignment(self, new_horizontal_alignment: str) -> None:
        allowed = {"center", "right", "left"}
        if not isinstance(new_horizontal_alignment, str):
            err_msg = (f"[{error_trace(self)}] `horizontal_alignment` must be "
                       f"a string with one of the following values: {allowed} "
                       f"(received object of type: "
                       f"{type(new_horizontal_alignment)})")
            raise TypeError(err_msg)
        if new_horizontal_alignment not in allowed:
            err_msg = (f"[{error_trace(self)}] `horizontal_alignment` must be "
                       f"a string with one of the following values: {allowed} "
                       f"(received: {repr(new_horizontal_alignment)})")
            raise ValueError(err_msg)
        self.obj.set_horizontalalignment(new_horizontal_alignment)
        self.obj.get_figure().tight_layout()

    @property
    def rotation(self) -> float:
        return self.obj.get_rotation()

    @rotation.setter
    def rotation(self, new_rotation: NUMERIC) -> None:
        if not isinstance(new_rotation, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `rotation` must be a numeric "
                       f"representing the counterclockwise rotation angle in "
                       f"degrees (received object of type: "
                       f"{type(new_rotation)})")
            raise TypeError(err_msg)
        self.obj.set_rotation(new_rotation)
        self.obj.get_figure().tight_layout()

    @property
    def line_spacing(self) -> float:
        return self._line_spacing  # no get_linespacing() method

    @line_spacing.setter
    def line_spacing(self, new_line_spacing: NUMERIC) -> None:
        if not isinstance(new_line_spacing, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size` "
                       f"(received object of type: {type(new_line_spacing)})")
            raise TypeError(err_msg)
        if not new_line_spacing >= 1:
            err_msg = (f"[{error_trace(self)}] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size` "
                       f"(received: {repr(new_line_spacing)})")
            raise ValueError(err_msg)
        self._line_spacing = float(new_line_spacing)
        self.obj.set_linespacing(self._line_spacing)
        self.obj.get_figure().tight_layout()

    @property
    def position(self) -> tuple[float, float]:
        return self.obj.get_position()

    @position.setter
    def position(self, new_position: tuple[NUMERIC, NUMERIC]) -> None:
        if not isinstance(new_position, tuple):
            err_msg = (f"[{error_trace(self)}] `position` must be an `(x, y)` "
                       f"tuple of length 2 containing only numerics between 0 "
                       f"and 1 (received object of type: {type(new_position)})")
            raise TypeError(err_msg)
        if (len(new_position) != 2 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_position) or
            not all(0 <= v <= 1 for v in new_position)):
            err_msg = (f"[{error_trace(self)}] `position` must be an `(x, y)` "
                       f"tuple of length 2 containing only numerics between 0 "
                       f"and 1 (received: {repr(new_position)})")
            raise ValueError(err_msg)
        self.obj.set_position(new_position)
        self.obj.get_figure().tight_layout()

    @property
    def size(self) -> float:
        return self.obj.get_fontsize()

    @size.setter
    def size(self, new_size: NUMERIC) -> None:
        if not isinstance(new_size, NUMERIC_TYPECHECK):
            err_msg = (f"[{error_trace(self)}] `size` must be a numeric > 0 "
                       f"(received object of type: {type(new_size)})")
            raise TypeError(err_msg)
        if not new_size > 0:
            err_msg = (f"[{error_trace(self)}] `size` must be a numeric > 0 "
                       f"(received: {repr(new_size)})")
            raise ValueError(err_msg)
        self.obj.set_fontsize(new_size)
        self.obj.get_figure().tight_layout()

    @property
    def text(self) -> str:
        """Return figure title (not related to any subplot)."""
        return self.obj.get_text()

    @text.setter
    def text(self, new_text: str) -> None:
        """Set figure title (not related to any subplot)."""
        if not isinstance(new_text, str):
            err_msg = (f"[{error_trace(self)}] `text` must be a string "
                       f"(received object of type: {type(new_text)})")
            raise TypeError(err_msg)
        self.obj.set_text(new_text)

    @property
    def vertical_alignment(self) -> str:
        return self.obj.get_verticalalignment()

    @vertical_alignment.setter
    def vertical_alignment(self, new_vertical_alignment: str) -> None:
        allowed = {"center", "top", "bottom", "baseline", "center_baseline"}
        if not isinstance(new_vertical_alignment, str):
            err_msg = (f"[{error_trace(self)}] `vertical_alignment` must be a "
                       f"string with one of the following values: {allowed} "
                       f"(received object of type: "
                       f"{type(new_vertical_alignment)})")
            raise TypeError(err_msg)
        if new_vertical_alignment not in allowed:
            err_msg = (f"[{error_trace(self)}] `vertical_alignment` must be a "
                       f"string with one of the following values: {allowed} "
                       f"(received: {repr(new_vertical_alignment)})")
            raise ValueError(err_msg)
        self.obj.set_verticalalignment(new_vertical_alignment)
        self.obj.get_figure().tight_layout()

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
        self.obj.get_figure().tight_layout()

    @property
    def weight(self) -> str:
        return self.obj.get_fontweight()

    @weight.setter
    def weight(self, new_weight: str) -> None:
        allowed = {"ultralight", "light", "normal", "regular", "book", "medium",
                   "roman", "semibold", "demibold", "demi", "bold", "heavy",
                   "extra bold", "black"}
        if not isinstance(new_weight, str):
            err_msg = (f"[{error_trace(self)}] `weight` must be a string with "
                       f"one of the following values: {allowed} (received "
                       f"object of type: {type(new_weight)}")
            raise TypeError(err_msg)
        if new_weight not in allowed:
            err_msg = (f"[{error_trace(self)}] `weight` must be a string with "
                       f"one of the following values: {allowed} (received: "
                       f"{repr(new_weight)})")
            raise ValueError(err_msg)
        self.obj.set_fontweight(new_weight)
        self.obj.get_figure().tight_layout()

    def properties(
        self) -> dict[str, Union[str, NUMERIC, bool, tuple[NUMERIC, ...]]]:
        prop_dict = {
            "alpha": self.alpha,
            "autowrap": self.autowrap,
            "color": self.color,
            "font": self.font,
            "horizontal_alignment": self.horizontal_alignment,
            "rotation": self.rotation,
            "line_spacing": self.line_spacing,
            "position": self.position,
            "size": self.size,
            "text": self.text,
            "vertical_alignment": self.vertical_alignment,
            "visible": self.visible,
            "weight": self.weight
        }
        return prop_dict

    def update_color(self, color: DynamicColor) -> None:
        self.obj.set_color(color.rgba)

    def __repr__(self) -> str:
        props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
        return f"DynamicText({repr(self.obj)}, {', '.join(props)})"

    def __str__(self) -> str:
        return self.text
