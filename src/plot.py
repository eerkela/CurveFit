from __future__ import annotations
from math import ceil, sqrt
from pathlib import Path
from typing import Optional, Union

import matplotlib as mpl
from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt

"""
TODO: Implement Sphinx documentation
"""


NUMERIC = Union[int, float]
NUMERIC_TYPECHECK = (int, float)


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


def color_diff(rgb1: tuple[NUMERIC, NUMERIC, NUMERIC],
               rgb2: tuple[NUMERIC, NUMERIC, NUMERIC]) -> float:
    return sqrt(sum([(v1 - v2)**2 for v1, v2 in zip(rgb1, rgb2)]))


class DynamicText:

    def __init__(self, text_obj: mpl.text.Text, **kwargs):
        if not isinstance(text_obj, mpl.text.Text):
            err_msg = (f"[DynamicText.__init__] `text_obj` must be an "
                       f"instance of matplotlib.text.Text (received object of "
                       f"type: {type(text_obj)})")
            raise TypeError(err_msg)
        self.obj = text_obj
        # matplotlib.text.Text apparently doesn't have a get_linespacing method
        # see matplotlib.text.Text.set_linespacing if default changes in future
        self._line_spacing = 1.2  # matplotlib default value (02/07/2022)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def alpha(self) -> float:
        result = self.obj.get_alpha()
        if result is None:
            return 1.0
        return result

    @alpha.setter
    def alpha(self, new_alpha: NUMERIC) -> None:
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicText.alpha] `alpha` must be a numeric "
                       f"between 0 and 1 (received object of type: "
                       f"{type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[DynamicText.alpha] `alpha` must be a numeric "
                       f"between 0 and 1 (received: {new_alpha})")
            raise ValueError(err_msg)
        self.obj.set_alpha(new_alpha)

    @property
    def autowrap(self) -> bool:
        return self.obj.get_wrap()

    @autowrap.setter
    def autowrap(self, new_wrap: bool) -> None:
        if not isinstance(new_wrap, bool):
            err_msg = (f"[DynamicText.autowrap] `autowrap` must be a boolean "
                       f"(received object of type: {type(new_wrap)})")
            raise TypeError(err_msg)
        self.obj.set_wrap(new_wrap)
        self.obj.get_figure().tight_layout()

    @property
    def color(self) -> tuple[float, float, float]:
        # matplotlib.colors.to_rgb converts named colors, drops alpha channel
        return mpl.colors.to_rgb(self.obj.get_color())

    @color.setter
    def color(
        self, new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
    ) -> None:
        if not isinstance(new_color, (str, tuple)):
            err_msg = (f"[DynamicText.color] `color` must be either a string "
                       f"specifying a named color or a tuple of numeric RGB "
                       f"values between 0 and 1 (received object of type: "
                       f"{type(new_color)})")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[DynamicText.color] when passing RGB values, "
                           f"`color` must be a length 3 tuple containing "
                           f"floats between 0 and 1 (received: {new_color})")
                raise ValueError(err_msg)
            self.obj.set_color(new_color + (self.alpha,))
        else:
            self.obj.set_color(new_color)

    @property
    def font(self) -> str:
        return self.obj.get_fontfamily()[0]  # should only ever have 1 font

    @font.setter
    def font(self, new_font: str) -> None:
        allowed = available_fonts()
        if not isinstance(new_font, str):
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[DynamicText.font] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}\n(received object of type: "
                       f"{type(new_font)})")
            raise TypeError(err_msg)
        if new_font not in allowed:
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[DynamicText.font] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}\n(received: '{new_font}')")
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
            err_msg = (f"[DynamicText.horizontal_alignment] "
                       f"`horizontal_alignment` must be a string with one of "
                       f"the following values: {allowed} (received object of "
                       f"type: {type(new_horizontal_alignment)})")
            raise TypeError(err_msg)
        if new_horizontal_alignment not in allowed:
            err_msg = (f"[DynamicText.horizontal_alignment] "
                       f"`horizontal_alignment` must be a string with one of "
                       f"the following values: {allowed} (received: "
                       f"'{new_horizontal_alignment}')")
            raise ValueError(err_msg)
        self.obj.set_horizontalalignment(new_horizontal_alignment)
        self.obj.get_figure().tight_layout()

    @property
    def rotation(self) -> float:
        return self.obj.get_rotation()

    @rotation.setter
    def rotation(self, new_rotation: NUMERIC) -> None:
        if not isinstance(new_rotation, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicText.rotation] `rotation` must be a numeric "
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
            err_msg = (f"[DynamicText.line_spacing] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size` "
                       f"(received object of type: {type(new_line_spacing)})")
            raise TypeError(err_msg)
        if not new_line_spacing >= 1:
            err_msg = (f"[DynamicText.line_spacing] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size` "
                       f"(received: {new_line_spacing})")
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
            err_msg = (f"[DynamicText.position] `position` must be an "
                       f"`(x, y)` tuple of length 2 containing only numerics "
                       f"between 0 and 1 (received object of type: "
                       f"{type(new_position)})")
            raise TypeError(err_msg)
        if (len(new_position) != 2 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_position) or
            not all(0 <= v <= 1 for v in new_position)):
            err_msg = (f"[DynamicText.position] `position` must be an "
                       f"`(x, y)` tuple of length 2 containing only numerics "
                       f"between 0 and 1 (received: {new_position})")
            raise ValueError(err_msg)
        self.obj.set_position(new_position)
        self.obj.get_figure().tight_layout()

    @property
    def size(self) -> float:
        return self.obj.get_fontsize()

    @size.setter
    def size(self, new_size: NUMERIC) -> None:
        if not isinstance(new_size, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicText.size] `size` must be a numeric > 0 "
                       f"(received object of type: {type(new_size)})")
            raise TypeError(err_msg)
        if not new_size > 0:
            err_msg = (f"[DynamicText.size] `size` must be a numeric > 0 "
                       f"(received: {new_size})")
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
            err_msg = (f"[DynamicText.text] `text` must be a string (received "
                       f"object of type: {type(new_text)})")
            raise TypeError(err_msg)
        self.obj.set_text(new_text)

    @property
    def vertical_alignment(self) -> str:
        return self.obj.get_verticalalignment()

    @vertical_alignment.setter
    def vertical_alignment(self, new_vertical_alignment: str) -> None:
        allowed = {"center", "top", "bottom", "baseline", "center_baseline"}
        if not isinstance(new_vertical_alignment, str):
            err_msg = (f"[DynamicText.vertical_alignment] `vertical_alignment` "
                       f"must be a string with one of the following values: "
                       f"{allowed} (received object of type: "
                       f"{type(new_vertical_alignment)})")
            raise TypeError(err_msg)
        if new_vertical_alignment not in allowed:
            err_msg = (f"[DynamicText.vertical_alignment] `vertical_alignment` "
                       f"must be a string with one of the following values: "
                       f"{allowed} (received: '{new_vertical_alignment}')")
            raise ValueError(err_msg)
        self.obj.set_verticalalignment(new_vertical_alignment)
        self.obj.get_figure().tight_layout()

    @property
    def visible(self) -> bool:
        return self.obj.get_visible()

    @visible.setter
    def visible(self, new_visible: bool) -> None:
        if not isinstance(new_visible, bool):
            err_msg = (f"[DynamicText.visible] `visible` must be a boolean "
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
            err_msg = (f"[DynamicText.weight] `weight` must be a string with "
                       f"one of the following values: {allowed} (received "
                       f"object of type: {type(new_weight)}")
            raise TypeError(err_msg)
        if new_weight not in allowed:
            err_msg = (f"[DynamicText.weight] `weight` must be a string with "
                       f"one of the following values: {allowed} (received: "
                       f"'{new_weight}')")
            raise ValueError(err_msg)
        self.obj.set_fontweight(new_weight)
        self.obj.get_figure().tight_layout()

    def invert_color(self) -> None:
        self.color = tuple(map(lambda v: 1 - v, self.color))

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

    def __repr__(self) -> str:
        props = [f"{k}={repr(v)}" for k, v in self.properties().items()]
        return f"DynamicText({repr(self.obj)}, {', '.join(props)})"

    def __str__(self) -> str:
        return self.text


class DynamicRectangle:

    def __init__(self, rect_obj: mpl.patches.Rectangle, **kwargs):
        if not isinstance(rect_obj, mpl.patches.Rectangle):
            err_msg = (f"[DynamicRectangle.__init__] `rect_obj` must be an "
                       f"instance of matplotlib.patches.Rectangle (received "
                       f"{type(rect_obj)} instead)")
            raise TypeError(err_msg)
        self.obj = rect_obj
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def anchor(self) -> tuple[float, float]:
        return self.obj.get_xy()

    @anchor.setter
    def anchor(self, new_anchor: tuple[NUMERIC, NUMERIC]) -> None:
        if not isinstance(new_anchor, tuple):
            err_msg = (f"[DynamicRectangle.anchor] `anchor` must be a length "
                       f"2 tuple `(x, y)` of numerics (received object of "
                       f"type: {type(new_anchor)})")
            raise TypeError(err_msg)
        # if  # value check
        self.obj.set_xy(new_anchor)

    @property
    def border_alpha(self) -> float:
        return self.obj.get_edgecolor()[-1]

    @border_alpha.setter
    def border_alpha(self, new_alpha: NUMERIC) -> None:
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.border_alpha] `border_alpha` must "
                       f"be a numeric between 0 and 1 (received object of "
                       f"type: {type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[DynamicRectangle.border_alpha] `border_alpha` must "
                       f"be a numeric between 0 and 1 (received: {new_alpha})")
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
            err_msg = (f"[DynamicRectangle.border_color] `border_color` must "
                       f"be either a string specifying a named color or a "
                       f"tuple of numeric RGB values between 0 and 1 "
                       f"(received object of type: {type(new_color)})")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[DynamicRectangle.border_color] `border_color` "
                           f"must be either a string specifying a named color "
                           f"or a tuple of numeric RGB values between 0 and 1 "
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
            err_msg = (f"[DynamicRectangle.border_style] `border_style` must "
                       f"be a string with one of the following values: "
                       f"{allowed} (received object of type: "
                       f"{type(new_style)})")
            raise TypeError(err_msg)
        if new_style not in allowed:
            err_msg = (f"[DynamicRectangle.border_style] `border_style` must "
                       f"be a string with one of the following values: "
                       f"{allowed} (received: {new_style})")
            raise ValueError(err_msg)
        self.obj.set_linestyle(new_style)

    @property
    def border_width(self) -> float:
        return self.obj.get_linewidth()

    @border_width.setter
    def border_width(self, new_width: NUMERIC) -> None:
        if not isinstance(new_width, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.border_width] `border_width` must "
                       f"be a numeric value >= 0 (received object of type: "
                       f"{type(new_width)})")
            raise TypeError(err_msg)
        if new_width < 0:
            err_msg = (f"[DynamicRectangle.border_width] `border_width` must "
                       f"be a numeric value >= 0 (received: {new_width})")
            raise ValueError(err_msg)
        self.obj.set_linewidth(new_width)

    @property
    def face_alpha(self) -> float:
        return self.obj.get_facecolor()[-1]

    @face_alpha.setter
    def face_alpha(self, new_alpha: NUMERIC) -> None:
        if not isinstance(new_alpha, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.face_alpha] `face_alpha` must be a "
                       f"numeric between 0 and 1 (received object of type: "
                       f"{type(new_alpha)})")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[DynamicRectangle.face_alpha] `face_alpha` must be a "
                       f"numeric between 0 and 1 (received: {new_alpha})")
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
            err_msg = (f"[DynamicRectangle.face_color] `face_color` must be "
                       f"either a string specifying a named color or a tuple "
                       f"of numeric RGB values between 0 and 1 (received "
                       f"object of type: {type(new_color)})")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[DynamicRectangle.face_color] `face_color` must "
                           f"be either a string specifying a named color or a "
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
            err_msg = (f"[DynamicRectangle.hatch] `hatch` must be a string "
                       f"with one or more of the following values: {allowed} "
                       f"(received object of type: {type(new_hatch)})")
            raise TypeError(err_msg)
        if not all(v in allowed for v in new_hatch):
            err_msg = (f"[DynamicRectangle.hatch] `hatch` must be a string "
                       f"with one or more of the following values: {allowed} "
                       f"(received: {new_hatch})")
            raise ValueError(err_msg)
        self.obj.set_hatch(new_hatch)

    @property
    def height(self) -> float:
        return self.obj.get_height()

    @height.setter
    def height(self, new_height: NUMERIC) -> None:
        if not isinstance(new_height, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.height] `height` must be a numeric "
                       f"!= 0 (received object of type: {type(new_height)})")
            raise TypeError(err_msg)
        if new_height == 0:
            err_msg = (f"[DynamicRectangle.height] `height` must be a numeric "
                       f"!= 0 (received: {new_height})")
            raise ValueError(err_msg)
        self.obj.set_height(new_height)

    @property
    def rotation(self) -> float:
        return self.obj.get_angle()

    @rotation.setter
    def rotation(self, new_rotation: NUMERIC) -> None:
        if not isinstance(new_rotation, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.rotation] `rotation` must be a "
                       f"numeric (received object of type: "
                       f"{type(new_rotation)})")
            raise TypeError(err_msg)
        self.obj.set_angle(new_rotation)

    @property
    def width(self) -> float:
        return self.obj.get_width()

    @width.setter
    def width(self, new_width: NUMERIC) -> None:
        if not isinstance(new_width, NUMERIC_TYPECHECK):
            err_msg = (f"[DynamicRectangle.width] `width` must be a numeric "
                       f"!= 0 (received object of type: {type(new_width)})")
            raise TypeError(err_msg)
        if new_width == 0:
            err_msg = (f"[DynamicRectangle.width] `width` must be a numeric "
                       f"!= 0 (received: {new_width})")
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


class DynamicFigure:

    # DEFAULTS
    observed_labels: set = set()
    color_cutoff: float = 0.4  # invert text color below this difference cutoff
    horizontal_size_cutoff_medium: float = 6.4  # resize text below this width
    horizontal_size_cutoff_small: float = 3.2  #  ^
    vertical_size_cutoff_medium: float = 4.8  # resize text below this height
    vertical_size_cutoff_small: float = 2.4  #  ^

    def __init__(self,
                 label: str,
                 figure: plt.Figure = None,
                 background: bool = True,
                 **kwargs):
        if label in self.observed_labels:
            err_msg = (f"[DynamicFigure.__init__] `label` must be unique "
                       f"(observed: {self.observed_labels}, received: "
                       f"'{label}')")
            raise ValueError(err_msg)
        if figure is None:
            self.fig = plt.figure(constrained_layout=True)
        else:
            self.fig = figure
        self.label = label
        self.observed_labels.add(self.label)
        self.fig.set_label(self.label)
        self.fig.tight_layout()
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        # set up dynamic elements
        self._grid = DynamicFigure.SubplotGrid(self)
        self._background = None  # initialize
        self.background = background
        if self.fig._suptitle is not None:
            self._title = DynamicText(self.fig._suptitle)
        else:
            self._title = None

    @property
    def background(self) -> DynamicFigure.Background:
        """Read-only accessor for self._background."""
        # background rectangle is always the first element of get_children()
        return self._background

    @background.setter
    def background(self, has_background: Optional[bool]) -> None:
        if not isinstance(has_background, (bool, type(None))):
            err_msg = (f"[DynamicFigure.background] `background` must be set "
                       f"to a boolean or None, with False/None deleting the "
                       f"current background rectangle (received object of "
                       f"type: {type(has_background)})")
            raise TypeError(err_msg)
        children = self.fig.get_children()
        if (len(children) == 0 or
            not isinstance(children[0], mpl.patches.Rectangle)):
            children_msg = "\n".join(children)
            err_msg = (f"[DynamicFigure.background] unexpected error, figure "
                       f"has no background rectangle: expected first index of "
                       f"figure.get_children() to be an instance of "
                       f"matplotlib.patches.Rectangle (observed children: "
                       f"{children_msg})")
            raise RuntimeError(err_msg)
        if has_background:
            self._background = DynamicFigure.Background(children[0], self)
            self._background.visible = True
        else:
            self._background.visible = False
            self._background = None

    # @property
    # def contents(self) -> list[DynamicAxes]:
    #     """Return the subplot contents of this figure."""
    #     return [DynamicAxes(ax) for ax in self.fig.axes]

    @property
    def dpi(self) -> float:
        return self.fig.get_dpi()

    @dpi.setter
    def dpi(self, new_dpi: NUMERIC) -> None:
        if not isinstance(new_dpi, NUMERIC_TYPECHECK):
            err_msg = f"[DynamicFigure.dpi] `dpi` must be a numeric > 0"
            raise TypeError(err_msg)
        if new_dpi <= 0:
            err_msg = f"[DynamicFigure.dpi] `dpi` must be a numeric > 0"
            raise ValueError(err_msg)
        self.fig.set_dpi(new_dpi)

    @property
    def height(self) -> float:
        """Return figure height in inches."""
        return self.fig.get_figheight()

    @height.setter
    def height(self, new_height: NUMERIC) -> None:
        """Set figure height in inches."""
        if not isinstance(new_height, NUMERIC_TYPECHECK):
            err_msg = f"[DynamicFigure.height] `height` must be a numeric > 0"
            raise TypeError(err_msg)
        if new_height <= 0:
            err_msg = f"[DynamicFigure.height] `height` must be a numeric > 0"
            raise ValueError(err_msg)
        # resize elements of axes
        self.fig.set_figheight(new_height)
        self.fig.tight_layout()

    @property
    def subplot_grid(self) -> DynamicFigure.SubplotGrid:
        return self._grid

    @property
    def title(self) -> DynamicText:
        """Read-only accessor for self._title."""
        return self._title

    @title.setter
    def title(self, new_title: Optional[str]) -> None:
        """Spawns a new DynamicText object representing the figure title."""
        if not isinstance(new_title, (str, type(None))):
            err_msg = (f"[DynamicFigure.title] `title` must be either a "
                       f"string or None (received {type(new_title)})")
            raise TypeError(err_msg)
        if not new_title:  # title is None or empty string
            self._title = None
            self.fig._suptitle = None
        else:
            if self._title is not None:
                kwargs = self._title.properties()
                kwargs.pop("text")
            else:
                kwargs = {}
            self._title = DynamicText(self.fig.suptitle(new_title), **kwargs)
        self.fig.tight_layout()

    @property
    def width(self) -> float:
        """Return figure width in inches."""
        return self.fig.get_figwidth()

    @width.setter
    def width(self, new_width: NUMERIC) -> None:
        """Set figure width in inches."""
        if not isinstance(new_width, NUMERIC_TYPECHECK):
            err_msg = f"[DynamicFigure.width] `width` must be a numeric > 0"
            raise TypeError(err_msg)
        if new_width <= 0:
            err_msg = f"[DynamicFigure.width] `width` must be a numeric > 0"
            raise ValueError(err_msg)
        # resize elements of axes
        self.fig.set_figwidth(new_width)
        self.fig.tight_layout()

    def save(self, save_to: Union[Path, str]) -> None:
        """Save this figure to given path."""
        if not any(issubclass(type(save_to), t) for t in [Path, str]):
            err_msg = (f"[DynamicFigure.save] `save_to` must be either a "
                       f"string or Path-like object")
            raise TypeError(err_msg)
        self.set_active()
        plt.savefig(save_to)

    def set_active(self) -> None:
        """Set this figure as current matplotlib object.  After running this,
        `plt.gcf()` will return a reference to `self.fig`.
        """
        plt.figure(self.label)

    def show(self) -> None:
        """Show this figure on current graphics device."""
        self.set_active()
        plt.show()

    # def __add__(self, axes: Union[plt.Axes, DynamicAxes]) -> DynamicFigure:
    #     """Add an axis to this figure as a new subplot."""
    #     raise NotImplementedError()

    # def __iadd__(self, axes: DynamicAxes) -> DynamicFigure:
    #     """Add an axis to this figure as a new subplot (in-place)."""
    #     raise NotImplementedError()

    def __len__(self) -> int:
        """Returns total number of axes/subplots contained in this figure."""
        return len(self.fig.axes)

    def __str__(self) -> str:
        """Returns a quick string identifier for this figure."""
        if self.__len__() > 1:  # plural
            return (f"{self.label} ({self.subplot_grid.rows}x"
                    f"{self.subplot_grid.columns}, {self.__len__()} subplots)")
        return (f"{self.label} ({self.subplot_grid.rows}x"
                f"{self.subplot_grid.columns}, {self.__len__()} subplot)")

    # def __sub__(self, axes: DynamicAxes) -> DynamicFigure:
    #     """Remove an axis/subplot from this figure."""
    #     raise NotImplementedError()

    # def __isub__(self, axes: DynamicAxes) -> DynamicFigure:
    #     """Remove an axis/subplot from this figure (in-place)."""
    #     raise NotImplementedError()

    class Background(DynamicRectangle):

        def __init__(self,
                     rect_obj: mpl.patches.Rectangle,
                     parent: DynamicFigure,
                     **kwargs):
            super().__init__(rect_obj, **kwargs)
            self.parent = parent

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
                err_msg = (f"[DynamicFigure.Background.face_color] "
                           f"`face_color` must be either a string specifying "
                           f"a named color or a tuple of numeric RGB values "
                           f"between 0 and 1 (received object of type: "
                           f"{type(new_color)})")
                raise TypeError(err_msg)
            if (isinstance(new_color, tuple) and
                (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color))):
                err_msg = (f"[DynamicFigure.Background.face_color] "
                           f"`face_color` must be either a string specifying "
                           f"a named color or a tuple of numeric RGB values "
                           f"between 0 and 1 (received: {new_color})")
                raise ValueError(err_msg)
            if isinstance(new_color, str):
                self.obj.set_facecolor(new_color)
            else:
                self.obj.set_facecolor(new_color + (self.face_alpha,))
            cdiff = color_diff(self.face_color, self.parent.title.color)
            if cdiff < self.parent.color_cutoff:
                self.parent.title.invert_color()

        @property
        def height(self) -> float:
            return self.parent.height

        @height.setter
        def height(self, new_height: NUMERIC) -> None:
            self.parent.height = new_height

        @property
        def width(self) -> float:
            return self.parent.width

        @width.setter
        def width(self, new_width: NUMERIC) -> None:
            self.parent.width = new_width

    class SubplotGrid:

        """Initialize this to a 4-column grid, then have each axes object fill
        the available space.  This gets rid of the `max_columns` field.

        When a new plot is added to the grid, divide the available space among
        the subplots.
            1 plot: 1x4 grid, plot fills all 4 columns
            2 plots: 1x4 grid, each plot fills 2 columns
            3 plots: 1x4 grid, each plot fills 1 column, last column empty
            4 plots: 1x4 grid, each plot fills 1 column
            5 plots: 2x4 grid, each plot fills 1 column, 3 empty columns in
                last row
            ...

        For different numbers of columns:
            1 column: each plot fills the column
            2 columns: first plot double fills
            3 columns: first plot triple fills, second leaves one empty
            4 columns: see above
            5 columns: first plot fills all 5 columns, second fills 2 and leaves
                one empty, third leaves 2 empty, fourth leaves 1

        When empty columns are encountered, use the set_position() method to
        do fractional fills.  This only applies to the first row.

        Maybe initialize to 12 columns for better divisibility?  Like a CSS
        layout.

        12-column grid:
            1 plot/row: plot fills all 12 columns
            2 plots/row: each plot fills 6 columns
            3 plots/row: each plot fills 4 columns
            4 plots/row: each plot fills 3 columns
            -- autowrap --
            5 plots/row: 1 padding column on each side, each plot
                fills 2 columns
            6 plots/row: each plot fills 2 columns
            -- autowrap --
            7+ plots/row: requires custom specification
        """

        def __init__(self, parent: DynamicFigure):
            self.parent = parent
            self.gridspec = GridSpec(1, 12)

        @property
        def columns(self) -> int:
            """Return the number of columns for the current subplot grid."""
            return self.gridspec.ncols

        @columns.setter
        def columns(self, new_columns: int) -> None:
            """Set the number of columns for the current subplot grid."""
            if not isinstance(new_columns, int):
                err_msg = (f"[DynamicFigure.SubplotGrid.columns] `columns` "
                           f"must be an integer >= 1")
                raise TypeError(err_msg)
            if new_columns < 1:
                err_msg = (f"[DynamicFigure.SubplotGrid.columns] `columns` "
                           f"must be an integer >= 1")
                raise ValueError(err_msg)
            # https://stackoverflow.com/questions/22881301/changing-matplotlib-subplot-size-position-after-axes-creation
            if new_columns != self.columns:  # reposition existing axes
                new_rows = ceil(self.parent.__len__() / new_columns)
                self.gridspec = GridSpec(new_rows, new_columns)
                # self.width = self.width * (new_columns / self.columns)
                for index, ax in enumerate(self.parent.fig.axes):
                    new_sps = SubplotSpec(self.gridspec, index)
                    ax.set_subplotspec(new_sps)
                self.parent.fig.tight_layout()

        @property
        def rows(self) -> int:
            """Return total number of rows for current subplot grid."""
            return self.gridspec.nrows

        @rows.setter
        def rows(self, new_rows: int) -> None:
            """Set number of rows for current subplot grid."""
            min_rows = max(1, ceil(self.parent.__len__() / self.columns))
            if not isinstance(new_rows, int):
                err_msg = (f"[DynamicFigure.SubplotGrid.rows] `rows` must be "
                           f"an integer >= {min_rows}")
                raise TypeError(err_msg)
            if new_rows < min_rows:
                err_msg = (f"[DynamicFigure.SubplotGrid.rows] `rows` must be "
                           f"an integer >= {min_rows}")
                raise ValueError(err_msg)
            # https://stackoverflow.com/questions/22881301/changing-matplotlib-subplot-size-position-after-axes-creation
            if new_rows != self.rows:  # reposition existing axes
                self.gridspec = GridSpec(new_rows, self.columns)
                # self.width = self.width * (new_cols / self.columns)
                # self.height = self.height * (new_rows / self.rows)
                for index, ax in enumerate(self.parent.fig.axes):
                    new_sps = SubplotSpec(self.gridspec, index)
                    ax.set_subplotspec(new_sps)
                self.parent.fig.tight_layout()

        @property
        def shape(self) -> tuple[int, int]:
            """Return (rows, cols) of current subplot grid."""
            return (self.rows, self.columns)

        @shape.setter
        def shape(self, new_shape: tuple[int, int]) -> None:
            """Set (rows, cols) of current subplot grid."""
            if not isinstance(new_shape, tuple):
                err_msg = (f"[DynamicFigure.SubplotGrid.shape] `shape` must "
                           f"be a length 2 tuple of integers "
                           f"`(n_rows, n_columns)`")
                raise TypeError(err_msg)
            if (len(new_shape) != 2 or
                not all(isinstance(i, int) for i in new_shape)):
                err_msg = (f"[DynamicFigure.SubplotGrid.shape] `shape` must "
                           f"be a length 2 tuple of integers "
                           f"`(n_rows, n_columns)`")
                raise ValueError(err_msg)
            rows, cols = new_shape
            self.rows = rows
            self.cols = cols


if __name__ == "__main__":

    fig, axes = plt.subplots(2, 3)
    dfig = DynamicFigure("test_plot", fig)
    dfig.title = "test"
    dfig.title.alpha = 0.5
    print(f"Title alpha: {dfig.title.alpha}")
    dfig.title.autowrap = True
    print(f"Title autowrap: {dfig.title.autowrap}")
    dfig.background.face_color = (0.2, 0.2, 0.2)
    print(f"Title color: {dfig.title.color}")
    dfig.title.font = "Liberation Serif"
    print(f"Title font: {dfig.title.font}")
    dfig.title.horizontal_alignment = "left"
    print(f"Title horizontal_alignment: {dfig.title.horizontal_alignment}")
    dfig.title.rotation = 10
    print(f"Title rotation: {dfig.title.rotation}")
    dfig.title.line_spacing = 1.4
    print(f"Title line_spacing: {dfig.title.line_spacing}")
    dfig.title.position = (0.4, 0.94)
    print(f"Title position: {dfig.title.position}")
    dfig.title.size = 14
    print(f"Title size: {dfig.title.size}")
    print(f"Title text: {dfig.title}")
    dfig.title.vertical_alignment = "top"
    print(f"Title vertical_alignment: {dfig.title.vertical_alignment}")
    print(f"Title visible: {dfig.title.visible}")
    dfig.title.weight = "bold"
    print(f"Title weight: {dfig.title.weight}")
    print(repr(dfig.title))
    print()
    print(f"Background color: {dfig.background.face_color}")
    dfig.background.face_alpha = 0.5
    print(f"Background alpha: {dfig.background.face_alpha}")
    dfig.background.hatch = "O"
    print(f"Background hatch style: {dfig.background.hatch}")
    dfig.background.border_width = 10
    print(f"Background border width: {dfig.background.border_width}")
    dfig.background.border_color = "red"
    print(f"Background border color: {dfig.background.border_color}")
    dfig.background.border_alpha = 1.0
    print(f"Background border alpha: {dfig.background.border_alpha}")
    dfig.background.border_style = "--"
    print(f"Background border style: {dfig.background.border_style}")
    print(repr(dfig.background))

    dfig.save(Path("CurveFit_test.pdf"))
    print(dfig)
