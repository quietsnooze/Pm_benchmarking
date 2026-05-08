"""Modelling-dataset assembly + per-product OLS orchestration.

This is where the pieces come together: ``firm_results`` (one row per firm
x acsyear) is inner-joined to the per-acsyear low-point shocks and the
per-firm provision-coverage frame, firm-name dummies are added, and a
universal exclude list (Standard Chartered by default — non-UK retail
book) is applied. The result is the regression dataset the legacy R
called ``st_modelling_df``.

On top of that, the four product recipes (mortgage / retail / CRE /
business) are encoded as :class:`ProductRecipe` constants in
:data:`RECIPES`, and :func:`fit_product_models` fits them all in one go.
Each recipe carries its own per-product additional excludes (CRE drops
Nationwide, mirroring the legacy v4.R).

Public surface:
    build_modelling_dataset(results, shocks, provisions, *, exclude_firms)
        -> pd.DataFrame
    ProductRecipe                         (frozen dataclass)
    RECIPES: dict[str, ProductRecipe]     ({"mortgage", "retail", "cre", "business"})
    fit_product_models(df, recipes=RECIPES) -> dict[str, RegressionResults]
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from statsmodels.regression.linear_model import RegressionResults

from uk_stress_benchmark.models import add_dummies, fit_linear_model

# Universal default exclude — Standard Chartered is on the BoE list of UK
# stress-test participants but its UK retail / mortgage book is too small
# to model meaningfully. Mirrors the legacy v4.R `filter(!firm_name == "SCB")`
# applied before fitting any product model.
_DEFAULT_EXCLUDE: tuple[str, ...] = ("Standard Chartered",)


def build_modelling_dataset(
    results: pd.DataFrame,
    shocks: pd.DataFrame,
    provisions: pd.DataFrame,
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
    provisions : pd.DataFrame
        Output of :func:`uk_stress_benchmark.provisions.load_provisions`.
        One row per firm, with the three ``*_prov_coverage`` columns.
    exclude_firms : tuple[str, ...]
        Firms to drop from the dataset before modelling. Match is
        case-insensitive on ``firm_name``. Default is
        ``("Standard Chartered",)`` — the universal exclude that all
        four legacy R product models applied.

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
    df = df.merge(provisions, on="firm_name", how="inner")

    excludes_lower = {f.lower() for f in exclude_firms}
    df = df[~df["firm_name"].str.lower().isin(excludes_lower)].reset_index(drop=True)

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
        Predictor column names (a mix of low-point-shock features, provision-
        coverage columns, and firm-name dummies).
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
            "mort_prov_coverage",
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
            "retail_prov_coverage",
        ),
    ),
    "cre": ProductRecipe(
        dependent_var="uk_cre_5yr_ic_pct",
        independent_vars=(
            "uk_commercial_real_estate_price_index_aggregate_pct_fall",
            "uk_corporate_profits_pct_fall",
            "commercial_prov_coverage",
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
            "commercial_prov_coverage",
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
            sub = sub[~sub["firm_name"].str.lower().isin(excl)]
        fitted[name] = fit_linear_model(
            sub,
            dependent_var=recipe.dependent_var,
            independent_vars=list(recipe.independent_vars),
            stepwise=recipe.stepwise,
        )
    return fitted
