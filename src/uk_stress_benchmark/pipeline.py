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
    predict_for_scenario(models, shock_values, firms_df) -> pd.DataFrame
    year_benchmark(modelling_df, year, coverage) -> pd.DataFrame
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd
from statsmodels.regression.linear_model import RegressionResults

from uk_stress_benchmark.models import add_dummies, fit_linear_model, predict_with_model

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
    btl: pd.DataFrame | None = None,
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
    btl : pd.DataFrame | None, default ``None``
        Output of :func:`uk_stress_benchmark.provisions.load_btl` — one row
        per firm with a ``btl_share`` column (buy-to-let proportion of the
        mortgage book). A static per-firm attribute broadcast across every
        year (the same figure applies to all of a firm's rows). Merged with
        a left join so a firm missing a BTL figure keeps its rows with a
        NaN ``btl_share`` (only the mortgage fit, which uses the column,
        drops that firm-year). When ``None`` the column is still created,
        filled with NaN, so the mortgage recipe never hits a missing column.
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
    df = df.loc[~df["firm_name"].str.lower().isin(excludes_lower)].reset_index(drop=True)

    # BTL share is a static per-firm attribute; broadcast it across the
    # firm's rows via a left join so a missing figure never drops a firm
    # from products that don't use it. Always materialise the column so the
    # mortgage recipe can reference it unconditionally.
    if btl is not None:
        df = df.merge(btl.loc[:, ["firm_name", "btl_share"]], on="firm_name", how="left")
    else:
        df["btl_share"] = float("nan")

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
# readability vs the R source. Two deliberate departures from the R:
#   * The firm-name fixed effect (``firm_name_san_uk`` in the R source)
#     has been dropped from every model. A published benchmark cannot rate
#     a firm as riskier than its peers on the strength of its name alone;
#     the general firm-dummy machinery in :func:`add_dummies` is retained
#     for research but no default recipe keys off firm identity.
#   * The mortgage model gains ``btl_share`` — the buy-to-let proportion
#     of a firm's mortgage book — a structural risk driver the macro
#     shocks and provision coverage don't capture. It is a static per-firm
#     attribute (see :func:`uk_stress_benchmark.provisions.load_btl`) and a
#     stepwise candidate like every other predictor.
RECIPES: dict[str, ProductRecipe] = {
    "mortgage": ProductRecipe(
        dependent_var="uk_mort_5yr_ic_pct",
        independent_vars=(
            "uk_residential_property_price_index_pct_fall",
            "uk_unemployment_rate_pct_rise",
            "uk_unemployment_rate_pct_fall",
            "mort_prov_coverage",
            "btl_share",
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
        the original ``firm_name`` column, the three ``*_prov_coverage``
        columns, and the ``firm_name_*`` dummy columns produced by
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


def year_benchmark(
    modelling_df: pd.DataFrame,
    year: int,
    coverage: dict[str, float],
    *,
    recipes: dict[str, ProductRecipe] = RECIPES,
    your_firm: str = "Your firm",
    min_obs: int = 3,
) -> pd.DataFrame:
    """Benchmark against one published stress test's actual results.

    Within a single stress test every firm faces the same macro scenario,
    so the scenario shocks carry no cross-firm information — the only
    within-year variation the data offers is firm-level provision
    coverage. This benchmark therefore shows peers' *actual published*
    impairment outcomes untouched, and places ``your_firm`` on that
    cross-section by regressing each product's outcome on its coverage
    column (no stepwise, no firm effects) across the year's participants.

    Parameters
    ----------
    modelling_df : pd.DataFrame
        Output of :func:`build_modelling_dataset` (only ``firm_name``,
        ``acsyear``, the target columns and the ``*_prov_coverage``
        columns are used).
    year : int
        The published stress test to benchmark against. Must exist in
        ``modelling_df['acsyear']``.
    coverage : dict[str, float]
        ``{coverage_column: value}`` for your firm, e.g.
        ``{"mort_prov_coverage": 0.002, ...}``. Products whose coverage
        column is missing from this dict get a NaN prediction.
    recipes : dict[str, ProductRecipe]
        Product definitions; each recipe's coverage predictor is the
        ``*_prov_coverage`` entry of its ``independent_vars``, and its
        ``exclude_firms`` are dropped from the fit (never from the
        peer rows shown).
    your_firm : str
        Index label for the synthetic row appended to the output.
    min_obs : int
        Fewest usable (outcome, coverage) pairs required to fit a
        product's cross-section; below it the prediction is NaN.

    Returns
    -------
    pd.DataFrame
        Indexed by ``firm_name`` (the year's participants plus
        ``your_firm``), one column per recipe key. Peer cells are actual
        published outcomes; the ``your_firm`` row is modelled. Cells are
        NaN where a firm didn't publish that product or the fit was
        infeasible.

    Raises
    ------
    ValueError
        If ``modelling_df`` has no rows for ``year``.
    """
    rows = modelling_df.loc[modelling_df["acsyear"] == year]
    if rows.empty:
        raise ValueError(f"no stress-test results for year {year}")

    peers = rows.drop_duplicates("firm_name").set_index("firm_name")
    out = pd.DataFrame(index=peers.index.append(pd.Index([your_firm], name="firm_name")))

    for name, recipe in recipes.items():
        target = recipe.dependent_var
        out.loc[peers.index, name] = peers[target]

        cov_col = next(v for v in recipe.independent_vars if v.endswith("_prov_coverage"))
        fit_rows = rows
        if recipe.exclude_firms:
            excl = {f.lower() for f in recipe.exclude_firms}
            fit_rows = fit_rows.loc[~fit_rows["firm_name"].str.lower().isin(excl)]
        fit_rows = fit_rows.dropna(subset=[target, cov_col])

        prediction = math.nan
        if len(fit_rows) >= min_obs and cov_col in coverage:
            model = fit_linear_model(
                fit_rows,
                dependent_var=target,
                independent_vars=[cov_col],
                stepwise=False,
            )
            scored = predict_with_model(pd.DataFrame({cov_col: [coverage[cov_col]]}), model)
            prediction = float(scored["prediction"].iloc[0])
        out.loc[your_firm, name] = prediction

    return out
