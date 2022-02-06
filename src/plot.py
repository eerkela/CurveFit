from __future__ import annotations
import inspect
from math import ceil, floor
from pathlib import Path
from typing import Type, Union

import matplotlib as mpl
from matplotlib.colors import to_rgb
from matplotlib.font_manager import findSystemFonts, get_font
from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt


NUMERIC = Union[int, float]


class DynamicText:

    def __init__(self, parent):
        self.parent = parent

    @property
    def alpha(self) -> float:
        text = self.get_text_obj()
        if text:
            result = text.get_alpha()
            if result is None:
                return 1.0
            return result
        return None

    @alpha.setter
    def alpha(self, new_alpha: NUMERIC) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_alpha, (int, float)):
            err_msg = (f"[{self._error_trace()}] `alpha` must be a numeric "
                       f"between 0 and 1")
            raise TypeError(err_msg)
        if not 0 <= new_alpha <= 1:
            err_msg = (f"[{self._error_trace()}] `alpha` must be a numeric "
                       f"between 0 and 1 (received {new_alpha})")
            raise ValueError(err_msg)
        text.set_alpha(new_alpha)

    @property
    def autowrap(self) -> bool:
        text = self._get_text_obj()
        if text:
            return text.get_wrap()
        return None

    @autowrap.setter
    def autowrap(self, new_wrap: bool) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_wrap, bool):
            err_msg = f"[{self._error_trace()}] `autowrap` must be a boolean"
            raise TypeError(err_msg)
        text.set_wrap(new_wrap)
        self._get_figure().tight_layout()

    @property
    def color(self) -> tuple[float, float, float]:
        text = self._get_text_obj()
        if text:
            return to_rgb(text.get_color())  # converts named colors
        return None

    @color.setter
    def color(
        self, new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
    ) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_color, (str, tuple)):
            err_msg = (f"[{self._error_trace()}] `color` must be either a "
                       f"string or tuple of numeric RGB values")
            raise TypeError(err_msg)
        if isinstance(new_color, tuple):
            if (len(new_color) != 3 or
                not all(isinstance(v, (int, float)) for v in new_color) or
                not all(0 <= v <= 1 for v in new_color)):
                err_msg = (f"[{self._error_trace()}] when passing RGB values, "
                           f"`color` must be a tuple of length 3 containing "
                           f"floats between 0 and 1 (received {new_color})")
                raise ValueError(err_msg)
        text.set_color(new_color)

    @property
    def font(self) -> str:
        text = self._get_text_obj()
        if text:
            return text.get_fontfamily()
        return None

    @font.setter
    def font(self, new_font: str) -> None:
        text = self._get_text_obj(error=True)
        allowed = self.available_fonts()
        if not isinstance(new_font, str):
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[{self._error_trace()}] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}")
            raise TypeError(err_msg)
        if new_font not in allowed:
            allowed_msg = "\n".join(sorted(allowed))
            err_msg = (f"[{self._error_trace()}] `font` must be a string "
                       f"referencing one of the available system fonts: "
                       f"{allowed_msg}")
            raise ValueError(err_msg)
        text.set_fontfamily(new_font)
        self._get_figure().tight_layout()

    """TODO: replace *_alignment fields with generic alignment field"""
    @property
    def horizontal_alignment(self) -> str:
        text = self._get_text_obj()
        if text:
            return text.get_horizontalalignment()
        return None

    @horizontal_alignment.setter
    def horizontal_alignment(self, new_horizontal_alignment: str) -> None:
        text = self._get_text_obj(error=True)
        allowed = {"center", "right", "left"}
        if not isinstance(new_horizontal_alignment, str):
            err_msg = (f"[{self._error_trace()}] `horizontal_alignment` must "
                       f"be a string with one of the following values: "
                       f"{allowed}")
            raise TypeError(err_msg)
        if new_horizontal_alignment not in allowed:
            err_msg = (f"[{self._error_trace()}] `horizontal_alignment` must "
                       f"be a string with one of the following values: "
                       f"{allowed}")
            raise ValueError(err_msg)
        text.set_horizontalalignment(new_horizontal_alignment)
        self._get_figure().tight_layout()

    @property
    def rotation(self) -> float:
        text = self._get_text_obj()
        if text:
            return text.get_rotation()
        return None

    @rotation.setter
    def rotation(self, new_rotation: NUMERIC) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_rotation, (int, float)):
            err_msg = (f"[{self._error_trace}] `rotation` must be a numeric "
                       f"representing the counterclockwise rotation angle in "
                       f"degrees (0 = horizontal, 90 = vertical)")
            raise TypeError(err_msg)
        text.set_rotation(new_rotation)
        self._get_figure().tight_layout()

    @property
    def line_spacing(self) -> float:
        text = self._get_text_obj()
        if text:
            return text.get_linespacing()
        return None

    @line_spacing.setter
    def line_spacing(self, new_line_spacing: NUMERIC) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_line_spacing, (int, float)):
            err_msg = (f"[{self._error_trace()}] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size`")
            raise TypeError(err_msg)
        if not new_line_spacing >= 1:
            err_msg = (f"[{self._error_trace()}] `line_spacing` must be a "
                       f"numeric >= 1 representing a multiple of `font_size`")
            raise ValueError(err_msg)
        text.set_linespacing(new_line_spacing)
        self._get_figure().tight_layout()

    @property
    def position(self) -> tuple[float, float]:
        text = self._get_text_obj()
        if text:
            return text.get_position()
        return None

    @position.setter
    def position(self, new_position: tuple[NUMERIC, NUMERIC]) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_position, tuple):
            err_msg = (f"[{self._error_trace()}] `position` must be an (x, y) "
                       f"tuple of length 2 containing only numeric values")
            raise TypeError(err_msg)
        if (len(new_position) != 2 or
            not all(isinstance(v, (int, float)) for v in new_position) or
            not all(v > 0 for v in new_position)):
            err_msg = (f"[{self._error_trace()}] `position` must be an (x, y) "
                       f"tuple of length 2 containing only numeric values "
                       f"(received: {new_position})")
            raise ValueError(err_msg)
        text.set_position(new_position)
        self._get_figure().tight_layout()

    @property
    def size(self) -> float:
        text = self._get_text_obj()
        if text:
            return text.get_fontsize()
        return None

    @size.setter
    def size(self, new_size: NUMERIC) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_size, (int, float)):
            err_msg = f"[{self._error_trace()}] `size` must be a numeric > 0"
            raise TypeError(err_msg)
        if not new_size > 0:
            err_msg = f"[{self._error_trace()}] `size` must be > 0"
            raise ValueError(err_msg)
        text.set_size(new_size)
        self._get_figure().tight_layout()

    @property
    def text(self) -> str:
        """Return figure title (not related to any subplot)."""
        text = self._get_text_obj()
        if text:
            return text.get_text()
        return None

    @text.setter
    def text(self, new_text: str) -> None:
        """Set figure title (not related to any subplot)."""
        text = self._get_text_obj(error=True)
        if not isinstance(new_text, str):
            err_msg = f"[{self._error_trace()}] `text` must be a string"
            raise TypeError(err_msg)
        text.set_text(new_text)

    @property
    def vertical_alignment(self) -> str:
        text = self._get_text_obj()
        if text:
            return text.get_verticalalignment()
        return None

    @vertical_alignment.setter
    def vertical_alignment(self, new_vertical_alignment: str) -> None:
        text = self._get_text_obj(error=True)
        allowed = {"center", "top", "bottom", "baseline", "center_baseline"}
        if not isinstance(new_vertical_alignment, str):
            err_msg = (f"[{self._error_trace()}] `vertical_alignment` must be "
                       f"a string (allowed values: {allowed})")
            raise TypeError(err_msg)
        if new_vertical_alignment not in allowed:
            err_msg = (f"[{self._error_trace()}] `vertical_alignment` must be "
                       f"one of the following: {allowed} (received "
                       f"'{new_vertical_alignment}')")
            raise ValueError(err_msg)
        text.set_verticalalignment(new_vertical_alignment)
        self._get_figure().tight_layout()

    @property
    def visible(self) -> bool:
        text = self._get_text_obj()
        if text:
            return text.get_visible()
        return None

    @visible.setter
    def visible(self, new_visible: bool) -> None:
        text = self._get_text_obj(error=True)
        if not isinstance(new_visible, bool):
            err_msg = (f"[{self._error_trace()}] `visible` must be a "
                        f"boolean")
            raise TypeError(err_msg)
        text.set_visible(new_visible)
        self._get_figure().tight_layout()

    @property
    def weight(self) -> str:
        text = self._get_text_obj()
        if text:
            return text.get_weight()
        return None

    @weight.setter
    def weight(self, new_weight: str) -> None:
        text = self._get_text_obj(error=True)
        allowed = {"ultralight", "light", "normal", "regular", "book", "medium",
                   "roman", "semibold", "demibold", "demi", "bold", "heavy",
                   "extra bold", "black"}
        if not isinstance(new_weight, str):
            err_msg = (f"[{self._error_trace()}] `weight` must be a string "
                       f"(allowed values: {allowed})")
            raise TypeError(err_msg)
        if new_weight not in allowed:
            err_msg = (f"[{self._error_trace()}] `weight` must be one of the "
                       f"following: {allowed} (received '{new_weight}')")
            raise ValueError(err_msg)
        text.set_fontweight(new_weight)
        self._get_figure().tight_layout()

    def _error_trace(self, stack_index: int = 1) -> str:
        """Returns a quick stack trace in the event of an error."""
        parent_class = self.parent.__class__.__name__
        self_class = self.__class__.__name__
        calling_function = inspect.stack()[stack_index].function
        return f"{parent_class}.{self_class}.{calling_function}"

    # OVERRIDE THIS
    def _get_figure(self) -> mpl.figure.Figure:
        """Return the matplotlib.figure.Figure instance associated with this
        object.

        This method must be overriden with a custom accessor that points from
        the current DynamicText object to the appropriate
        matplotlib.figure.Figure instance.  The route to access this will be
        different depending on the location of the text being modified
        (e.g. Figure suptitles vs. Axes labels vs. Legend text).

        When using self._error_trace() with this method, remember to set
        `stack_index=2`.
        """
        raise NotImplementedError()

    # OVERRIDE THIS
    def _get_text_obj(self, error: bool = False) -> mpl.text.Text:
        """Return the matplotlib.text.Text instance associated with this object.

        This method must be overriden with a custom accessor that points from
        the current DynamicText object to the appropriate matplotlib.text.Text
        instance.  The route to access this will be different depending on the
        location of the text being modified (e.g. Figure suptitles vs. Axes
        labels vs. Legend text).

        When using self._error_trace() with this method, remember to set
        `stack_index=2`.
        """
        raise NotImplementedError()

    def available_fonts(self) -> set[str]:
        return set(get_font(fpath).family_name for fpath in findSystemFonts())

    def __str__(self) -> str:
        return self.text


class DynamicAxes:

    def __init__(self, axes: plt.Axes = None, **kwargs):
        raise NotImplementedError()

    def dark_mode(self, convert: bool = True) -> None:
        raise NotImplementedError()

    def draw(self, type, position) -> None:
        """Draw lines/polygons on the current axes."""
        raise NotImplementedError()

    class Foreground:

        def __init__(self, parent):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def alpha(self) -> float:
            raise NotImplementedError()

        @property
        def color(self) -> tuple[float, float, float]:
            raise NotImplementedError()

    class Legend:

        def __init__(self, parent):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def visible(self) -> bool:
            raise NotImplementedError()

    class Title:

        def __init__(self, parent):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def text(self) -> str:
            raise NotImplementedError()

    class XAxis:

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
    color_cutoff: float = 0.2  # convert to white text below this RGB value
    horizontal_size_cutoff_medium: float = 6.4  # resize text below this width
    horizontal_size_cutoff_small: float = 3.2  #  ^
    vertical_size_cutoff_medium: float = 4.8  # resize text below this height
    vertical_size_cutoff_small: float = 2.4  #  ^

    def __init__(self,
                 label: str,
                 figure: plt.Figure = None,
                 max_columns: int = 4,
                 **kwargs):
        if label in self.observed_labels:
            err_msg = (f"[{self.__class__.__name__}.init] `label` must be "
                       f"unique (observed: {self.observed_labels}, received: "
                       f"'{label}')")
            raise ValueError(err_msg)
        if figure is None:
            self.fig = plt.figure(constrained_layout=True)
        else:
            self.fig = figure
        self.label = label
        self.observed_labels.add(self.label)
        self.fig.set_label(self.label)
        self.max_columns = max_columns
        self.fig.tight_layout()
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        self._background = DynamicFigure.Background(self)
        self._border = DynamicFigure.Border(self)
        self._title = DynamicFigure.Title(self)
        # TODO: keeping these public might be a problem.

    @property
    def background(self) -> DynamicFigure.Background:
        """Read-only accessor for self._background."""
        return self._background

    @property
    def border(self) -> DynamicFigure.Border:
        """Read-only accessor for self._border."""
        return self._border

    @property
    def dpi(self) -> float:
        raise NotImplementedError()

    @dpi.setter
    def dpi(self, new_dpi: float) -> None:
        raise NotImplementedError()

    @property
    def height(self) -> float:
        """Return figure height in inches."""
        return self.fig.get_figheight()

    @height.setter
    def height(self, new_height: float) -> None:
        """Set figure height in inches."""
        if not isinstance(new_height, float):
            err_msg = (f"[{self.__class__.__name__}.height] `height` must be "
                       f"a float")
            raise TypeError(err_msg)
        if new_height <= 0:
            err_msg = (f"[{self.__class__.__name__}.height] `height` must be "
                       f"> 0")
            raise ValueError(err_msg)
        # resize elements of axes
        self.fig.set_figheight(new_height)
        self.fig.tight_layout()

    @property
    def title(self) -> DynamicFigure.Title:
        """Read-only accessor for self._title."""
        return self._title

    @title.setter
    def title(self, new_title) -> None:
        """Alias for self._title.text"""
        self._title.text = new_title

    @property
    def width(self) -> float:
        """Return figure width in inches."""
        return self.fig.get_figwidth()

    @width.setter
    def width(self, new_width: float) -> None:
        """Set figure width in inches."""
        if not isinstance(new_width, float):
            err_msg = (f"[{self.__class__.__name__}.width] `width` must be a "
                       f"float")
            raise TypeError(err_msg)
        if new_width <= 0:
            err_msg = (f"[{self.__class__.__name__}.width] `width` must be "
                       f"> 0")
            raise ValueError(err_msg)
        # resize elements of axes
        self.fig.set_figwidth(new_width)
        self.fig.tight_layout()

    def save(self, save_to: Union[Path, str]) -> None:
        """Save this figure to given path."""
        if not any(issubclass(type(save_to), t) for t in [Path, str]):
            err_msg = (f"[{self.__class__.__name__}.save] `save_to` must be "
                       f"either a string or Path-like object")
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
            return (f"{self.label} ({self.rows}x{self.columns}, "
                    f"{self.__len__()} subplots)")
        return (f"{self.label} ({self.rows}x{self.columns}, "
                f"{self.__len__()} subplot)")

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
            return to_rgb(self.parent.fig.get_facecolor())

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
                    not all(isinstance(v, (int, float)) for v in new_color) or
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
            # if color is too dark, convert to white text to maintain contrast
            if all(c <= self.parent.color_cutoff for c in self.color):
                self.parent.title.color = "white"
            else:
                self.parent.title.color = "black"

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
            return to_rgb(self.parent.fig.get_edgecolor())

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
                    not all(isinstance(v, (int, float)) for v in new_color) or
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

        def __init__(self, parent: DynamicFigure):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def axes(self) -> list[DynamicAxes]:
            """Return the subplot contents of this figure."""
            return [DynamicAxes(ax) for ax in self.fig.axes]

        @property
        def columns(self) -> int:
            """Return the number of columns for the current subplot grid."""
            if self.gridspec is not None:
                return self.gridspec.ncols
            return None

        @columns.setter
        def columns(self, new_columns: int) -> None:
            """Set the number of columns for the current subplot grid."""
            if self.columns is None:
                err_msg = (f"[{self.__class__.__name__}.columns] Could not set "
                        f"`columns`: figure has no axes")
                raise RuntimeError(err_msg)
            if not isinstance(new_columns, int):
                err_msg = (f"[{self.__class__.__name__}.columns] `columns` must be "
                        f"an integer")
                raise TypeError(err_msg)
            if new_columns < 1:
                err_msg = (f"[{self.__class__.__name__}.columns] `columns` must be "
                        f">= 1")
                raise ValueError(err_msg)
            # https://stackoverflow.com/questions/22881301/changing-matplotlib-subplot-size-position-after-axes-creation
            if new_columns != self.columns:  # reposition existing axes
                new_rows = ceil(self.__len__() / new_columns)
                new_gs = GridSpec(new_rows, new_columns)
                self.width = self.width * (new_columns / self.columns)
                for index, ax in enumerate(self.fig.axes):
                    new_sps = SubplotSpec(new_gs, index)
                    ax.set_subplotspec(new_sps)
                self.fig.tight_layout()

        @property
        def gridspec(self) -> GridSpec:
            """Return underlying GridSpec object associated with subplot grid."""
            if len(self.fig.axes) > 0:
                return self.fig.axes[0].get_subplotspec() \
                                    .get_topmost_subplotspec() \
                                    .get_gridspec()
            return None

        @property
        def max_columns(self) -> int:
            """Return maximum number of columns allowed per row, after which
            auto-wrapping will occur.
            """
            if hasattr(self, "_max_columns"):
                return self._max_columns
            return 0

        @max_columns.setter
        def max_columns(self, new_max_columns: int) -> None:
            """Set the maximum number of columns per row, after which auto-wrapping
            will occur.

            TODO: is this strictly necessary?
            """
            if not isinstance(new_max_columns, int):
                err_msg = (f"[{self.__class__.__name__}.max_columns] "
                        f"`max_columns` must be an integer")
                raise TypeError(err_msg)
            if new_max_columns < 1:
                err_msg = (f"[{self.__class__.__name__}.max_columns] "
                        f"`max_columns` must be >= 1")
                raise ValueError(err_msg)
            if (new_max_columns != self.max_columns and
                new_max_columns < self.columns):
                self.columns = new_max_columns
            self._max_columns = new_max_columns

        @property
        def rows(self) -> int:
            """Return total number of rows for current subplot grid."""
            if self.gridspec is not None:
                return self.gridspec.nrows
            return None

        @rows.setter
        def rows(self, new_rows: int) -> None:
            """Set number of rows for current subplot grid."""
            if self.rows is None:
                err_msg = (f"[{self.__class__.__name__}.rows] Could not set "
                        f"`rows`: figure has no axes")
                raise RuntimeError(err_msg)
            if not isinstance(new_rows, int):
                err_msg = (f"[{self.__class__.__name__}.rows] `rows` must be "
                        f"an integer")
                raise TypeError(err_msg)
            if new_rows < max(1, ceil(self.__len__() / self.max_columns)):
                err_msg = (f"[{self.__class__.__name__}.rows] `rows` must be "
                        f">= {max(1, ceil(self.__len__() / self.max_columns))}")
                raise ValueError(err_msg)
            # https://stackoverflow.com/questions/22881301/changing-matplotlib-subplot-size-position-after-axes-creation
            if new_rows != self.rows:  # reposition existing axes
                new_cols = min(self.max_columns, ceil(self.__len__() / new_rows))
                new_gs = GridSpec(new_rows, new_cols)
                self.width = self.width * (new_cols / self.columns)
                self.height = self.height * (new_rows / self.rows)
                for index, ax in enumerate(self.fig.axes):
                    new_sps = SubplotSpec(new_gs, index)
                    ax.set_subplotspec(new_sps)
                # above doesn't work for 
                self.fig.tight_layout()

        @property
        def shape(self) -> tuple[int, int]:
            """Return (rows, cols) of current subplot grid."""
            return (self.rows, self.columns)

        @shape.setter
        def shape(self, new_shape: tuple[int, int]) -> None:
            """Set (rows, cols) of current subplot grid."""
            if (not isinstance(new_shape, tuple) or
                not all(isinstance(i, int) for i in new_shape)):
                err_msg = (f"[{self.__class__.__name__}.shape] `shape` must be a "
                        f"tuple of integers")
                raise TypeError(err_msg)
            if len(new_shape) != 2:
                err_msg = (f"[{self.__class__.__name__}.shape] `shape` must be a "
                        f"tuple of length 2 `(width, height)`")
                raise ValueError(err_msg)
            rows, cols = new_shape
            self.rows = rows
            self.cols = cols

    class Title(DynamicText):

        @property
        def text(self) -> str:
            """Return figure title (not related to any subplot)."""
            text = self._get_text_obj()
            if text:
                return text.get_text()
            return None

        @text.setter
        def text(self, new_text: str) -> None:
            """Set figure title (not related to any subplot)."""
            if not isinstance(new_text, str):
                err_msg = (f"[{self._error_trace()}] `text` must be a string")
                raise TypeError(err_msg)
            self.parent.fig.suptitle(new_text)
            self.parent.fig.tight_layout()
            rgb_vals = self.parent.background.color
            if all(c <= self.parent.color_cutoff for c in rgb_vals):
                self.color = "white"  # convert to white to maintain contrast

        def _get_figure(self) -> mpl.figure.Figure:
            """Returns the matplotlib.figure.Figure instance referenced by this
            object.  A helper method like this helps maintain a D.R.Y. and
            easily extensible codebase.
            """
            return self.parent.fig

        def _get_text_obj(self, error: bool = False) -> mpl.text.Text:
            """Returns the matplotlib.text.Text instance referenced by this
            object.  A helper method like this helps maintain a D.R.Y. and
            easily extensible codebase.

            If `error=True`, raises a generic RuntimeError if the
            text object is None, which occurs when a title has not yet been
            set for the current figure.
            """
            attr_obj = self._get_figure()
            attr_name = "_suptitle"
            if hasattr(attr_obj, attr_name):
                result = getattr(attr_obj, attr_name)
                if not result and error:
                    err_msg = f"[{self._error_trace(2)}] figure has no title "
                    raise RuntimeError(err_msg)
                return result
            err_msg = (f"[{self._error_trace(2)}] Unexpected error: figure has "
                       f"no {attr_name} attribute (fatal)")
            raise RuntimeError(err_msg)


if __name__ == "__main__":

    fig, axes = plt.subplots(2, 3)
    dfig = DynamicFigure("test_plot", fig)
    dfig.title = "test"
    dfig.background.color = (0.2, 0.2, 0.2)
    print(dfig.title.text)
    # print(dfig.title.weight)
    # dfig.title.vertical_alignment = "bottom"
    # print(dfig.title.vertical_alignment)
    dfig.save(Path("CurveFit_test.png"))
    # print(dfig)
