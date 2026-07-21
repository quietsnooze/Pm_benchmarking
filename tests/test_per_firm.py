"""Tests for per-firm regression diagnostics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.per_firm import PerFirmDiagnostics, fit_per_firm_models
from uk_stress_benchmark.pipeline import build_modelling_dataset, fit_product_models
from uk_stress_benchmark.provisions import load_btl, load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenario_index import modelling_paths
from uk_stress_benchmark.scenarios import build_low_point_shocks

PROCESSED = Path(__file__).resolve().parent.parent / "processed_inputs"

# Six stress-test years. Macro shocks vary year on year; the two "flat"
# shocks (bank-rate and unemployment-fall) are held constant so they carry
# no within-firm variation and must never be selected.
_YEARS = [2015, 2016, 2017, 2018, 2019, 2022]
_HOUSE_FALL = [-0.30, -0.20, -0.35, -0.25, -0.33, -0.28]
_UNEMP_RISE = [0.90, 0.60, 1.10, 0.80, 1.00, 0.70]
_CRE_FALL = [-0.40, -0.30, -0.45, -0.35, -0.42, -0.38]
_GDP_FALL = [-0.08, -0.05, -0.10, -0.06, -0.09, -0.07]
_CORP_FALL = [-0.20, -0.15, -0.25, -0.18, -0.22, -0.19]


def _toy_modelling_df() -> pd.DataFrame:
    """Two firms with per-firm-exact linear outcomes in a single driver each.

    * mortgage outcome depends only on the house-price fall,
    * retail on the unemployment rise,
    so a firm-specific fit should recover R^2 = 1 on that one predictor and
    never lean on a within-firm-constant column (provision coverage / BTL).
    """
    rows: list[dict[str, object]] = []
    firm_params = {
        "Alpha": {"mort": (0.005, -0.5), "retail": (0.02, 0.03), "cov": 0.003, "btl": 0.10},
        "Beta": {"mort": (0.004, -0.3), "retail": (0.01, 0.05), "cov": 0.002, "btl": 0.05},
    }
    for firm, p in firm_params.items():
        for i, year in enumerate(_YEARS):
            mort_a, mort_b = p["mort"]
            ret_a, ret_b = p["retail"]
            rows.append(
                {
                    "firm_name": firm,
                    "acsyear": year,
                    "uk_residential_property_price_index_pct_fall": _HOUSE_FALL[i],
                    "uk_commercial_real_estate_price_index_aggregate_pct_fall": _CRE_FALL[i],
                    "uk_unemployment_rate_pct_rise": _UNEMP_RISE[i],
                    "uk_unemployment_rate_pct_fall": 0.0,
                    "uk_nominal_gdp_index_pct_fall": _GDP_FALL[i],
                    "uk_corporate_profits_pct_fall": _CORP_FALL[i],
                    "uk_bank_rate_pct_rise": 0.0,
                    "uk_bank_rate_pct_fall": 0.0,
                    "mort_prov_coverage": p["cov"],
                    "retail_prov_coverage": p["cov"],
                    "commercial_prov_coverage": p["cov"],
                    "btl_share": p["btl"],
                    "uk_mort_5yr_ic_pct": mort_a + mort_b * _HOUSE_FALL[i],
                    "uk_retail_5yr_ic_pct": ret_a + ret_b * _UNEMP_RISE[i],
                    "uk_cre_5yr_ic_pct": 0.01 - 0.2 * _CRE_FALL[i],
                    "uk_bus_5yr_ic_pct": 0.0 - 0.4 * _GDP_FALL[i],
                }
            )
    return pd.DataFrame(rows)


def test_returns_one_accuracy_row_per_firm_and_product():
    diag = fit_per_firm_models(_toy_modelling_df(), min_obs=4)
    assert isinstance(diag, PerFirmDiagnostics)
    got = set(zip(diag.accuracy["firm_name"], diag.accuracy["product"], strict=True))
    assert got == {
        ("Alpha", "mortgage"),
        ("Alpha", "retail"),
        ("Alpha", "cre"),
        ("Alpha", "business"),
        ("Beta", "mortgage"),
        ("Beta", "retail"),
        ("Beta", "cre"),
        ("Beta", "business"),
    }


def test_firm_product_below_min_obs_is_dropped():
    # Blank out Alpha's retail outcome in four of its six years, leaving
    # only two usable (target, shocks) rows — below the floor. Alpha's
    # other products, and Beta's retail, are untouched.
    df = _toy_modelling_df()
    mask = (df["firm_name"] == "Alpha") & df["acsyear"].isin([2016, 2017, 2018, 2019])
    df.loc[mask, "uk_retail_5yr_ic_pct"] = None

    diag = fit_per_firm_models(df, min_obs=4)
    keys = set(zip(diag.accuracy["firm_name"], diag.accuracy["product"], strict=True))
    assert ("Alpha", "retail") not in keys
    assert ("Alpha", "mortgage") in keys
    assert ("Beta", "retail") in keys
    # Dropped fits carry no model either.
    assert ("Alpha", "retail") not in diag.models


def test_recovers_the_single_driver_and_ignores_constant_predictors():
    diag = fit_per_firm_models(_toy_modelling_df(), min_obs=4)
    acc = diag.accuracy.set_index(["firm_name", "product"])

    # Mortgage is exact in the house-price fall: near-perfect fit, ~zero error.
    mort = acc.loc[("Alpha", "mortgage")]
    assert mort["r_squared"] == pytest.approx(1.0, abs=1e-6)
    assert mort["rmse"] == pytest.approx(0.0, abs=1e-6)
    assert "uk_residential_property_price_index_pct_fall" in mort["predictors"]

    # Provision coverage and BTL share are constant within a firm, as are the
    # two flat shocks — none may ever be selected, for any firm or product.
    forbidden = {
        "mort_prov_coverage",
        "retail_prov_coverage",
        "commercial_prov_coverage",
        "btl_share",
        "uk_bank_rate_pct_rise",
        "uk_bank_rate_pct_fall",
        "uk_unemployment_rate_pct_fall",
    }
    for predictors in diag.accuracy["predictors"]:
        assert forbidden.isdisjoint(predictors), predictors


def test_pooled_rmse_column_only_appears_with_a_baseline():
    df = _toy_modelling_df()
    without = fit_per_firm_models(df, min_obs=4)
    assert "pooled_rmse" not in without.accuracy.columns

    baseline = fit_product_models(df)
    withb = fit_per_firm_models(df, min_obs=4, baseline_models=baseline)
    assert "pooled_rmse" in withb.accuracy.columns
    # Every pooled score is a finite, non-negative error.
    assert (withb.accuracy["pooled_rmse"] >= 0).all()
    assert withb.accuracy["pooled_rmse"].notna().all()


def test_models_are_keyed_by_firm_and_product_and_carry_an_intercept():
    diag = fit_per_firm_models(_toy_modelling_df(), min_obs=4)
    assert ("Alpha", "mortgage") in diag.models
    model = diag.models[("Alpha", "mortgage")]
    assert "const" in model.params.index
    # Only firm-product pairs in the accuracy table have a model, and vice versa.
    acc_keys = set(zip(diag.accuracy["firm_name"], diag.accuracy["product"], strict=True))
    assert set(diag.models.keys()) == acc_keys


# ------------------------------ real-data smoke ------------------------------


@pytest.fixture(scope="module")
def real_modelling_df() -> pd.DataFrame:
    canonical_vars = [
        "UK residential property price index",
        "UK commercial real estate price index - aggregate",
        "UK unemployment rate",
        "UK nominal GDP index",
        "UK nominal GDP",
        "UK corporate profits",
        "UK Bank Rate",
    ]
    shocks = build_low_point_shocks(
        modelling_paths(PROCESSED),
        variables=canonical_vars,
        impute={"UK corporate profits": ["UK nominal GDP"]},
    )
    results = load_results(PROCESSED / "firm_results.csv")
    provisions = load_provisions(PROCESSED / "firm_provisions.csv")
    btl = load_btl(PROCESSED / "firm_btl.csv")
    return build_modelling_dataset(results, shocks, provisions, btl=btl)


def test_real_data_fits_per_firm_models_within_the_df_budget(real_modelling_df: pd.DataFrame):
    baseline = fit_product_models(real_modelling_df)
    diag = fit_per_firm_models(real_modelling_df, baseline_models=baseline)

    assert not diag.accuracy.empty
    # The core panel firms each get at least one product model.
    for firm in ["Barclays", "HSBC", "Lloyds Banking Group", "Santander UK"]:
        assert firm in set(diag.accuracy["firm_name"])

    acc = diag.accuracy
    # Every fit spends fewer than n_obs - 1 parameters (intercept + predictors),
    # so no model is saturated and adjusted R^2 is always well defined.
    assert (acc["n_predictors"] <= acc["n_obs"] - 2).all()
    assert acc["r_squared_adj"].notna().all()
    assert acc["rmse"].notna().all()
    assert (acc["rmse"] >= 0).all()
    # The pooled baseline is scored on every firm that supplies its columns.
    assert "pooled_rmse" in acc.columns
