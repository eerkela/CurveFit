from __future__ import annotations
from math import ceil
from pathlib import Path
from typing import Optional, Union

import matplotlib as mpl
from matplotlib.gridspec import GridSpec, SubplotSpec
import matplotlib.pyplot as plt

from . import NUMERIC, NUMERIC_TYPECHECK
from .color import color_diff
from .shape import DynamicRectangle
from .text import DynamicText

"""
TODO: Implement Sphinx documentation
"""


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
