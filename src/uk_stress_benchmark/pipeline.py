"""Modelling-dataset assembly + per-product OLS orchestration.

This is where the pieces come together: ``firm_results`` (one row per firm
x acsyear) is inner-joined to the per-acsyear low-point shocks, firm-name
dummies are added, and a universal exclude list (Standard Chartered and
The Co-operative Bank by default) is applied. The result is the regression
dataset the legacy R called ``st_modelling_df``.

On top of that, the four product recipes (mortgage / retail / CRE /
business) are encoded as :class:`ProductRecipe` constants in
:data:`RECIPES`, and :func:`fit_product_models` fits them all in one go.
Each recipe carries its own per-product additional excludes (CRE drops
Nationwide, mirroring the legacy v4.R).

Public surface:
    build_modelling_dataset(results, shocks, *, exclude_firms)
        -> pd.DataFrame
    ProductRecipe                         (frozen dataclass)
    RECIPES: dict[str, ProductRecipe]     ({"mortgage", "retail", "cre", "business"})
    fit_product_models(df, recipes=RECIPES) -> dict[str, RegressionResults]
    predict_for_scenario(models, shock_values, firms_df) -> pd.DataFrame
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from statsmodels.regression.linear_model import RegressionResults

from uk_stress_benchmark.models import add_dummies, fit_linear_model, predict_with_model

# Universal default exclude. Standard Chartered is on the BoE list of UK
# stress-test participants but its UK retail / mortgage book is too small to
# model meaningfully (mirrors the legacy v4.R `filter(!firm_name == "SCB")`).
# The Co-operative Bank appears only in 2014 and was historically dropped as a
# side effect of the (now-removed) provisions inner-join; it is excluded
# explicitly so the modelling firm set is unchanged.
_DEFAULT_EXCLUDE: tuple[str, ...] = ("Standard Chartered", "The Co-operative Bank")


def build_modelling_dataset(
    results: pd.DataFrame,
    shocks: pd.DataFrame,
    *,
    exclude_firms: tuple[str, ...] = _DEFAULT_EXCLUDE,
) -> pd.DataFrame:
    """Assemble the per-firm-per-acsyear regression dataset.

    Parameters
    ----------
    results : pd.DataFrame
        Output of :func:`uk_stress_benchmark.results.load_results`. One row
        per (firm, acsyear), with the per-product impairment-charge target
        columns (``uk_mort_5yr_ic_pct`` etc.).
    shocks : pd.DataFrame
        Output of :func:`uk_stress_benchmark.scenarios.build_low_point_shocks`.
        Indexed by ``acsyear`` (or carrying it as a column) with the
        per-variable ``_pct_fall`` / ``_pct_rise`` features.
    exclude_firms : tuple[str, ...]
        Firms to drop from the dataset before modelling. Match is
        case-insensitive on ``firm_name``. Default is Standard Chartered
        (the universal legacy exclude) plus The Co-operative Bank.

    Returns
    -------
    pd.DataFrame
        Inner-joined, dummy-expanded, exclude-filtered frame ready for
        :func:`fit_product_models` or any caller that wants to fit a
        single LM via :func:`uk_stress_benchmark.models.fit_linear_model`.
    """
    # Tolerate shocks being indexed by acsyear or carrying it as a column.
    if "acsyear" not in shocks.columns:
        shocks = shocks.reset_index()

    df = results.merge(shocks, on="acsyear", how="inner")

    excludes_lower = {f.lower() for f in exclude_firms}
    df = df.loc[~df["firm_name"].str.lower().isin(excludes_lower)].reset_index(drop=True)

    df = add_dummies(df, "firm_name")
    return df


@dataclass(frozen=True)
class ProductRecipe:
    """One product model's recipe — target, predictors, and any per-product excludes.

    Attributes
    ----------
    dependent_var : str
        Name of the impairment-charge column to model.
    independent_vars : tuple[str, ...]
        Predictor column names (a mix of low-point-shock features and
        firm-name dummies).
    exclude_firms : tuple[str, ...]
        Additional firms to drop *before fitting this specific product*,
        on top of the dataset-wide exclude. Case-insensitive match on
        ``firm_name``. CRE drops Nationwide (mortgage-heavy book skews CRE
        regression).
    stepwise : bool
        Run backward-AIC elimination after the initial fit.
    """

    dependent_var: str
    independent_vars: tuple[str, ...]
    exclude_firms: tuple[str, ...] = field(default_factory=tuple)
    stepwise: bool = True


# Recipes ported from the legacy ``stress testing v4.R`` workflow
# (lines 63-148). Predictor lists preserve the original ordering for
# readability vs the R source. ``firm_name_san_uk`` in the R source
# becomes ``firm_name_santander_uk`` here because we keep full firm
# names in the ingest layer.
RECIPES: dict[str, ProductRecipe] = {
    "mortgage": ProductRecipe(
        dependent_var="uk_mort_5yr_ic_pct",
        independent_vars=(
            "uk_residential_property_price_index_pct_fall",
            "uk_unemployment_rate_pct_rise",
            "uk_unemployment_rate_pct_fall",
            "firm_name_santander_uk",
            "uk_bank_rate_pct_rise",
            "uk_bank_rate_pct_fall",
        ),
    ),
    "retail": ProductRecipe(
        dependent_var="uk_retail_5yr_ic_pct",
        independent_vars=(
            "uk_unemployment_rate_pct_rise",
            "uk_bank_rate_pct_rise",
            "uk_bank_rate_pct_fall",
        ),
    ),
    "cre": ProductRecipe(
        dependent_var="uk_cre_5yr_ic_pct",
        independent_vars=(
            "uk_commercial_real_estate_price_index_aggregate_pct_fall",
            "uk_corporate_profits_pct_fall",
            "uk_unemployment_rate_pct_rise",
            "uk_unemployment_rate_pct_fall",
            "firm_name_santander_uk",
            "uk_bank_rate_pct_rise",
            "uk_bank_rate_pct_fall",
        ),
        exclude_firms=("Nationwide",),
    ),
    "business": ProductRecipe(
        dependent_var="uk_bus_5yr_ic_pct",
        independent_vars=(
            "uk_nominal_gdp_index_pct_fall",
            "uk_corporate_profits_pct_fall",
            "uk_unemployment_rate_pct_rise",
            "uk_unemployment_rate_pct_fall",
            "firm_name_santander_uk",
            "uk_bank_rate_pct_rise",
            "uk_bank_rate_pct_fall",
        ),
    ),
}


def fit_product_models(
    df: pd.DataFrame,
    recipes: dict[str, ProductRecipe] = RECIPES,
) -> dict[str, RegressionResults]:
    """Fit every recipe in ``recipes`` against ``df`` and return the lot.

    Each recipe's per-product ``exclude_firms`` is applied on top of any
    dataset-wide filtering already done by :func:`build_modelling_dataset`.

    Parameters
    ----------
    df : pd.DataFrame
        Output of :func:`build_modelling_dataset`.
    recipes : dict[str, ProductRecipe]
        Recipes to fit. Defaults to the four legacy R products.

    Returns
    -------
    dict[str, RegressionResults]
        ``{recipe_name: fitted_model}``. Inspect with ``model.summary()``
        or ``model.params`` per the statsmodels API.
    """
    fitted: dict[str, RegressionResults] = {}
    for name, recipe in recipes.items():
        sub = df
        if recipe.exclude_firms:
            excl = {f.lower() for f in recipe.exclude_firms}
            sub = sub.loc[~sub["firm_name"].str.lower().isin(excl)]
        fitted[name] = fit_linear_model(
            sub,
            dependent_var=recipe.dependent_var,
            independent_vars=list(recipe.independent_vars),
            stepwise=recipe.stepwise,
        )
    return fitted


def predict_for_scenario(
    models: dict[str, RegressionResults],
    shock_values: dict[str, float],
    firms_df: pd.DataFrame,
) -> pd.DataFrame:
    """Predict per-firm impairment charges under a single hypothetical scenario.

    Broadcasts the supplied ``shock_values`` across every firm in
    ``firms_df`` and runs each fitted product model. The output is a tidy
    table indexed by ``firm_name`` with one column per product.

    Parameters
    ----------
    models : dict[str, RegressionResults]
        Output of :func:`fit_product_models` — one fitted OLS per product.
    shock_values : dict[str, float]
        ``{shock_column_name: value}`` for the low-point shock features
        (e.g. ``"uk_residential_property_price_index_pct_fall": -0.30``).
        Keys not referenced by any model are harmless. Keys referenced by
        a model but missing here will produce NaN predictions for that
        product.
    firms_df : pd.DataFrame
        One row per firm carrying everything firm-level the models need:
        the original ``firm_name`` column and the ``firm_name_*`` dummy
        columns produced by
        :func:`uk_stress_benchmark.models.add_dummies`. Typically built by
        ``modelling_df.drop_duplicates("firm_name")``.

    Returns
    -------
    pd.DataFrame
        Indexed by ``firm_name``, with one column per product key in
        ``models``. Values are predicted impairment-charge percentages
        for the supplied scenario.
    """
    scoring = firms_df.copy()
    for col, val in shock_values.items():
        scoring[col] = val

    out = pd.DataFrame({"firm_name": scoring["firm_name"].values})
    for product_name, model in models.items():
        scored = predict_with_model(scoring, model)
        out[product_name] = scored["prediction"].values
    return out.set_index("firm_name")
