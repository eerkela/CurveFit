from __future__ import annotations
from math import ceil, floor
from pathlib import Path
from typing import Union

from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt


class Title:
    """Meant to make changing title sizes/colors easier"""

    def __init__(self, txt: str, **kwargs):
        raise NotImplementedError()

    @property
    def bold(self) -> bool:
        raise NotImplementedError()

    @bold.setter
    def bold(self, new_bold: bool) -> None:
        raise NotImplementedError()


class DynamicAxes:

    def __init__(self, axes: plt.Axes = None, **kwargs):
        raise NotImplementedError()

    @property
    def foreground_color(self) -> str:
        raise NotImplementedError()

    @foreground_color.setter
    def foreground_color(self, new_foreground_color: str) -> None:
        raise NotImplementedError()

    @property
    def title(self) -> str:
        raise NotImplementedError()

    @title.setter
    def title(self, new_title: str) -> None:
        raise NotImplementedError()

    @property
    def x_label(self) -> str:
        raise NotImplementedError()

    @x_label.setter
    def x_label(self, new_x_label: str) -> None:
        raise NotImplementedError()

    @property
    def y_label(self) -> str:
        raise NotImplementedError()

    @y_label.setter
    def y_label(self, new_y_label: str) -> None:
        raise NotImplementedError()

    @property
    def x_limit(self) -> float:
        raise NotImplementedError()

    @x_limit.setter
    def x_limit(self, new_x_limit: float) -> None:
        raise NotImplementedError()

    @property
    def y_limit(self) -> float:
        raise NotImplementedError()

    @y_limit.setter
    def y_limit(self, new_y_limit: float) -> None:
        raise NotImplementedError()

    @property
    def legend(self) -> bool:
        raise NotImplementedError()

    @legend.setter
    def legend(self, new_legend: bool) -> None:
        raise NotImplementedError()

    def dark_mode(self, convert: bool = True) -> None:
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

    @property
    def axes(self) -> list[DynamicAxes]:
        """Return the subplot contents of this figure."""
        return [DynamicAxes(ax) for ax in self.fig.axes]

    @property
    def background_color(self) -> tuple[float, float, float, float]:
        """Return RGBA color values of this figure's background rectangle."""
        return self.fig.get_facecolor()

    @background_color.setter
    def background_color(
        self,
        new_background_color: Union[str, tuple[float, float, float, float]]
    ) -> None:
        """Set the color of the background rectangle for the current figure."""
        if not any(isinstance(new_background_color, t) for t in [str, tuple]):
            err_msg = (f"[{self.__class__.__name__}.background_color] "
                       f"`background_color` must be either a string or tuple "
                       f"of RGBA values")
            raise TypeError(err_msg)
        if isinstance(new_background_color, tuple):
            if (len(new_background_color) != 4 or
                not all(isinstance(v, float) for v in new_background_color) or
                not all(0 <= v <= 1 for v in new_background_color)):
                err_msg = (f"[{self.__class__.__name__}.background_color] "
                           f"when passing RGBA values, `background_color` "
                           f"must be a length 4 tuple of floats between 0 and "
                           f"1 (received {new_background_color})")
                raise ValueError(err_msg)
        self.fig.set_facecolor(new_background_color)
        if all(c <= self.color_cutoff for c in self.fig.get_facecolor()[0:3]):
            self.title = self.title  # update with white text

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
    def border_color(self) -> tuple[float, float, float, float]:
        """Return RGBA color values of border line around the current figure."""
        return self.fig.get_edgecolor()

    @border_color.setter
    def border_color(
        self,
        new_border_color: Union[str, tuple[float, float, float, float]]
    ) -> None:
        """Set color of border line around the current figure."""
        if not any(isinstance(new_border_color, t) for t in [str, tuple]):
            err_msg = (f"[{self.__class__.__name__}.border_color] `border_color` "
                       f"must be either a string or tuple of RGBA values")
            raise TypeError(err_msg)
        if isinstance(new_border_color, tuple):
            if (len(new_border_color) != 4 or
                not all(isinstance(v, float) for v in new_border_color) or
                not all(0 <= v <= 1 for v in new_border_color)):
                err_msg = (f"[{self.__class__.__name__}.border_color] when "
                           f"passing RGBA values, `border_color` must be a "
                           f"length 4 tuple of floats between 0 and 1 "
                           f"(received {new_border_color})")
                raise ValueError(err_msg)
        self.fig.set_edgecolor(new_border_color)

    @property
    def border_width(self) -> float:
        """Return width (in points) of border line around the current figure."""
        return self.fig.get_linewidth()

    @border_width.setter
    def border_width(self, new_border_width: float) -> None:
        """Set width (in points) of border line around the current figure."""
        if not isinstance(new_border_width, float):
            err_msg = (f"[{self.__class__.__name__}.border_width] "
                       f"`border_width` must be a float")
            raise TypeError(err_msg)
        if new_border_width < 0:
            err_msg = (f"[{self.__class__.__name__}.border_width] "
                       f"`border_width` must be >= 0")
            raise ValueError(err_msg)
        self.fig.set_linewidth(new_border_width)

    @property
    def gridspec(self) -> GridSpec:
        """Return underlying GridSpec object associated with subplot grid."""
        if len(self.fig.axes) > 0:
            return self.fig.axes[0].get_subplotspec() \
                                   .get_topmost_subplotspec() \
                                   .get_gridspec()
        return None

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

    @property
    def title(self) -> str:
        """Return figure title (not related to any subplot)."""
        return self.fig._suptitle.get_text()

    @title.setter
    def title(self, new_title: str) -> None:
        """Set figure title (not related to any subplot)."""
        if not isinstance(new_title, str):
            err_msg = (f"[{self.__class__.__name__}.title] `title` must be a "
                       f"string")
            raise TypeError(err_msg)
        if all(c <= self.color_cutoff for c in self.background_color[0:3]):
            self.fig.suptitle(new_title, color="white")  # maintain contrast
        else:
            self.fig.suptitle(new_title)
        self.fig.tight_layout()

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


if __name__ == "__main__":

    fig, axes = plt.subplots(2, 3)
    dfig = DynamicFigure("test_plot", fig, title = "Test Figure")
    dfig.columns = 2
    dfig.background_color = (0.2, 0.2, 0.2, 1.0)
    dfig.border_width = 10.0
    dfig.border_color = "black"
    dfig.save(Path("CurveFit_test.png"))
    print(dfig)
