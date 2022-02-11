from __future__ import annotations
from pathlib import Path
import re
from typing import Union

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, fmin
import sympy as sym
from sympy.utilities.lambdify import lambdify
# from sympy.utilities.autowrap import ufuncify  # speedup over lambdify
from sympy.parsing.sympy_parser import parse_expr


def decompose_r_func(formula: str) -> tuple[str, str, sym.core.expr.Expr]:
    """Parses R-style fit formula (`response ~ terms`), decomposing it into
    its component parts and casting `terms` to a symbolic sympy function.
    """
    if formula.count("~") != 1:
        err_msg = (f"[decompose_r_func] Could not decompose r-style fit "
                   f"formula: `formula` is malformed (expected `response ~ "
                   f"terms`, received `{formula}`)")
        raise ValueError(err_msg)
    dep_var, str_func = tuple(map(str.strip, re.split("~", formula)))
    sym_func = parse_expr(str_func)
    return (dep_var, str_func, sym_func)


def identify_vars(sym_func: sym.core.expr.Expr,
                  dep_var: str,
                  data_cols: list[str],
                  n_vars: int = None
    ) -> tuple[set[sym.Symbol], set[sym.Symbol]]:
    """Identifies independent variable(s) and fit parameters in symbolic sympy
    function via comparison against `data_cols`.
    """
    ind_vars = set([s for s in sym_func.free_symbols if str(s) in data_cols])
    fit_pars = set([s for s in sym_func.free_symbols if s not in ind_vars])
    if dep_var not in data_cols:
        err_msg = (f"[identify_vars] Could not identify fit variables: "
                    f"dependent variable `{dep_var}` was not detected in "
                    f"columns of `data` (columns: `{data_cols}`)")
        raise ValueError(err_msg)
    if n_vars is not None and len(ind_vars) != n_vars:
        err_msg = (f"[identify_vars] Could not identify fit variables: "
                   f"`sym_func` must have exactly {n_vars} independent "
                   f"variable(s) (candidates: `{data_cols}`, sym_func: "
                   f"`{sym_func}`)")
        raise ValueError(err_msg)
    if len(fit_pars) < 1:
        err_msg = (f"[identify_vars] Could not identify fit variables: "
                   f"`sym_func` contains no fit parameters (`{sym_func}` must "
                   f"have at least one free variable other than `{ind_vars}`)")
        raise ValueError(err_msg)
    return (ind_vars, fit_pars)


def filter_data(data: pd.DataFrame,
                to_keep: list[str],
                uncertainties: dict[str, str] = None,
                drop_na: bool = True,
                numeric_only: bool = True,
                min_points: int = 2) -> pd.DataFrame:
    """Removes unwanted columns from `data`, not including those marked as
    containing uncertainty information of the `to_keep` variables.
    """
    if uncertainties is not None:
        for k, v in uncertainties.items():
            if k not in to_keep:
                err_msg = (f"[filter_data] Could not filter data: invalid key "
                           f"in uncertainty map (`{k}` does not reference "
                           f"independent/dependent variables: `{to_keep}`")
                raise ValueError(err_msg)
            if v not in data:
                err_msg = (f"[filter_data] Could not filter data: invalid "
                           f"value in uncertainty map (`{v}` does not "
                           f"reference a column name in `data`: "
                           f"`{data.columns}`)")
                raise ValueError(err_msg)
        to_keep.extend(uncertainties.values())
    filtered = data[to_keep]
    if numeric_only:
        numeric_cols = list(filtered.select_dtypes(include=np.number).columns)
        data_cols = list(filtered.columns)
        if len(numeric_cols) != len(data_cols):
            err_msg = (f"[filter_data] Could not filter data: `data` must "
                       f"contain only numeric values, after filtering columns "
                       f"(detected non-numerics in `{data_cols-numeric_cols}`)")
            raise ValueError(err_msg)
    if drop_na:
        filtered = filtered.dropna()
        if len(filtered) < min_points:
            err_msg = (f"[filter_data] Could not filter data: `data` must "
                       f"contain at least {min_points} data points, after "
                       f"filtering columns and removing missing values "
                       f"(received {len(filtered)})")
            raise ValueError(err_msg)
    return filtered


def gather_guesses_from_kwargs(keys: list[str],
                               random_seed = 12345,
                               **kwargs) -> dict[str, float]:
    """Gathers initial fit parameter guesses and/or bounds from a **kwargs dict
    and casts to scipy.optimize.curve_fit format:

        tuple(p0 = [...], bounds = ([...], [...]))

    Supports interpretation of tuple values as (min, max) parameter bounds.
    """
    p0 = []
    bounds = ([], [])
    for k in kwargs:
        if k not in keys:
            err_msg = (f"[gather_guesses_from_kwargs] Could not gather "
                       f"parameter guesses/bounds: parameter `{k}` was not "
                       f"recognized (available parameters: `{keys}`)")
            raise ValueError(err_msg)
    for k in keys:
        if k not in kwargs:
            p0.append(1)  # default value in scipy.optimize.curve_fit
            bounds[0].append(-np.inf)  # disables parameter bounds in curve_fit
            bounds[1].append(np.inf)   # ^
            continue
        val = kwargs[k]
        if not issubclass(type(val), (int, float, tuple)):
            err_msg = (f"[gather_guesses_from_kwargs] Could not gather "
                       f"parameter guesses/bounds: parameter `{k}` must be "
                       f"assigned either an int, float, or tuple of "
                       f"ints/floats (received: `{val}`)")
            raise TypeError(err_msg)
        if issubclass(type(val), tuple):
            if len(val) != 2:
                err_msg = (f"[gather_guesses_from_kwargs] Could not gather "
                           f"parameter guesses/bounds: parameter `{k}` was "
                           f"assigned a bounding tuple of unexpected length "
                           f"(expected tuple of length 2, received `{val}`)")
                raise ValueError(err_msg)
            allowed_types = (int, float, type(None))
            if not all(issubclass(type(i), allowed_types) for i in val):
                err_msg = (f"[gather_guesses_from_kwargs] Could not gather "
                           f"parameter guesses/bounds: parameter `{k}` was "
                           f"assigned a bounding tuple of invalid type (all "
                           f"elements must be int/float/None, received: "
                           f"`{val}`)")
                raise TypeError(err_msg)
            # interpret bounds
            if val[0] is None and val[1] is None:  # no bounds
                p0.append(1)  # default value in scipy.optimize.curve_fit
                bounds[0].append(-np.inf)
                bounds[1].append(np.inf)
            elif val[0] is None:  # no lower bound
                p0.append(val[1])  # initialize at max value
                bounds[0].append(-np.inf)
                bounds[1].append(val[1])
            elif val[1] is None:  # no upper bound
                p0.append(val[0])  # initialize at min value
                bounds[0].append(val[0])
                bounds[1].append(np.inf)
            else:
                val = sorted(val)
                rng = np.random.default_rng(random_seed)
                p0.append(rng.uniform(val[0], val[1]))
                bounds[0].append(val[0])
                bounds[1].append(val[1])
        else:  # val is a single int/float
            p0.append(val if val is not None else 1)
            bounds[0].append(-np.inf)
            bounds[1].append(np.inf)
    return (p0, bounds)


def covariance_to_correlation(cov_mat: pd.DataFrame) -> pd.DataFrame:
    """Convert covariance matrix into correlation matrix of the same form."""
    par_names = list(cov_mat.columns)
    rows, cols = cov_mat.shape  # should be square
    corr_mat = np.full((rows, cols), None)
    for i in range(rows):
        for j in range(cols):
            covar = cov_mat.iloc[i, j]
            x_var = cov_mat.iloc[i, i]
            y_var = cov_mat.iloc[j, j]
            if any(var == 0 for var in [x_var, y_var]):
                corr_mat[i, j] = np.nan
            else:
                corr_mat[i, j] = covar / np.sqrt(x_var * y_var)
    return pd.DataFrame(corr_mat, columns = par_names, index = par_names)


class SymFunc:

    def __init__(self, str_func: str):
        raise NotImplementedError()

    def derivative(self, with_respect_to: Union[str, sym.Symbol]) -> SymFunc:
        raise NotImplementedError()

    def intersection(self, other: Union[str, SymFunc]):
        raise NotImplementedError()

    def maximum(self, around) -> float:
        raise NotImplementedError()

    def minimum(self, around) -> float:
        raise NotImplementedError()

    def plot(self, *) -> None:
        raise NotImplementedError()

    def substitute(self):
        raise NotImplementedError()

    def __call__(self, *) -> float:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()


class GeneralizedFitFunc:

    """
    Private:
        _data
        _orig_function
        _dep_var
        _str_func
        _sym_func
        _ind_vars
        _fit_pars
        _covariance
        _correlation
        _adj_r_squared
        _chi_squared

    """

    def __init__(self, data: pd.DataFrame, function: str):
        """Column names should match independent variables in expression.
        Everything else will be interpreted as a free parameter for fits.

        Use r-style:   y ~ a * x + b
        match vars to columns to determine dependent and independent
        """
        # TODO: check for missing values, or implement an na_rm flag
        # TODO: check that all columns are numerical
        # check for sufficient data points
        if len(data) < 2:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not initialize FitFunc: `data` "
                       f"must have at least 2 data points to perform fit "
                       f"(received {len(data)})")
            raise ValueError(err_msg)
        self._data = data

        # check that function is of expected form (`response ~ terms`)
        if function.count("~") != 1:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not initialize FitFunc: "
                       f"`function` is malformed (expected `response ~ terms`, "
                       f"received `{function}`)")
            raise ValueError(err_msg)
        self._orig_function = function

        # parse function for dependent variable and fit equation
        parts = tuple(map(str.strip, re.split("~", self._orig_function)))
        dep_var, str_func = parts
        if dep_var not in self._data.columns:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not initialize FitFunc: "
                       f"dependent variable `{dep_var}` was not detected in "
                       f"columns of `data` (columns: {self._data.columns})")
            raise ValueError(err_msg)
        self._dep_var = dep_var
        self._str_func = str_func

        # convert fit equation to symbolic function and identify independent
        # variables + fit parameters via introspection
        sym_func = parse_expr(str_func)
        ind_vars = set([sym.Symbol(c) for c in data.columns if c in str_func])
        fit_pars = set([s for s in sym_func.free_symbols if s not in ind_vars])
        if len(ind_vars) < 1:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not initialize FitFunc: "
                       f"`function` must have at least one independent "
                       f"variable (column names: `{self._data.columns}`, "
                       f"function: `{self._orig_function}`)")
            raise ValueError(err_msg)
        if len(fit_pars) < 1:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not initialize FitFunc: "
                       f"`function` contains no parameters to fit (column "
                       f"names: `{self._data.columns}`, function: "
                       f"`{self._orig_function}`)")
            raise ValueError(err_msg)
        self._sym_func = sym_func
        self._ind_vars = ind_vars

        # initialize parameter dictionary, preserving order from input function
        in_order = sorted(fit_pars, key=lambda s: self._str_func.index(str(s)))
        self._fit_pars = dict.fromkeys(in_order, None)
        # as of python 3.7, dict preserves insertion order by default.  For
        # python <= 3.6, replace above with the following:
        # from collections import OrderedDict
        # self._fit_pars = OrderedDict.fromkeys(in_order, None)

        # keep only columns of data that are referenced in function
        to_keep = set(map(str, self._ind_vars.copy()))
        to_keep.add(self._dep_var)
        self._data = self._data[[*to_keep]]

    @classmethod
    def from_simulated(cls,
                       func: Union[str, sym.core.expr.Expr],
                       ind_var: Union[str, sym.Symbol],
                       par_values: dict[Union[str, sym.Symbol], float],
                       *args,
                       start: float = 0,
                       stop: float = 10,
                       num_points: int = 20,
                       noise: float = 1,
                       seed = 12345):
        # TODO: generalize to higher dimensions
        if issubclass(type(func), str):
            func = parse_expr(func)
        if issubclass(type(ind_var), str):
            ind_var = sym.Symbol(ind_var)
        if ind_var not in func.free_symbols:
            class_name = cls.__name__
            err_msg = (f"[{class_name}] Could not generate simulated data: "
                       f"`func` must contain the symbol identified in "
                       f"`ind_var` (expected '{str(func)}' to contain "
                       f"'{str(ind_var)})'")
            raise ValueError(err_msg)

        # substitute in parameter values and create lambda function
        sub_func = func.subs(par_values)
        if len(sub_func.free_symbols) != 1:
            class_name = cls.__name__
            err_msg = (f"[{class_name}] Could not generate simulated data: "
                       f"after substituting `par_values`, `func` must have "
                       f"exactly 1 free variable remaining ({str(sub_func)})")
            raise ValueError(err_msg)
        lam_func = lambdify(ind_var, sub_func, "numpy")

        # generate simulated data
        rng = np.random.default_rng(seed)
        xdata = np.linspace(start, stop, num_points)
        y = np.array([lam_func(x) for x in xdata])
        y_noise = noise * rng.normal(size=xdata.size)
        ydata = y + y_noise
        data = pd.DataFrame({str(ind_var): xdata, "data": ydata})
        return cls(data, func)

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    @property
    def function(self) -> sym.core.expr.Expr:
        return self._sym_func

    @property
    def independent_variables(self) -> set[sym.Symbol]:
        return self._ind_vars

    @property
    def fit_parameters(self) -> dict[sym.Symbol, float]:
        return self._fit_pars

    @property
    def covariance_matrix(self) -> pd.DataFrame:
        if self._lambda_func is None:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not generate covariance matrix: "
                       f"function has not yet been fitted")
            raise RuntimeError(err_msg)
        return self._covariance

    @property
    def correlation_matrix(self) -> pd.DataFrame:
        raise NotImplementedError()

    @property
    def residuals(self) -> pd.DataFrame:
        # TODO: generalize to higher dimensions
        if self._lambda_func is None:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not generate residuals: function "
                       f"has not yet been fitted")
            raise RuntimeError(err_msg)

        if self._residuals is not None:
            return self._residuals
        columns = list(self.data.columns)
        observed = columns[len(columns) - columns.index(str(self._ind_var)) - 1]
        get_expected = lambda x: self._lambda_func(x[str(self._ind_var)])
        get_residual = lambda x: x[observed] - x["expected"]
        df = self.data.assign(expected = get_expected, residual = get_residual)
        self._residuals = df[[str(self._ind_var), "residual"]]
        return self._residuals

    @property
    def degrees_of_freedom(self) -> int:
        return len(self.data) - len(self.fit_parameters)

    @property
    def r_squared(self) -> float:
        raise NotImplementedError()

    @property
    def adjusted_r_squared(self) -> float:
        """Returns the adjusted r-squared coefficient of determination for the
        current fit.
        """
        # TODO: update for new model
        if self._adj_r_squared is not None:
            return self._adj_r_squared
        residuals = list(self.residuals["residual"])
        observed = list(self.data[self._result_column])
        n_obs = len(observed)
        avg_obs = sum(observed) / n_obs

        SS_res = sum([e**2 for e in residuals])
        SS_tot = sum([(obs - avg_obs)**2 for obs in observed])
        df_t = n_obs - 1
        df_e = self.degrees_of_freedom - 1
        self._adj_r_squared = 1 - ((SS_res/df_e) / (SS_tot/df_t))
        return self._adj_r_squared

    @property
    def chi_squared(self) -> float:
        """Returns the reduced chi-square statistic for the current fit."""
        # TODO: update for new model
        if self._chi_squared is not None:
            return self._chi_squared
        residuals = list(self.residuals["residual"])
        SS_res = sum([e**2 for e in residuals])
        self._chi_squared = SS_res / self.degrees_of_freedom
        return self._chi_squared

    @property
    def info(self) -> tuple[str]:
        # contents
        # 0 - original fit function
        # 1 - observation data
        # 2 - fit parameters
        # 3 - covariance matrix
        # 4 - adjusted r squared
        # 5 - chi squared
        raise NotImplementedError()

    def derivative(self, with_respect_to: Union[str, sym.Symbol]) -> FitFunc:
        """Returns a partial derivative of the current FitFunc with respect to
        the indicated variable.  Interpolates new values for the dependent
        variable, scaling residuals appropriately.
        """
        if issubclass(type(with_respect_to), str):
            with_respect_to = sym.Symbol(with_respect_to)
        if with_respect_to not in self._ind_vars:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not calculate derivative of "
                       f"FitFunc: `with_respect_to` was not recognized as "
                       f"an independent variable (expected `{self._ind_vars}`, "
                       f"received `{with_respect_to}`)")
            raise ValueError(err_msg)

        sym_deriv = sym.diff(self._sym_func, with_respect_to)
        ind_vars = [s for s in sym_deriv.free_symbols if s in self._ind_vars]
        lam_deriv = lambdify(ind_vars, sym_deriv, "numpy")

        # interpolate `dep_var` column of data
        interp = {self._dep_var: lambda x: lam_deriv(*[x[i] for i in ind_vars])}
        data = self._data[[*ind_vars]].assign(**interp)

        # scale residuals
        # TODO: get scaling coefficient, multiply by residuals, add to data

        function = f"{str(self.dep_var)} ~ {str(sym_deriv)}"
        return FitFunc(data, function)

    def fit(self, p0: dict[Union[str, sym.Symbol],
                           Union[float, tuple[float]]] = None) -> None:
        """TODO: implement parameter guesses (maybe use kwargs?).
        if p0 values are given as tuples, they are interpreted as a bounded
        range, else they are unbounded guesses.
        sorted(dict, key = ...) works to sort dictionaries by key

        TODO: return a FitInfo object
        """
        if self._ind_var not in self._sym_func.free_symbols:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Invalid sympy function: `function` "
                       f"must contain the same independent variable as "
                       f"FitFunc.data (expected '{str(self._sym_func)}' to "
                       f"contain independent variable '{str(self._ind_var)}')")
            raise ValueError(err_msg)

        # identify columns
        x = list(self.data[str(self._ind_var)])
        y = list(self.data[self._result_column])

        # set up lambda function and perform fit
        variables = [self._ind_var, *self._fit_pars.keys()]
        fit_func = lambdify(variables, self._sym_func, "numpy")
        par_values, covariance = curve_fit(fit_func, x, y)

        # gather fit parameters
        for k, v in zip(self._fit_pars.keys(), par_values):
            self._fit_pars[k] = v

        # format covariance/correlation matrix
        par_names = list(map(str, self._fit_pars.keys()))
        self._covariance = pd.DataFrame(covariance, columns = par_names,
                                        index = par_names)
        # rows = cols = len(par_names)
        # self.correlation = np.zeros((rows, cols))
        # for i in range(rows):
        #     for j in range(cols):
        #         cov = self.covariance[i, j]
        #         x_var = self.covariance[i, i]
        #         y_var = self.covariance[j, j]
        #         self.correlation[i, j] = cov / np.sqrt(x_var * y_var)

        # assign fitted lambda function
        fit_func = self._sym_func.subs(self._fit_pars)
        self._lambda_func = lambdify(self._ind_var, fit_func, "numpy")

    def intersection(self, other: FitFunc, x0: float, tolerance: float = 1e-8,
                     recursion_limit: int = 1000) -> float:
        # TODO: move this to a specific, 1D case
        # newton-raphson gradient descent
        this_deriv = self.derivative(with_respect_to = ind_var)
        other_deriv = other.derivative(with_respect_to = ind_var)
        f = lambda x: self.__call__(x) - other.__call__(x)
        f_prime = lambda x: this_deriv.__call__(x) - other_deriv.__call__(x)
        recursion_depth = 0
        while abs(f(x0)) > tolerance:
            x0 = x0 - f(x0) / f_prime(x0)
            recursion_depth += 1
            if recursion_depth > recursion_limit:
                class_name = self.__class__.__name__
                err_msg = (f"[{class_name}] Could not compute "
                            f"intersection: recursion_limit reached "
                            f"({recursion_limit})")
                raise RecursionError(err_msg)
        return x0

    def maximum(self, around: float) -> float:
        # reflect function, then minimize
        raise NotImplementedError()

    def minimum(self, around: float) -> float:
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fmin.html
        raise NotImplementedError()

    def plot(self):
        raise NotImplementedError()

    def t_test(self, hypothesis: str, alpha: float = None, plot: bool = False,
               save_to: Path = None) -> Union[float, bool]:
        """two-tailed t_test (one-sided optional).  Returns p-value of a
        particular proposed parameter value.  If alpha is given, returns
        boolean.

        Maybe pass in alternative hypothesis as a string?  e.g. "a=2" would
        imply a two-sided hypothesis test.  "a > 2" would be one-sided.
        """
        # TODO: finish writing test logic
        comp = re.findall("(={1,2}|<=|>=|<|>)", hypothesis)
        if len(comp) != 1:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not perform t-test: "
                       f"`hypothesis` must have exactly one of the following "
                       f"(in)equality operators: ['=', '==', '>', '>=', '<', "
                       f"'<='] (received {comp})")
            raise ValueError(err_msg)

        lhs, rhs = list(map(str.strip, re.split(comp[0], hypothesis)))
        # check lhs is in par_values and rhs is a number

        if any(c in comp for c in ["=", "=="]):  # two-tailed
            pass
        if any(c in comp for c in [">", ">="]):  # right-tailed
            pass
        if any(c in comp for c in ["<", "<="]):  # left-tailed
            pass
        raise NotImplementedError()

    def __call__(self, x) -> float:
        if self._lambda_func is None:
            self.fit()
        return self._lambda_func(x)

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self):
        raise NotImplementedError()

    def __str__(self) -> str:
        return str(self.function)


class CurveFit:

    """
    Private:
        _data
        _uncertainties
        _ind_var
        _dep_var
        _orig_formula
        _str_func
        _sym_func
        _lam_func
        _fit_pars
        _covariance
        _correlation
        _chi_squared
        _adj_r_squared
        _r_squared
        _residuals
    """

    def __init__(self, data: pd.DataFrame, formula: str,
                 uncertainties: dict[str, str] = None):
        """Column names should match independent variables in expression.
        Everything else will be interpreted as a free parameter for fits.

        Use r-style:   y ~ a * x + b
        match vars to columns to determine dependent and independent
        """
        dep_var, str_func, sym_func = decompose_r_func(formula)
        ind_vars, fit_pars = identify_vars(sym_func, dep_var,
                                           list(data.columns), n_vars = 1)
        to_keep = [*list(map(str, ind_vars)), dep_var]
        data = filter_data(data, to_keep, uncertainties, drop_na=True,
                           numeric_only=True, min_points=2)

        # assign private fields
        self._orig_formula = formula
        self._str_func = str_func
        self._sym_func = sym_func
        self._dep_var = dep_var
        self._ind_var = ind_vars.pop()
        self._data = data

        # initialize fit parameter dictionary, preserving order from input func
        in_order = sorted(fit_pars, key=lambda s: self._str_func.index(str(s)))
        self._fit_pars = dict.fromkeys(in_order, None)

        # as of python 3.7, dict preserves insertion order by default.  For
        # python <= 3.6, replace above with the following:
        # from collections import OrderedDict
        # self._fit_pars = OrderedDict.fromkeys(in_order, None)

        if uncertainties is not None:
            self._uncertainties = uncertainties

    @classmethod
    def from_simulated(cls,
                       formula: str,
                       ind_var: str,
                       par_values: dict[str, float],
                       *,
                       start: float = 0,
                       stop: float = 10,
                       num_points: int = 10,
                       noise: float = 1,
                       x_uncertain: bool = False,
                       y_uncertain: bool = False,
                       mag_uncertain: float = 1,
                       seed = 12345):
        """Returns a new CurveFit object from randomly-generated simulation
        data, following the relationship specified in `formula`
        """
        # check that formula is of expected form (`response ~ terms`)
        decomposed = decompose_r_func(formula)
        dep_var, _, sym_func = decomposed
        ind_var = sym.Symbol(ind_var)
        if ind_var not in sym_func.free_symbols:
            err_msg = (f"[{cls.__name__}.from_simulated] Could not generate "
                       f"simulation data: `formula` must contain the symbol "
                       f"identified in  `ind_var` (expected `{str(formula)}` "
                       f"to contain `{str(ind_var)})`")
            raise ValueError(err_msg)

        # substitute in parameter values and create lambda function
        sub_func = sym_func.subs(par_values)
        if len(sub_func.free_symbols) != 1:
            err_msg = (f"[{cls.__name__}.from_simulated] Could not generate "
                       f"simulation data: after substituting `par_values`, "
                       f"`formula` must have exactly 1 free variable "
                       f"remaining ({str(sub_func)})")
            raise ValueError(err_msg)
        lam_func = lambdify(ind_var, sub_func, "numpy")

        # generate simulated data
        x_data = np.linspace(start, stop, num_points)
        y = lam_func(x_data)
        rng = np.random.default_rng(seed)
        y_noise = noise * rng.normal(size=x_data.size)
        y_data = y + y_noise
        data = pd.DataFrame({str(ind_var): x_data, dep_var: y_data})

        # add simulated uncertainties if applicable
        if x_uncertain or y_uncertain:
            uncertainties = {}
            if x_uncertain:
                x_unc = abs(mag_uncertain * rng.normal(size=x_data.size))
                x_unc_col = f"{str(ind_var)}_unc"
                data[x_unc_col] = x_unc
                uncertainties[str(ind_var)] = x_unc_col
            if y_uncertain:
                y_unc = abs(mag_uncertain * rng.normal(size=y_data.size))
                y_unc_col = f"{dep_var}_unc"
                data[y_unc_col] = y_unc
                uncertainties[dep_var] = y_unc_col
            return cls(data, formula, uncertainties)
        return cls(data, formula)

    @property
    def adjusted_r_squared(self) -> float:
        """Returns the adjusted r-squared coefficient of determination for the
        current fit.
        """
        if hasattr(self, "_adj_r_squared") and self._adj_r_squared is not None:
            return self._adj_r_squared
        residuals = list(self.residuals["residual"])
        observed = list(self._data[self._dep_var])
        n_obs = len(observed)
        avg_obs = sum(observed) / n_obs
        SS_res = sum([e**2 for e in residuals])
        SS_tot = sum([(obs - avg_obs)**2 for obs in observed])
        df_t = n_obs - 1
        df_e = self.degrees_of_freedom - 1
        self._adj_r_squared = 1 - ((SS_res/df_e) / (SS_tot/df_t))
        return self._adj_r_squared

    @property
    def chi_squared(self) -> float:
        """Returns the reduced chi-square statistic for the current fit."""
        if hasattr(self, "_chi_squared") and self._chi_squared is not None:
            return self._chi_squared
        residuals = list(self.residuals["residual"])
        SS_res = sum([e**2 for e in residuals])
        self._chi_squared = SS_res / self.degrees_of_freedom
        return self._chi_squared

    @property
    def degrees_of_freedom(self) -> int:
        return len(self._data) - len(self._fit_pars)

    @property
    def fitted(self) -> bool:
        if hasattr(self, "_lambda_func"):
            return self._lambda_func is not None
        return False

    @property
    def r_squared(self) -> float:
        if hasattr(self, "_r_squared") and self._r_squared is not None:
            return self._r_squared
        residuals = list(self.residuals["residual"])
        observed = list(self._data[self._dep_var])
        n_obs = len(observed)
        avg_obs = sum(observed) / n_obs
        SS_res = sum([e**2 for e in residuals])
        SS_tot = sum([(obs - avg_obs)**2 for obs in observed])
        self._r_squared = 1 - (SS_res / SS_tot)
        return self._r_squared

    @property
    def residuals(self) -> Residuals:
        if not self.fitted:
            err_msg = (f"[{self.__class__.__name__}.residuals] Could not "
                       f"compute residuals: CurveFit has not yet been fitted")
            raise RuntimeError(err_msg)
        if hasattr(self, "_residuals") and self._residuals is not None:
            return self._residuals
        get_expected = lambda x: self._lambda_func(x[str(self._ind_var)])
        get_residual = lambda x: x[self._dep_var] - x["expected"]
        df = self._data.assign(expected = get_expected, residual = get_residual)
        self._residuals = df[[str(self._ind_var), "residual"]]
        return self._residuals

    # def derivative(self) -> CurveFit:
    #     return CurveFit(self._data, sym.diff(self._sym_func, self._ind_var))

    def fit(self, random_seed = None, **kwargs) -> None:
        """TODO: return a FitInfo object."""
        x_data = list(self._data[str(self._ind_var)])
        y_data = list(self._data[self._dep_var])

        # set up lambda function
        variables = [self._ind_var, *self._fit_pars.keys()]
        fit_func = lambdify(variables, self._sym_func, "numpy")

        # gather parameter guesses/bounds, variable uncertainties, then fit
        keys = list(map(str, self._fit_pars.keys()))
        p0, bounds = gather_guesses_from_kwargs(keys, **kwargs)
        if hasattr(self, "_uncertainties"):
            if str(self._ind_var) in self._uncertainties:
                # perform Orthogonal Distance Regression (see scipy docs)
                raise NotImplementedError()
            else:
                sigma = list(self._data[self._uncertainties[self._dep_var]])
                fit_kwargs = {"p0": p0, "bounds": bounds, "sigma": sigma,
                              "absolute_sigma": True}
                par_v, cov = curve_fit(fit_func, x_data, y_data, **fit_kwargs)
        else:
            par_v, cov = curve_fit(fit_func, x_data, y_data,
                                               p0=p0, bounds=bounds)

        # gather fit parameters
        for k, v in zip(self._fit_pars, par_v):
            self._fit_pars[k] = v

        # format covariance/correlation matrix
        par_names = list(map(str, self._fit_pars.keys()))
        self._covariance = pd.DataFrame(cov, columns=par_names, index=par_names)
        self._correlation = covariance_to_correlation(self._covariance)

        # assign fitted lambda function
        fit_func = self._sym_func.subs(self._fit_pars)
        self._lambda_func = lambdify(self._ind_var, fit_func, "numpy")

    def intersection(self, other: FitFunc, x0: float, tolerance: float = 1e-8,
                     recursion_limit: int = 1000) -> float:
        # newton-raphson gradient descent
        this_deriv = self.derivative(with_respect_to = ind_var)
        other_deriv = other.derivative(with_respect_to = ind_var)
        f = lambda x: self.__call__(x) - other.__call__(x)
        f_prime = lambda x: this_deriv.__call__(x) - other_deriv.__call__(x)
        recursion_depth = 0
        while abs(f(x0)) > tolerance:
            x0 = x0 - f(x0) / f_prime(x0)
            recursion_depth += 1
            if recursion_depth > recursion_limit:
                class_name = self.__class__.__name__
                err_msg = (f"[{class_name}] Could not compute "
                            f"intersection: recursion_limit reached "
                            f"({recursion_limit})")
                raise RecursionError(err_msg)
        return x0

    def maximum(self, around: float) -> float:
        # reflect function, then minimize
        raise NotImplementedError()

    def minimum(self, around: float) -> float:
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fmin.html
        raise NotImplementedError()

    def plot(self,
             *,
             height: float = None,
             width: float = None,
             background_color: str = None,
             foreground_color: str = None,
             title: str = None,
             x_label: str = None,
             y_label: str = None,
             legend: bool = True,
             x_lim: Union[float, tuple[float, float]] = None,
             y_lim: Union[float, tuple[float, float]] = None,
             log_x: bool = False,
             log_y: bool = False,
             data_alpha: float = 1,
             data_color: str = None,
             data_marker: Union[str, Path] = "s",
             data_size: float = None,
             data_label: str = None,
             errorbar_alpha: float = None,
             errobar_color: str = None,
             errorbar_width: float = None,
             errorbar_capsize: float = None, 
             fit_alpha: float = 0.8,
             fit_color: str = None,
             fit_line_style: str = "solid",
             fit_line_width: float = None,
             fit_label: str = None,
             add_to_figure: bool = False,
             add_to_subplot: bool = False,
             subplots_per_row: int = 3,
             save_to: Path = None) -> None:
        """Plots the current fit data and trend line, along with error bars if
        applicable.

        Named colors in matplotlib:
            https://matplotlib.org/stable/gallery/color/named_colors.html

        TODO: directly reference figure rather than using `add_to_figure`
        TODO: ^ same with axis
        """
        # get figure
        if not add_to_figure:  # create new figure
            fig = plt.figure(constrained_layout=True)
            # configure fig
            if width is not None:
                fig.set_figwidth(width)
            if height is not None:
                fig.set_figheight(height)
            if background_color is not None:
                fig.set_facecolor(background_color)
        else:  # add to existing figure
            fig = plt.gcf()

        # get axes
        if not add_to_subplot:  # create new axes/subplot
            size = len(fig.get_axes())
            if size > 0:
                orig_gs = fig.axes[0].get_subplotspec() \
                                     .get_topmost_subplotspec() \
                                     .get_gridspec()
                rows, cols =  orig_gs.get_geometry()
                # search for first empty subplot
                gen = (i for i, j in enumerate(fig.axes) if not j.has_data())
                first_empty = next(gen, size)
                if first_empty >= rows * cols:  # add a new column/row
                    old_width, old_height = fig.get_size_inches()
                    if cols < subplots_per_row:  # add a column
                        fig.set_figwidth(old_width * (cols + 1) / cols)
                        new_gs = gridspec.GridSpec(rows, cols + 1)
                    else:  # add a row
                        fig.set_figheight(old_height * (rows + 1) / rows)
                        new_gs = gridspec.GridSpec(rows + 1, cols)
                    for i in range(size): # reposition existing subplots
                        new_sps = gridspec.SubplotSpec(new_gs, i)
                        fig.axes[i].set_subplotspec(new_sps)
                    new_sps = gridspec.SubplotSpec(new_gs, first_empty)
                    ax = fig.add_subplot(new_sps)
                else:
                    if first_empty < size:  # found an empty subplot
                        fig.axes[first_empty].remove()
                    new_sps = gridspec.SubplotSpec(orig_gs, first_empty)
                    ax = fig.add_subplot(new_sps)
            else:
                ax = fig.add_subplot(1, 1, 1)

            if foreground_color is not None:
                ax.set_facecolor(foreground_color)
            # labels
            if title is not None:
                ax.set_title(title)
            else:
                ax.set_title(f"CurveFit: {self._orig_formula}")
            if x_label is not None:
                ax.set_xlabel(x_label)
            else:
                ax.set_xlabel(str(self._ind_var))
            if y_label is not None:
                ax.set_ylabel(y_label)
            else:
                ax.set_ylabel(self._dep_var)
            # limits
            if x_lim is not None:
                if issubclass(type(x_lim), tuple):
                    ax.set_xlim(left=x_lim[0], right=x_lim[1])
                else:
                    ax.set_xlim(right=x_lim)
            if y_lim is not None:
                if issubclass(type(y_lim), tuple):
                    ax.set_ylim(left=y_lim[0], right=y_lim[1])
                else:
                    ax.set_ylim(right=y_lim)
        else:  # add to existing axes/subplot
            ax = plt.gca()

        # plot scatter data
        if data_label is not None:
            label = data_label
        else:
            label = f"Observed {self._dep_var}"
        plt.scatter(str(self._ind_var),
                    self._dep_var,
                    s=data_size,
                    c=data_color,
                    marker=data_marker,
                    alpha=data_alpha,
                    data=self._data,
                    label=label)

        # add error bars if applicable:
        if hasattr(self, "_uncertainties"):
            if str(self._ind_var) in self._uncertainties:  # include x errors
                plt.errorbar(str(self._ind_var),
                             self._dep_var,
                             xerr=self._uncertainties[str(self._ind_var)],
                             yerr=self._uncertainties[self._dep_var],
                             ecolor=errobar_color,
                             alpha=errorbar_alpha,
                             elinewidth=errorbar_width,
                             capsize=errorbar_capsize,
                             linestyle="",
                             data=self._data)
            else:  # only has y errors
                plt.errorbar(str(self._ind_var),
                             self._dep_var,
                             yerr=self._uncertainties[self._dep_var],
                             ecolor=errobar_color,
                             alpha=errorbar_alpha,
                             elinewidth=errorbar_width,
                             capsize=errorbar_capsize,
                             linestyle="",
                             data=self._data)

        # add fit line:
        min_x, max_x = sorted(ax.get_xlim())
        min_x = int(np.floor(self._data[str(self._ind_var)].min()))
        max_x = int(np.ceil(self._data[str(self._ind_var)].max()))
        x_fitted = np.linspace(min_x, max_x, 10 * (max_x - min_x))
        y_fitted = self.__call__(x_fitted)
        if fit_label is not None:
            label = fit_label
        else:
            label = f"Predicted {self._dep_var}"
        plt.plot(x_fitted,
                 y_fitted,
                 c=fit_color,
                 ls=fit_line_style,
                 lw=fit_line_width,
                 alpha=fit_alpha,
                 label=label)

        # configure scale/legend
        if log_x:
            plt.xscale("symlog")
        if log_y:
            plt.yscale("symlog")
        if legend:
            plt.legend()
        plt.tight_layout()

        # display plot:
        if save_to is None:
            plt.show()
        else:
            plt.savefig(save_to)

    def t_test(self, hypothesis: str, alpha: float = None, plot: bool = False,
               save_to: Path = None) -> Union[float, bool]:
        """two-tailed t_test (one-sided optional).  Returns p-value of a
        particular proposed parameter value.  If alpha is given, returns
        boolean.

        Maybe pass in alternative hypothesis as a string?  e.g. "a=2" would
        imply a two-sided hypothesis test.  "a > 2" would be one-sided.
        """
        comp = re.findall("(={1,2}|<=|>=|<|>)", hypothesis)
        if len(comp) != 1:
            class_name = self.__class__.__name__
            err_msg = (f"[{class_name}] Could not perform t-test: "
                       f"`hypothesis` must have exactly one of the following "
                       f"(in)equality operators: ['=', '==', '>', '>=', '<', "
                       f"'<='] (received {comp})")
            raise ValueError(err_msg)

        lhs, rhs = list(map(str.strip, re.split(comp[0], hypothesis)))
        # check lhs is in par_values and rhs is a number

        if any(c in comp for c in ["=", "=="]):  # two-tailed
            pass
        if any(c in comp for c in [">", ">="]):  # right-tailed
            pass
        if any(c in comp for c in ["<", "<="]):  # left-tailed
            pass
        raise NotImplementedError()

    def __call__(self, x: Union[float, np.array], **kwargs) -> float:
        if not self.fitted:
            self.fit(**kwargs)
        return self._lambda_func(x)

    def __str__(self) -> str:
        if self.fitted:
            short = {k: np.round(self._fit_pars[k], 4) for k in self._fit_pars}
            return str(self._sym_func.subs(short))
        return str(self._sym_func)


class Residuals:

    def __init__(self, res_df: pd.DataFrame):
        if "residual" not in res_df.columns:
            err_msg = ()
            raise ValueError(err_msg)

    @property
    def sum_squares(self) -> float:
        raise NotImplementedError()

    def histogram(self, save_to: Path = None):
        raise NotImplementedError()

    def plot(self, save_to: Path = None):
        raise NotImplementedError()

    def qq_plot(self, save_to: Path = None):
        raise NotImplementedError()

    def rescale(self, coef: float):
        raise NotImplementedError()


def main() -> None:
    formula = "y ~ a * exp(b * x) + c"
    # formula = "y ~ a * x**2 + b * x + c"
    # formula = "y ~ a * 1/x + b * x + c"
    f = CurveFit.from_simulated(formula,
                                "x",
                                {"a": 1.1, "b": 1.2, "c": 1.3},
                                start = 0,
                                stop = 10,
                                num_points = 11,
                                noise = 1,
                                y_uncertain=True,
                                mag_uncertain=10,
                                seed=123)
    f.fit()
    print(f._data)
    print(f"{'Formula:':<30} {f._orig_formula}")
    print(f"{'Dependent variable:':<30} {f._dep_var}")
    print(f"{'String formula:':<30} {f._str_func}")
    print(f"{'Symbolic function:':<30} {f._sym_func}")
    # print(f"{'Derivative:':<30} {f.derivative()._sym_func}")
    print(f"{'Independent Variable:':<30} {f._ind_var}")
    print(f"{'Fit parameters:':<30} {f._fit_pars}")
    print(f"{'After substitution:':<30} {f}")
    print(f"{'R-squared:':<30} {f.r_squared}")
    print(f"{'Adjusted R-squared:':<30} {f.adjusted_r_squared}")
    print(f"{'Reduced chi-squared:':<30} {f.chi_squared}")
    interp_str = f"Value @ {f._dep_var} = 4:"
    print(f"{interp_str:<30} {f(4)}")
    print(f._covariance)
    print(f._correlation)

    fig = plt.figure()
    f.plot(save_to = Path("CurveFit_plot.png"), log_y = False, add_to_figure=True)
    f.plot(save_to = Path("CurveFit_plot.png"), log_y = True, add_to_figure=True, add_to_subplot=True)
    # f.plot(save_to = Path("CurveFit_plot.png"), log_y = False, add_to_figure=True)
    # f.plot(save_to = Path("CurveFit_plot.png"), log_y = True, add_to_figure=True)
    # f.plot(save_to = Path("CurveFit_plot.png"), log_y = False, add_to_figure=True)
    # f.plot(save_to = Path("CurveFit_plot.png"), log_y = True, add_to_figure=True)


if __name__ == "__main__":
    main()
