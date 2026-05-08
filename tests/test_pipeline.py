"""Tests for the modelling-dataset assembly + product-model orchestration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.pipeline import (
    RECIPES,
    ProductRecipe,
    build_modelling_dataset,
    fit_product_models,
)
from uk_stress_benchmark.provisions import load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenarios import build_low_point_shocks

PROCESSED = Path(__file__).resolve().parent.parent / "processed_inputs"


def _toy_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "firm_name": [
                "Barclays",
                "Barclays",
                "HSBC",
                "Standard Chartered",
                "Nationwide",
            ],
            "acsyear": [2017, 2018, 2017, 2017, 2018],
            "uk_mort_5yr_ic_pct": [0.01, 0.012, 0.008, 0.005, 0.009],
            "uk_retail_5yr_ic_pct": [0.05, 0.06, 0.04, 0.03, 0.045],
            "uk_cre_5yr_ic_pct": [0.07, 0.08, 0.06, 0.04, 0.07],
            "uk_bus_5yr_ic_pct": [0.06, 0.07, 0.05, 0.03, 0.06],
        }
    )


def _toy_shocks() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "acsyear": [2017, 2018],
            "uk_residential_property_price_index_pct_fall": [-0.33, -0.30],
            "uk_unemployment_rate_pct_rise": [0.98, 1.20],
        }
    ).set_index("acsyear")


def _toy_provisions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "firm_name": ["Barclays", "HSBC", "Standard Chartered", "Nationwide"],
            "mort_prov_coverage": [0.0028, 0.001, None, 0.0011],
            "retail_prov_coverage": [0.081, 0.037, None, 0.0911],
            "commercial_prov_coverage": [0.008, 0.0123, 0.013517, 0.005],
        }
    )


def test_build_modelling_dataset_inner_joins_results_shocks_provisions():
    df = build_modelling_dataset(_toy_results(), _toy_shocks(), _toy_provisions())
    # Standard Chartered excluded by default; remaining firms x acsyears
    # appear once each where data exists in all three sources.
    assert set(zip(df["firm_name"], df["acsyear"])) == {
        ("Barclays", 2017),
        ("Barclays", 2018),
        ("HSBC", 2017),
        ("Nationwide", 2018),
    }


def test_build_modelling_dataset_default_exclude_matches_legacy_r():
    df = build_modelling_dataset(_toy_results(), _toy_shocks(), _toy_provisions())
    assert "Standard Chartered" not in set(df["firm_name"])


def test_build_modelling_dataset_excludes_are_case_insensitive():
    # Caller passes lowercase / different casing — should still match.
    df = build_modelling_dataset(
        _toy_results(),
        _toy_shocks(),
        _toy_provisions(),
        exclude_firms=("standard chartered", "BARCLAYS"),
    )
    firms = set(df["firm_name"])
    assert "Standard Chartered" not in firms
    assert "Barclays" not in firms
    assert "HSBC" in firms


def test_build_modelling_dataset_adds_firm_name_dummies():
    df = build_modelling_dataset(_toy_results(), _toy_shocks(), _toy_provisions())
    # Original firm_name column preserved; one-hot columns added with
    # snake_case suffixes matching add_dummies.
    assert "firm_name" in df.columns
    assert "firm_name_barclays" in df.columns
    assert "firm_name_hsbc" in df.columns
    assert "firm_name_nationwide" in df.columns
    # Standard Chartered was excluded -> no dummy column for it.
    assert "firm_name_standard_chartered" not in df.columns


def test_recipes_cover_all_four_product_models():
    assert set(RECIPES.keys()) == {"mortgage", "retail", "cre", "business"}
    for name, recipe in RECIPES.items():
        assert isinstance(recipe, ProductRecipe), name
        assert recipe.dependent_var.startswith("uk_") and recipe.dependent_var.endswith(
            "_5yr_ic_pct"
        ), name
        assert len(recipe.independent_vars) >= 1, name


def test_cre_recipe_excludes_nationwide_per_legacy_r():
    # The legacy v4.R fits CRE on st_modelling_df %>% filter(!firm_name == "Nationwide").
    cre = RECIPES["cre"]
    assert any("Nationwide".lower() == f.lower() for f in cre.exclude_firms)


# ------------------------------ real-data smoke ------------------------------


@pytest.fixture(scope="module")
def real_modelling_df() -> pd.DataFrame:
    paths = {
        2014: PROCESSED / "scenario-2014-stress.csv",
        2015: PROCESSED / "scenario-2015-stress.csv",
        2016: PROCESSED / "scenario-2016-stress.csv",
        2017: PROCESSED / "scenario-2017-acs.csv",
        2018: PROCESSED / "scenario-2018-acs.csv",
        2019: PROCESSED / "scenario-2019-acs.csv",
    }
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
        paths,
        variables=canonical_vars,
        impute={"UK corporate profits": ["UK nominal GDP"]},
    )
    results = load_results(PROCESSED / "firm_results.csv")
    provisions = load_provisions(PROCESSED / "firm_provisions.csv")
    return build_modelling_dataset(results, shocks, provisions)


def test_real_modelling_dataset_has_expected_firms_and_acsyears(
    real_modelling_df: pd.DataFrame,
):
    firms = set(real_modelling_df["firm_name"])
    # SCB excluded by default. Co-op present in firm_results but not in
    # firm_provisions, so the inner join drops it.
    assert "Standard Chartered" not in firms
    assert "The Co-operative Bank" not in firms
    assert {"Barclays", "HSBC", "Lloyds Banking Group", "Nationwide", "Santander UK"}.issubset(
        firms
    )
    assert set(real_modelling_df["acsyear"]).issuperset({2014, 2015, 2016, 2017, 2018, 2019})


def test_real_data_fits_all_four_product_models(real_modelling_df: pd.DataFrame):
    fitted = fit_product_models(real_modelling_df)
    assert set(fitted.keys()) == {"mortgage", "retail", "cre", "business"}
    for name, model in fitted.items():
        assert "const" in model.params.index, name
        assert model.params.notna().all(), name
        assert len(model.params) >= 2, name  # intercept + at least one predictor


def test_real_fitted_models_have_sensible_coefficient_signs(
    real_modelling_df: pd.DataFrame,
):
    # Asserted only when stepwise hasn't dropped the predictor — robust to
    # AIC-driven shrinkage. The signs encode domain logic: pct_fall is
    # signed negative (a fall is a negative percent change), so for falls
    # to *drive* losses the coefficient on a *_pct_fall predictor must be
    # non-positive (so coef * negative_pct_fall yields a positive
    # contribution to the impairment-charge target). Symmetrically,
    # *_pct_rise on unemployment should be non-negative.
    fitted = fit_product_models(real_modelling_df)
    sensible_signs: dict[str, dict[str, str]] = {
        "mortgage": {
            "uk_residential_property_price_index_pct_fall": "non-positive",
            "uk_unemployment_rate_pct_rise": "non-negative",
        },
        "cre": {
            "uk_commercial_real_estate_price_index_aggregate_pct_fall": "non-positive",
        },
        "business": {
            "uk_nominal_gdp_index_pct_fall": "non-positive",
        },
    }
    for product, expectations in sensible_signs.items():
        params = fitted[product].params
        for predictor, expected in expectations.items():
            if predictor not in params.index:
                continue  # stepwise dropped it - nothing to assert
            value = params[predictor]
            if expected == "non-positive":
                assert value <= 1e-9, f"{product}.{predictor} = {value}"
            elif expected == "non-negative":
                assert value >= -1e-9, f"{product}.{predictor} = {value}"
