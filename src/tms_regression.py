from __future__ import annotations
import scipy
import numpy as np

from enum import Enum
from PyQt6.QtWidgets import QLabel
from datetime import datetime


class TmsLogger(object):
    """Object that allows printing to console or to the UI"""

    _instance = None
    output: QLabel = None

    def __new__(cls: type["TmsLogger"]) -> "TmsLogger":
        if cls._instance is None:
            print("Creating TmsLogger Class")
            cls._instance = super(TmsLogger, cls).__new__(cls)
        return cls._instance

    def set_label(self, ui) -> None:
        self.output = ui.findChild(QLabel, "consoleOutput")

    def log(self, text) -> None:
        if self.output is None:
            print(text)
        else:
            self.output.setText(f"{datetime.now()} :: {text}")


class RegressionModels(Enum):
    Cubic = "Cubic"
    Logistic = "Logistic"
    Gombertz = "Gombertz"
    ReverseGombertz = "Reverse Gombertz"
    Boltzmann = "Boltzmann"


class RegressionMode(object):
    """Singleton to change the selected regression mode"""

    _instance = None
    selected_regression_model = RegressionModels.Boltzmann

    def __new__(cls: type["RegressionMode"]) -> "RegressionMode":
        if cls._instance is None:
            print("Creating RegressionMode Class")
            cls._instance = super(RegressionMode, cls).__new__(cls)
        return cls._instance


class RegressionResult(object):
    """Class to cache the result of the curve fitting"""

    stored_values_x: list[int] = []
    stored_values_y: list[float] = []
    stored_mode: RegressionModels = RegressionModels.Cubic

    result_xx: list(float) = []
    result_yy: list(float) = []

    def __init__(self, x_values, y_values, regression_mode, xx, yy) -> None:
        self.stored_values_x = x_values
        self.stored_values_y = y_values
        self.stored_mode = regression_mode

        self.result_xx = xx
        self.result_yy = yy

    def valid(self, x_values, y_values, regression_mode) -> bool:
        if (
            self.stored_mode != regression_mode
            or self.stored_values_y != y_values
            or self.stored_values_x != x_values
        ):
            return False
        return True

    def cached_data(self):
        return self.result_xx, self.result_yy


class RegressionCache(object):
    """Singleton acts as a cache for all the Regression results calculated during one run"""

    _instance = None
    cached_results: list[RegressionResult] = []

    def __new__(cls: type["RegressionCache"]) -> "RegressionCache":
        if cls._instance is None:
            TmsLogger().log("Creating Regressioncache Class")
            cls._instance = super(RegressionCache, cls).__new__(cls)
        return cls._instance

    def get_cache(self, x_values, y_values, regression_mode) -> object:
        for result in self.cached_results:
            if result.valid(x_values, y_values, regression_mode):
                return result
        return None

    def update(self, regression_result: RegressionResult) -> None:
        self.cached_results.append(regression_result)


#### Static Functions for running different regression models
# Linear: Cubic
def linear_cubic_regression(x_values: list[int], y_values: list[float]):
    # Linear regression Model
    def model(x, a, b):
        return a * (x**3) + a * (x**2) + a * x + b

    x = np.array(x_values)
    y = np.array(y_values)

    # Linear Regression
    popt, pcov = scipy.optimize.curve_fit(f=model, xdata=x, ydata=y, p0=(0, 0))

    ## prepare some data for a plot
    xx = np.linspace(min(x_values), max(x_values), 100)
    yy = model(xx, *popt)

    return RegressionResult(
        x_values, y_values, RegressionMode().selected_regression_model, xx, yy
    )


# Non Linear: Logistic
def non_linear_logistic(x_values: list[int], y_values: list[float]):
    # Non linear regression: Logistic Curve
    TmsLogger().log("Running Logistic Regression")

    def model(x, a, b, c, d):
        return a + (c - a) / (1 + np.exp(b * (x - d)))

    def model_jac(x, a, b, c, d):
        return np.array(
            [
                1 - (1 / (np.exp(b * (-d + x)) + 1)),
                ((-a + c) * (-d + x) * np.exp(b * (-d + x)))
                / (np.exp(b * (-d + x)) + 1) ** 2,
                (1) / (np.exp(b * (-d + x)) + 1),
                (b * (-a + c) * np.exp(b * (-d + x))) / (np.exp(b * (-d + x)) + 1) ** 2,
            ]
        ).T

    ## The input data
    x = np.array(x_values)
    y = np.array(y_values)

    p0 = [0, -0.2, max(y) + 5, np.median(x)]

    ## Non Linear Regression
    try:
        popt, pcov = scipy.optimize.curve_fit(
            f=model,
            jac=model_jac,
            xdata=x,
            ydata=y,
            p0=p0,
            maxfev=50000,
        )
    except:
        TmsLogger().log("Cant Fit! Falling Back to...")
        return non_linear_gombertz(x_values=x_values, y_values=y_values)

    ## prepare some data for a plot
    xx = np.linspace(min(x_values), max(x_values), 100)
    yy = model(xx, *popt)

    return RegressionResult(
        x_values, y_values, RegressionMode().selected_regression_model, xx, yy
    )


def non_linear_gombertz(
    x_values: list[int], y_values: list[float], reverse: bool = False
):
    TmsLogger().log("Running Gombertz Regression")

    # Models
    def gombertz(x, a, b, c, d):
        return a + (c - a) * np.exp(-np.exp(b * (x - d)))

    def gombertz_reverse(x, a, b, c, d):
        return a + (c - a) * (1 - np.exp(-np.exp(-b * (x - d))))

    if reverse:
        model = gombertz_reverse
    else:
        model = gombertz

    def model_jac(x, a, b, c, d):
        return np.array(
            [
                1 - np.exp(-np.exp(b * (-d + x))),
                -(-a + c)
                * (-d + x)
                * np.exp(b * (-d + x))
                * np.exp(-np.exp(b * (-d + x))),
                np.exp(-np.exp(b * (-d + x))),
                b * (-a + c) * np.exp(b * (-d + x) * np.exp(-np.exp(b * (-d + x)))),
            ]
        ).T

    ## your input data
    x = np.array(x_values)
    y = np.array(y_values)
    p0 = [min(y), 0.2, max(y) + 5, np.median(x)]

    ## Non Linear Regression
    try:
        popt, pcov = scipy.optimize.curve_fit(
            f=model,
            jac=model_jac,
            xdata=x,
            ydata=y,
            p0=p0,
            maxfev=50000,
            method="dogbox",
        )
    except:
        TmsLogger().log("Cant Fit! Falling Back to...")
        return non_linear_boltzmann(x_values=x_values, y_values=y_values)
    ## prepare some data for a plot
    xx = np.linspace(min(x_values), max(x_values), 100)
    yy = model(xx, *popt)

    return RegressionResult(
        x_values, y_values, RegressionMode().selected_regression_model, xx, yy
    )


# Non Linear: Boltzmann Sigmoid
def non_linear_boltzmann(x_values: list[int], y_values: list[float]):
    TmsLogger().log("Running Boltzman Regression")
    ## your input data
    x = np.array(x_values)
    y = np.array(y_values)

    def model(x, L, x0, k, b):
        y = L / (1 + np.exp(-k * (x - x0))) + b
        return y

    p0 = [max(y), np.median(x), 0.1, min(y)]

    try:
        popt, pcov = scipy.optimize.curve_fit(
            f=model, xdata=x, ydata=y, p0=p0, maxfev=50000, method="dogbox"
        )
    except:
        TmsLogger().log("Cant Fit! Falling Back to...")
        return linear_cubic_regression(x_values=x_values, y_values=y_values)

    ## prepare some data for a plot
    xx = np.linspace(min(x_values), max(x_values), 100)
    yy = model(xx, *popt)

    return RegressionResult(
        x_values, y_values, RegressionMode().selected_regression_model, xx, yy
    )


#### Function to run the selected Regression Model from
def run_regression(
    x_values: list[int], y_values: list[float], regression_overwrite=None
):
    """Function to calculate a function to estimate the point distribution
    x - RMT(%) and y - MEP(mV)"""

    temp_regression_selection = RegressionMode().selected_regression_model

    regression_mode = regression_overwrite
    if regression_mode is None:
        regression_mode = RegressionMode().selected_regression_model
    else:
        RegressionMode().selected_regression_model = regression_mode

    cached_result = RegressionCache().get_cache(x_values, y_values, regression_mode)
    if cached_result is None:
        if regression_mode == RegressionModels.Cubic:
            RegressionCache().update(
                linear_cubic_regression(x_values=x_values, y_values=y_values)
            )
        elif regression_mode == RegressionModels.Logistic:
            RegressionCache().update(
                non_linear_logistic(x_values=x_values, y_values=y_values)
            )
        elif regression_mode == RegressionModels.Gombertz:
            RegressionCache().update(
                non_linear_gombertz(x_values=x_values, y_values=y_values)
            )
        elif regression_mode == RegressionModels.ReverseGombertz:
            RegressionCache().update(
                non_linear_gombertz(x_values=x_values, y_values=y_values, reverse=True)
            )
        elif regression_mode == RegressionModels.Boltzmann:
            RegressionCache().update(
                non_linear_boltzmann(x_values=x_values, y_values=y_values)
            )

        RegressionMode().selected_regression_model = temp_regression_selection
        return (
            RegressionCache()
            .get_cache(x_values, y_values, regression_mode)
            .cached_data()
        )
    else:
        RegressionMode().selected_regression_model = temp_regression_selection
        return cached_result.cached_data()
