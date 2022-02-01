# CurveFit
This repository describes a generic curve-fitting utility meant for use in data science workloads.

Oftentimes, researchers are interested in describing the mathematical relationship between a set of predictor variables and a dependent observable.  This library simplifies that task for one-dimensional, potentially non-linear relationships, such as those commonly encountered in real-world time series data.  As long as the relationship can be described as an r-style `response ~ terms` expression, this library can obtain fits, intersections between fits, summary statistics, goodness-of-fit statistics, and fit residuals.  It can also perform simple interpolation amd hypothesis tests of fit parameters (based on a Student's T distribution), as well as dynamically generate plots with high customizability.

If the underlying data has uncertainties in either the dependent or independent variables, they are taken into account, and in the case of an uncertain independent variable, Orthogonal Distance Regression (ODR) is used in place of the standard nonlinear least squares.

The library itself is built on the functions contained in the scipy.optimize and scipy.odr packages, and fits are expressed as symbolic sympy expressions of arbitrary complexity.
