"""LM-based imputation for missing values in a single column.

Mirrors the legacy R ``st_impute_missing_var``: fit an OLS regression of
``missing_var`` on ``based_on_vars`` over the rows where ``missing_var`` is
observed, then use the fitted model to fill the NaN cells. Observed values
are passed through unchanged.

Used in the BoE scenario pipeline to fill 2014's missing
``UK corporate profits`` (which the 2014 BoE workbook simply doesn't
publish) from ``UK nominal GDP``, so all six ACS years can contribute to
the cross-year regressions.

Public surface:
    impute_missing_var(df, *, missing_var, based_on_vars) -> pd.DataFrame
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def impute_missing_var(
    df: pd.DataFrame, *, missing_var: str, based_on_vars: list[str]
) -> pd.DataFrame:
    """Fill NaN cells in ``missing_var`` with predictions from an OLS model.

    Parameters
    ----------
    df : pd.DataFrame
        Frame containing ``missing_var`` and all of ``based_on_vars``.
    missing_var : str
        Name of the column whose NaN cells should be imputed.
    based_on_vars : list[str]
        Predictor column names. Must have no NaN in either the training
        rows (where ``missing_var`` is observed) or the rows being imputed.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``missing_var``'s NaN cells filled. Observed
        values are preserved exactly. All other columns and the frame's
        shape are unchanged.
    """
    out = df.copy()
    target = out[missing_var]
    observed_mask = target.notna()

    if observed_mask.sum() == 0:
        raise ValueError(
            f"impute_missing_var: no observed rows for {missing_var!r}; "
            "cannot fit imputation model."
        )

    X_train = sm.add_constant(out.loc[observed_mask, based_on_vars], has_constant="add")
    y_train = target.loc[observed_mask]
    model = sm.OLS(y_train, X_train).fit()

    X_all = sm.add_constant(out[based_on_vars], has_constant="add")
    predictions = model.predict(X_all)

    filled = np.where(observed_mask, target, predictions)
    out[missing_var] = filled
    return out
