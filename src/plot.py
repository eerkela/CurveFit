from __future__ import annotations
import inspect
from math import ceil, sqrt
from pathlib import Path
from typing import Optional, Union

import matplotlib as mpl
from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt


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
                       f"instance of matplotlib.text.Text (received "
                       f"{type(text_obj)})")
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
                       f"between 0 and 1")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[DynamicText.alpha] `alpha` must be a numeric "
                       f"between 0 and 1 (received {new_alpha})")
            raise ValueError(err_msg)
        self.obj.set_alpha(new_alpha)

    @property
    def autowrap(self) -> bool:
        return self.obj.get_wrap()

    @autowrap.setter
    def autowrap(self, new_wrap: bool) -> None:
        if not isinstance(new_wrap, bool):
            err_msg = f"[DynamicText.autowrap] `autowrap` must be a boolean"
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
            err_msg = (f"[DynamicText.color] `color` must be either a "
                       f"string or tuple of numeric RGB values")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[DynamicText.color] when passing RGB values, "
                           f"`color` must be a tuple of length 3 containing "
                           f"floats between 0 and 1 (received {new_color})")
                raise ValueError(err_msg)
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
                       f"{allowed_msg}")
            raise TypeError(err_msg)
        if new_font not in allowed:
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[DynamicText.font] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}")
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
                       f"the following values: {allowed}")
            raise TypeError(err_msg)
        if new_horizontal_alignment not in allowed:
            err_msg = (f"[DynamicText.horizontal_alignment] "
                       f"`horizontal_alignment` must be a string with one of "
                       f"the following values: {allowed}")
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
                       f"degrees (0 = horizontal, 90 = vertical)")
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
                       f"numeric >= 1 representing a multiple of `font_size`")
            raise TypeError(err_msg)
        if not new_line_spacing >= 1:
            err_msg = (f"[DynamicText.line_spacing] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size`")
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
            err_msg = (f"[DynamicText.position] `position` must be an (x, y) "
                       f"tuple of length 2 containing only numeric values "
                       f"between 0 and 1")
            raise TypeError(err_msg)
        if (len(new_position) != 2 or
            not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_position) or
            not all(0 <= v <= 1 for v in new_position)):
            err_msg = (f"[DynamicText.position] `position` must be an (x, y) "
                       f"tuple of length 2 containing only numeric values "
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
            err_msg = f"[DynamicText.size] `size` must be a numeric > 0"
            raise TypeError(err_msg)
        if not new_size > 0:
            err_msg = f"[DynamicText.size] `size` must be > 0"
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
            err_msg = f"[DynamicText.text] `text` must be a string"
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
                       f"must be a string (allowed values: {allowed})")
            raise TypeError(err_msg)
        if new_vertical_alignment not in allowed:
            err_msg = (f"[DynamicText.vertical_alignment] `vertical_alignment` "
                       f"must be one of the following: {allowed} (received "
                       f"'{new_vertical_alignment}')")
            raise ValueError(err_msg)
        self.obj.set_verticalalignment(new_vertical_alignment)
        self.obj.get_figure().tight_layout()

    @property
    def visible(self) -> bool:
        return self.obj.get_visible()

    @visible.setter
    def visible(self, new_visible: bool) -> None:
        if not isinstance(new_visible, bool):
            err_msg = (f"[DynamicText.visible] `visible` must be a boolean")
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
            err_msg = (f"[DynamicText.weight] `weight` must be a string "
                       f"(allowed values: {allowed})")
            raise TypeError(err_msg)
        if new_weight not in allowed:
            err_msg = (f"[DynamicText.weight] `weight` must be one of the "
                       f"following: {allowed} (received '{new_weight}')")
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
        return f"DynamicText({str(self.obj)}, {', '.join(props)})"

    def __str__(self) -> str:
        return self.text


class DynamicAxes:

    def __init__(self, axes: plt.Axes = None, **kwargs):
        raise NotImplementedError()

    def draw(self, type, position) -> None:
        """Draw lines/polygons on the current axes."""
        raise NotImplementedError()

    class Background:

        def __init__(self, parent):
            self.parent = parent

        @property
        def alpha(self) -> float:
            raise NotImplementedError()

        @property
        def color(self) -> tuple[float, float, float]:
            raise NotImplementedError()

    class Legend:

        def __init__(self, parent):
            self.parent = parent
            self.legend = self.parent.axes.get_legend()  # can be None
            # Texts: self.legend.get_texts()

        @property
        def visible(self) -> bool:
            raise NotImplementedError()

    class XAxis:

        def __init__(self, parent):
            self.parent = parent

        @property
        def label(self) -> str:
            raise NotImplementedError()

        @property
        def limit(self) -> float:
            raise NotImplementedError()

    class YAxis:

        def __init__(self, parent):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def label(self) -> str:
            raise NotImplementedError()

        @property
        def limit(self) -> float:
            raise NotImplementedError()


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
        self._background = DynamicFigure.Background(self)
        self._border = DynamicFigure.Border(self)
        self._grid = DynamicFigure.SubplotGrid(self)
        self._title = None

    @property
    def background(self) -> DynamicFigure.Background:
        """Read-only accessor for self._background."""
        return self._background

    @property
    def border(self) -> DynamicFigure.Border:
        """Read-only accessor for self._border."""
        return self._border

    @property
    def contents(self) -> list[DynamicAxes]:
        """Return the subplot contents of this figure."""
        return [DynamicAxes(ax) for ax in self.fig.axes]

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

    def __add__(self, axes: Union[plt.Axes, DynamicAxes]) -> DynamicFigure:
        """Add an axis to this figure as a new subplot."""
        raise NotImplementedError()

    def __iadd__(self, axes: DynamicAxes) -> DynamicFigure:
        """Add an axis to this figure as a new subplot (in-place)."""
        raise NotImplementedError()

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

    def __sub__(self, axes: DynamicAxes) -> DynamicFigure:
        """Remove an axis/subplot from this figure."""
        raise NotImplementedError()

    def __isub__(self, axes: DynamicAxes) -> DynamicFigure:
        """Remove an axis/subplot from this figure (in-place)."""
        raise NotImplementedError()

    class Background:

        def __init__(self, parent: DynamicFigure):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def alpha(self) -> float:
            return self.parent.fig.get_facecolor()[-1]

        @alpha.setter
        def alpha(self, new_alpha: float) -> None:
            if not isinstance(new_alpha, float):
                err_msg = (f"[{self.parent_class}.{self.self_class}.alpha] "
                           f"`alpha` must be a float")
                raise TypeError(err_msg)
            if not 0 <= new_alpha <= 1:
                err_msg = (f"[{self.parent_class}.{self.self_class}.alpha] "
                           f"`alpha` must be between 0 and 1 (received "
                           f"{new_alpha})")
                raise ValueError(err_msg)
            self.parent.fig.set_facecolor(self.color + (new_alpha,))

        @property
        def color(self) -> tuple[float, float, float]:
            """Return RGB color values of this figure's background rectangle."""
            return mpl.colors.to_rgb(self.parent.fig.get_facecolor())

        @color.setter
        def color(
            self,
            new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
        ) -> None:
            """Set the color of the background rectangle for the current figure."""
            if not any(isinstance(new_color, t) for t in [str, tuple]):
                err_msg = (f"[{self.parent_class}.{self.self_class}.color] "
                           f"`color` must be either a string or tuple of "
                           f"numeric RGB values")
                raise TypeError(err_msg)
            if isinstance(new_color, tuple):
                if (len(new_color) != 3 or
                    not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                    not all(0 <= v <= 1 for v in new_color)):
                    err_msg = (f"[{self.parent_class}.{self.self_class}.color] "
                               f"when passing RGB values, `color` must be a "
                               f"tuple of length 3 containing floats between "
                               f"0 and 1 (received {new_color})")
                    raise ValueError(err_msg)
            if isinstance(new_color, str):
                self.parent.fig.set_facecolor(new_color)
            else:
                self.parent.fig.set_facecolor(new_color + (self.alpha,))
            cdiff = color_diff(self.color, self.parent.title.color)
            if cdiff < self.parent.color_cutoff:
                self.parent.title.invert_color()

    class Border:

        def __init__(self, parent: DynamicFigure):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def alpha(self) -> float:
            return self.parent.fig.get_edgecolor()[-1]

        @alpha.setter
        def alpha(self, new_alpha: float):
            if not isinstance(new_alpha, float):
                err_msg = (f"[{self.parent_class}.{self.self_class}.alpha] "
                           f"`alpha` must be a float")
                raise TypeError(err_msg)
            if not 0 <= new_alpha <= 1:
                err_msg = (f"[{self.parent_class}.{self.self_class}.alpha] "
                           f"`alpha` must be between 0 and 1 (received "
                           f"{new_alpha})")
                raise ValueError(err_msg)
            self.parent.fig.set_edgecolor(self.color + (new_alpha,))

        @property
        def color(self) -> tuple[float, float, float]:
            """Return RGB color values of border line around current figure."""
            return mpl.colors.to_rgb(self.parent.fig.get_edgecolor())

        @color.setter
        def color(
            self,
            new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
        ) -> None:
            """Set color of border line around the current figure."""
            if not any(isinstance(new_color, t) for t in [str, tuple]):
                err_msg = (f"[{self.parent_class}.{self.self_class}.color] "
                           f"`color` must be either a string or tuple of "
                           f"numeric RGB values")
                raise TypeError(err_msg)
            if isinstance(new_color, tuple):
                if (len(new_color) != 3 or
                    not all(isinstance(v, NUMERIC_TYPECHECK) for v in new_color) or
                    not all(0 <= v <= 1 for v in new_color)):
                    err_msg = (f"[{self.parent_class}.{self.self_class}.color] "
                               f"when passing RGB values, `color` must be a "
                               f"tuple of length 3 containing floats between "
                               f"0 and 1 (received {new_color})")
                    raise ValueError(err_msg)
            self.parent.fig.set_edgecolor(new_color + (self.alpha,))

        @property
        def width(self) -> float:
            """Return width (in points) of border line around the current figure."""
            return self.parent.fig.get_linewidth()

        @width.setter
        def width(self, new_width: float) -> None:
            """Set width (in points) of border line around the current figure."""
            if not isinstance(new_width, float):
                err_msg = (f"[{self.__class__.__name__}.border.width] "
                           f"`width` must be a float")
                raise TypeError(err_msg)
            if new_width < 0:
                err_msg = (f"[{self.__class__.__name__}.border.width] "
                           f"`width` must be >= 0")
                raise ValueError(err_msg)
            self.parent.fig.set_linewidth(new_width)

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
    dfig.background.color = (0.2, 0.2, 0.2)
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
    # dfig.title = None
    # dfig.title = "test2"
    dfig.save(Path("CurveFit_test.png"))
    print(repr(dfig.title))
    print(dfig)
