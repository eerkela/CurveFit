from __future__ import annotations
from math import ceil, floor
from pathlib import Path
from typing import Union

from matplotlib.colors import to_rgb
from matplotlib.font_manager import findSystemFonts, get_font
from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt

"""
TODO: https://stackoverflow.com/questions/2024566/how-to-access-outer-class-from-an-inner-class
"""

NUMERIC = Union[int, float]


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

    class Title:
        """Meant to make changing title sizes/colors easier

        text fields:
        https://matplotlib.org/stable/api/text_api.html#matplotlib.text.Text
        """

        def __init__(self, parent: DynamicFigure):
            self.parent = parent
            self.parent_class = self.parent.__class__.__name__
            self.self_class = self.__class__.__name__

        @property
        def alpha(self) -> float:
            if hasattr(self.parent.fig, "_suptitle"):
                result = self.parent.fig._suptitle.get_alpha()
                if result is None:
                    return 1.0
                return result
            return None

        @alpha.setter
        def alpha(self, new_alpha: float) -> None:
            if not hasattr(self.parent.fig, "_suptitle"):
                err_msg = (f"[{self.__class__.__name__}.title.alpha] Could "
                           f"not set title alpha: figure has no title")
                raise RuntimeError(err_msg)
            if not isinstance(new_alpha, float):
                err_msg = (f"[{self.__class__.__name__}.title.alpha] `alpha` "
                           f"must be a float")
                raise TypeError(err_msg)
            if not 0 <= new_alpha <= 1:
                err_msg = (f"[{self.__class__.__name__}.title.alpha] `alpha` "
                           f"must be between 0 and 1 (received: {new_alpha})")
                raise ValueError(err_msg)
            self.parent.fig._suptitle.set_alpha(new_alpha)

        @property
        def autowrap(self) -> bool:
            raise NotImplementedError()

        @autowrap.setter
        def autowrap(self, new_wrap: bool) -> None:
            raise NotImplementedError()

        @property
        def color(self) -> tuple[float, float, float]:
            if hasattr(self.parent.fig, "_suptitle"):
                return to_rgb(self.parent.fig._suptitle.get_color())
            return None

        @color.setter
        def color(
            self,
            new_color: Union[str, tuple[NUMERIC, NUMERIC, NUMERIC]]
        ) -> None:
            if not hasattr(self.parent.fig, "_suptitle"):
                err_msg = (f"[{self.parent_class}.{self.self_class}.color] "
                           f"Could not set title color: figure has no title")
                raise RuntimeError(err_msg)
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
            return self.parent.fig._suptitle.set_color(new_color)

        @property
        def font(self) -> str:
            raise NotImplementedError()

        @font.setter
        def font(self) -> None:
            available_fonts = [get_font(p) for p in findSystemFonts()]
            raise NotImplementedError()

        """TODO: replace *_alignment fields with generic alignment field"""
        @property
        def horizontal_alignment(self) -> str:
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_horizontalalignment()
            return None

        @horizontal_alignment.setter
        def horizontal_alignment(self, new_horizontal_alignment: str) -> None:
            raise NotImplementedError()

        @property
        def rotation(self) -> float:
            raise NotImplementedError()

        @rotation.setter
        def rotation(self, new_rotation: float) -> None:
            raise NotImplementedError()

        @property
        def line_spacing(self) -> float:
            raise NotImplementedError()

        @line_spacing.setter
        def line_spacing(self, new_line_spacing: float) -> None:
            raise NotImplementedError()

        @property
        def position(self) -> tuple[float, float]:
            raise NotImplementedError()

        @position.setter
        def position(self, new_position: tuple[float, float]) -> None:
            raise NotImplementedError()

        @property
        def size(self) -> float:
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_fontsize()
            return None

        @size.setter
        def size(self, new_size: float) -> None:
            raise NotImplementedError()

        @property
        def text(self) -> str:
            """Return figure title (not related to any subplot)."""
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_text()
            return None

        @text.setter
        def text(self, new_text: str) -> None:
            """Set figure title (not related to any subplot)."""
            if not isinstance(new_text, str):
                err_msg = (f"[{self.parent_class}.{self.self_class}.text] "
                           f"`text` must be a string")
                raise TypeError(err_msg)
            self.parent.fig.suptitle(new_text)
            self.parent.fig.tight_layout()
            rgb_vals = self.parent.background.color
            if all(c <= self.parent.color_cutoff for c in rgb_vals):
                self.color = "white"  # convert to white to maintain contrast

        @property
        def vertical_alignment(self) -> str:
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_verticalalignment()
            return None

        @vertical_alignment.setter
        def vertical_alignment(self, new_vertical_alignment: str) -> None:
            if not hasattr(self.parent.fig, "_suptitle"):
                err_msg = (f"[{self.parent_class}.{self.self_class}."
                           f"vertical_alignment] Could not set title vertical "
                           f"alignment: figure has no title")
                raise RuntimeError(err_msg)
            if not isinstance(new_vertical_alignment, str):
                err_msg = (f"[{self.parent_class}.{self.self_class}."
                           f"vertical_alignment] `vertical_alignment` must be "
                           f"a string")
                raise TypeError(err_msg)
            allowed_vals = {"center", "top", "bottom", "baseline",
                            "center_baseline"}
            if new_vertical_alignment not in allowed_vals:
                err_msg = (f"[{self.parent_class}.{self.self_class}."
                           f"vertical_alignment] `vertical_alignment` must be "
                           f"one of the following: {allowed_vals} (received: "
                           f"{new_vertical_alignment})")
                raise ValueError(err_msg)
            self.parent.fig._suptitle.set_verticalalignment(
                new_vertical_alignment
            )
            self.parent.fig.tight_layout()

        @property
        def visible(self) -> bool:
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_visible()
            return False

        @visible.setter
        def visible(self, new_visible: bool) -> None:
            if not hasattr(self.parent.fig, "_suptitle"):
                err_msg = (f"[{self.parent_class}.{self.self_class}.visible] "
                           f"Could not set title visibility: figure has no "
                           f"title")
                raise RuntimeError(err_msg)
            if not isinstance(new_visible, bool):
                err_msg = (f"[{self.parent_class}.{self.self_class}.visible] "
                           f"`visible` must be a boolean")
                raise TypeError(err_msg)
            self.parent.fig._suptitle.set_visible(new_visible)
            self.parent.fig.tight_layout()

        @property
        def weight(self) -> str:
            if hasattr(self.parent.fig, "_suptitle"):
                return self.parent.fig._suptitle.get_weight()
            return None

        @weight.setter
        def weight(self, new_weight: str) -> None:
            allowed_vals = {"ultralight", "light", "normal", "regular", "book",
                            "medium", "roman", "semibold", "demibold", "demi",
                            "bold", "heavy", "extra bold", "black"}


if __name__ == "__main__":

    fig, axes = plt.subplots(2, 3)
    dfig = DynamicFigure("test_plot", fig)
    dfig.title = "test"
    dfig.background.color = (0.2, 0.2, 0.2)
    print(dfig.title.text)
    print(dfig.title.vertical_alignment)
    dfig.title.vertical_alignment = "bottom"
    print(dfig.title.vertical_alignment)
    dfig.save(Path("CurveFit_test.png"))
    print(dfig)
