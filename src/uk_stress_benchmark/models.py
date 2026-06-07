"""Per-product linear-regression machinery for stress-test impairment charges.

Ports three legacy R helpers:
    * ``st_create_dummy_var``   -> :func:`add_dummies`
    * ``st_build_linear_model`` -> :func:`fit_linear_model`
    * ``st_predict``            -> :func:`predict_with_model`

Backed by ``statsmodels`` so the OLS summary tables are inspectable in the
same shape Pete is used to from R. Backward-stepwise selection is by AIC,
matching R's default ``step()`` behaviour.

Public surface:
    add_dummies(df, column) -> pd.DataFrame
    fit_linear_model(df, *, dependent_var, independent_vars,
                     include_all_firms=False, stepwise=False) -> RegressionResults
    predict_with_model(df, model, *, actual_col=None) -> pd.DataFrame
"""

from __future__ import annotations

import re
from typing import cast

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResults


def _snake_case(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()


def add_dummies(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Append one-hot dummy columns for ``column``'s categories.

    New columns are named ``{column}_{snake_case_value}`` (e.g.
    ``firm_name_santander_uk``), matching the legacy R output of
    ``varhandle::to.dummy(prefix=column) %>% janitor::clean_names()``.
    The original ``column`` is preserved.

    Parameters
    ----------
    df : pd.DataFrame
        Frame containing ``column``.
    column : str
        Name of the categorical column to expand.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with one extra column per distinct value of ``column``.
    """
    dummies = pd.get_dummies(df[column], prefix=column, prefix_sep="_")
    dummies.columns = [f"{column}_{_snake_case(c[len(column) + 1 :])}" for c in dummies.columns]
    return pd.concat([df, dummies], axis=1)


def fit_linear_model(
    df: pd.DataFrame,
    *,
    dependent_var: str,
    independent_vars: list[str],
    include_all_firms: bool = False,
    stepwise: bool = False,
) -> RegressionResults:
    """Fit an OLS regression of ``dependent_var`` on ``independent_vars``.

    Parameters
    ----------
    df : pd.DataFrame
        Modelling dataset. Must contain ``dependent_var`` and every entry of
        ``independent_vars`` (plus, if ``include_all_firms``, columns
        matching ``firm_name_*``).
    dependent_var : str
        Target column name.
    independent_vars : list[str]
        Predictor column names.
    include_all_firms : bool, default ``False``
        When ``True``, every column whose name starts with ``firm_name_`` is
        appended to the predictor list (the firm fixed-effects intercepts).
    stepwise : bool, default ``False``
        When ``True``, run backward elimination by AIC after the initial
        fit, dropping the predictor whose removal most reduces AIC at each
        step. Stops when no removal improves AIC. Mirrors R's
        ``step(model, direction="backward")``.

    Returns
    -------
    statsmodels.regression.linear_model.RegressionResults
        The fitted model. Use ``.summary()`` for an R-style coefficient
        table, ``.params`` for the coefficient vector, ``.predict(...)``
        for predictions on new data.
    """
    predictors = list(independent_vars)
    if include_all_firms:
        firm_dummies = [c for c in df.columns if c.startswith("firm_name_")]
        for col in firm_dummies:
            if col not in predictors:
                predictors.append(col)

    fit_df = df.loc[:, [dependent_var] + predictors].dropna()
    y = fit_df[dependent_var]
    X = cast(pd.DataFrame, sm.add_constant(fit_df[predictors].astype(float), has_constant="add"))
    model = cast(RegressionResults, sm.OLS(y, X).fit())

    if stepwise:
        model = _backward_eliminate_by_aic(y, X)

    return model


def _backward_eliminate_by_aic(y: pd.Series, X: pd.DataFrame) -> RegressionResults:
    """Drop predictors one at a time to minimise AIC, R's ``step`` default.

    The intercept (``const``) is held fixed and never eliminated.
    """
    best = cast(RegressionResults, sm.OLS(y, X).fit())
    candidates = [c for c in X.columns if c != "const"]

    while candidates:
        # statsmodels stubs type .aic as float | None; a fitted OLS always
        # has a finite AIC, so treat it as float for a well-typed comparison.
        best_aic = cast(float, best.aic)
        drop_col = None
        for col in candidates:
            trial_cols = ["const"] + [c for c in candidates if c != col]
            trial = cast(RegressionResults, sm.OLS(y, X[trial_cols]).fit())
            trial_aic = cast(float, trial.aic)
            if trial_aic < best_aic:
                best_aic = trial_aic
                drop_col = col
                best = trial
        if drop_col is None:
            break
        candidates.remove(drop_col)

    return best


def predict_with_model(
    df: pd.DataFrame,
    model: RegressionResults,
    *,
    actual_col: str | None = None,
) -> pd.DataFrame:
    """Apply a fitted model to ``df`` and return it with a ``prediction`` column.

    Parameters
    ----------
    df : pd.DataFrame
        Frame to score. Must contain every predictor the model needs (a
        subset of the columns used at fit time, since stepwise may have
        dropped some).
    model : RegressionResults
        Fitted output of :func:`fit_linear_model`.
    actual_col : str | None
        If provided, also add an ``actual`` column copying ``df[actual_col]``.
        Convenience for actual-vs-expected plots.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with one extra column ``prediction`` (and optionally
        ``actual``). Rows where any required predictor is NaN come back
        with NaN in ``prediction``.
    """
    out = df.copy()
    needed = [c for c in model.params.index if c != "const"]
    X = sm.add_constant(out[needed].astype(float), has_constant="add")
    out["prediction"] = model.predict(X)
    if actual_col is not None:
        out["actual"] = out[actual_col]
    return out
