"""Per-firm regression diagnostics — one model per firm, per product.

The pooled product models in :mod:`uk_stress_benchmark.pipeline` deliberately
ignore firm identity: a published benchmark must not rate a firm as riskier
than its peers on the strength of its name. This module answers the
complementary *research* question Pete wants to be able to ask — if you set
that principle aside and fit a **separate** regression for each firm, how
accurately can that one firm's own stress-test history be reproduced, and
does a firm-specific model beat the pooled one?

Fitting a model to a single firm is a small-sample problem the pooled fit
never faces. A firm contributes at most one row per stress test (~7-8
points), and within those rows the firm's provision coverage and
buy-to-let share are *constant* — only the macro shocks move year to year.
This module hides three things a caller would otherwise get wrong:

    * dropping the within-firm-constant predictors (coverage, BTL) that
      would be perfectly collinear with the intercept;
    * choosing predictors by **forward** AIC selection capped so the fit
      never spends more degrees of freedom than the handful of rows can
      support (a naive backward pass from a saturated model over-fits);
    * scoring each fit — and, when a pooled baseline is supplied, the
      pooled model's error on the same rows — so "how accurate for this
      firm" is a number, not a vibe.

Public surface:
    fit_per_firm_models(modelling_df, *, recipes=RECIPES, min_obs=5,
                        baseline_models=None) -> PerFirmDiagnostics
    PerFirmDiagnostics                     (frozen dataclass)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResults

from uk_stress_benchmark.models import fit_linear_model, predict_with_model
from uk_stress_benchmark.pipeline import RECIPES, ProductRecipe


@dataclass(frozen=True)
class PerFirmDiagnostics:
    """Per-firm fits and their accuracy.

    Attributes
    ----------
    accuracy : pd.DataFrame
        One tidy row per (firm, product) that met ``min_obs``, with columns
        ``firm_name``, ``product``, ``n_obs``, ``n_predictors``,
        ``predictors`` (the selected predictor names, as a tuple),
        ``r_squared``, ``r_squared_adj`` and ``rmse``. When a pooled
        baseline is supplied, a ``pooled_rmse`` column is added — that
        product's pooled model scored on the same firm rows.
    models : dict[tuple[str, str], RegressionResults]
        ``{(firm_name, product): fitted_model}`` for every accuracy row.
    """

    accuracy: pd.DataFrame
    models: dict[tuple[str, str], RegressionResults]


def fit_per_firm_models(
    modelling_df: pd.DataFrame,
    *,
    recipes: dict[str, ProductRecipe] = RECIPES,
    min_obs: int = 5,
    baseline_models: dict[str, RegressionResults] | None = None,
) -> PerFirmDiagnostics:
    """Fit one regression per firm per product and score each fit.

    Parameters
    ----------
    modelling_df : pd.DataFrame
        Output of :func:`uk_stress_benchmark.pipeline.build_modelling_dataset`.
        Only ``firm_name``, each recipe's dependent column, and its predictor
        columns are read.
    recipes : dict[str, ProductRecipe]
        Product definitions. Each recipe's ``independent_vars`` supplies the
        *candidate* predictors; the fit selects a parsimonious subset. A
        recipe's ``exclude_firms`` is a pooled-fit concern (it stops one
        firm skewing the cross-firm regression) and is **not** applied here —
        a per-firm model uses only that firm's own rows, so there is nothing
        to skew. The ``min_obs`` floor keeps thin firm-product pairs out on
        its own.
    min_obs : int, default 5
        Fewest usable ``(outcome, predictors)`` rows a firm needs for a
        product before it is fitted. Below it the pair is silently skipped —
        it appears in neither ``accuracy`` nor ``models``. Firm time series
        are short, so this guards against fits with too little to say.
    baseline_models : dict[str, RegressionResults] | None
        Optional pooled models (typically
        :func:`uk_stress_benchmark.pipeline.fit_product_models`' output). When
        given, every accuracy row gains a ``pooled_rmse`` column: that
        product's pooled model scored on the same firm rows, so a firm-specific
        fit can be read against the one-size-fits-all baseline.

    Returns
    -------
    PerFirmDiagnostics
        The tidy accuracy table plus the fitted models.
    """
    accuracy_rows: list[dict[str, object]] = []
    models: dict[tuple[str, str], RegressionResults] = {}

    for firm in sorted(modelling_df["firm_name"].unique()):
        firm_rows = modelling_df.loc[modelling_df["firm_name"] == firm]
        for product, recipe in recipes.items():
            fit = _fit_one(firm_rows, recipe, min_obs=min_obs)
            if fit is None:
                continue
            model, target, predictors = fit
            baseline = baseline_models.get(product) if baseline_models is not None else None
            accuracy_rows.append(
                _score(
                    firm_rows,
                    model,
                    target,
                    predictors,
                    firm=firm,
                    product=product,
                    baseline=baseline,
                )
            )
            models[(firm, product)] = model

    return PerFirmDiagnostics(accuracy=_tidy(accuracy_rows), models=models)


# Column ordering for the accuracy frame — stable regardless of insertion
# order, and with the identifying keys first.
_ACCURACY_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "product",
    "n_obs",
    "n_predictors",
    "predictors",
    "r_squared",
    "r_squared_adj",
    "rmse",
    "pooled_rmse",
)


def _tidy(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Assemble the accuracy frame with a stable, key-first column order."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    ordered = [c for c in _ACCURACY_COLUMNS if c in df.columns]
    return df.loc[:, ordered]


def _fit_one(
    firm_rows: pd.DataFrame,
    recipe: ProductRecipe,
    *,
    min_obs: int,
) -> tuple[RegressionResults, str, list[str]] | None:
    """Fit one firm-product model, or ``None`` if the firm is too thin.

    Candidate predictors are the recipe's ``independent_vars`` restricted to
    those that actually vary across this firm's rows — provision coverage and
    BTL share are per-firm constants, so they drop out as collinear with the
    intercept. Forward AIC selection then picks a subset small enough to
    leave residual degrees of freedom.
    """
    target = recipe.dependent_var
    candidates = [c for c in recipe.independent_vars if c in firm_rows.columns]
    usable = firm_rows.loc[:, [target] + candidates].dropna(subset=[target])

    n_obs = len(usable)
    if n_obs < min_obs:
        return None

    varying = [c for c in candidates if usable[c].notna().all() and usable[c].nunique() > 1]
    if not varying:
        return None

    # Keep at least one residual degree of freedom: a firm with n rows can
    # afford at most n - 2 predictors alongside the intercept.
    max_predictors = max(1, n_obs - 2)
    selected = _forward_select(usable, target, varying, max_predictors)
    if not selected:
        return None

    model = fit_linear_model(
        usable,
        dependent_var=target,
        independent_vars=selected,
        stepwise=False,
    )
    return model, target, selected


def _forward_select(
    fit_df: pd.DataFrame,
    target: str,
    candidates: list[str],
    max_predictors: int,
) -> list[str]:
    """Greedily add predictors while AIC improves, up to ``max_predictors``.

    Starting from the intercept-only model keeps every intermediate fit
    non-singular — the safe direction when there are only a handful of rows.
    """
    y = fit_df[target].astype(float)

    def aic(predictors: list[str]) -> float:
        x = sm.add_constant(fit_df[predictors].astype(float), has_constant="add")
        # A predictor that fits the firm exactly drives SSR to zero, so the
        # log-likelihood's log(SSR) is -inf — a valid "cannot be beaten"
        # signal the caller stops on, not a numerical error worth warning on.
        with np.errstate(divide="ignore"):
            return cast(float, sm.OLS(y, x).fit().aic)

    selected: list[str] = []
    remaining = list(candidates)
    best_aic = aic(selected)

    while remaining and len(selected) < max_predictors:
        trial_aic, best_col = min((aic(selected + [c]), c) for c in remaining)
        if trial_aic < best_aic - 1e-9:
            selected.append(best_col)
            remaining.remove(best_col)
            best_aic = trial_aic
        else:
            break

    return selected


def _score(
    firm_rows: pd.DataFrame,
    model: RegressionResults,
    target: str,
    predictors: list[str],
    *,
    firm: str,
    product: str,
    baseline: RegressionResults | None,
) -> dict[str, object]:
    """One accuracy row: identity, fit quality, and the pooled comparison.

    Sole owner of the accuracy-frame's per-row schema — every column the
    frame carries is named exactly here (its ordering lives in
    :data:`_ACCURACY_COLUMNS`). ``baseline`` is the product's pooled model;
    when given, its error on the same firm rows is added as ``pooled_rmse``.
    """
    row: dict[str, object] = {
        "firm_name": firm,
        "product": product,
        "n_obs": int(model.nobs),
        "n_predictors": len(predictors),
        "predictors": tuple(predictors),
        "r_squared": float(model.rsquared),
        "r_squared_adj": float(model.rsquared_adj),
        "rmse": _rmse_on(firm_rows, model, target),
    }
    if baseline is not None:
        row["pooled_rmse"] = _rmse_on(firm_rows, baseline, target)
    return row


def _rmse_on(firm_rows: pd.DataFrame, model: RegressionResults, target: str) -> float:
    """Root-mean-square error of ``model`` on this firm's rows for ``target``.

    Delegates predictor handling to :func:`predict_with_model`, which scores
    unavailable predictors (absent columns or NaN values) to NaN; those rows,
    and any without a published outcome, are dropped before the error is
    taken. Returns NaN if nothing is left to score — e.g. a pooled model that
    needs a column this firm never supplies.
    """
    scored = predict_with_model(firm_rows, model, actual_col=target)
    pairs = scored.dropna(subset=["actual", "prediction"])
    if pairs.empty:
        return math.nan
    resid = pairs["actual"].to_numpy(dtype=float) - pairs["prediction"].to_numpy(dtype=float)
    return float(np.sqrt(np.mean(resid**2)))
