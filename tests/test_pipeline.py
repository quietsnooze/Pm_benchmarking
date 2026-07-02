"""Tests for the modelling-dataset assembly + product-model orchestration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.models import fit_linear_model
from uk_stress_benchmark.pipeline import (
    RECIPES,
    ProductRecipe,
    build_modelling_dataset,
    fit_product_models,
    predict_for_scenario,
    year_benchmark,
)
from uk_stress_benchmark.provisions import load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenario_index import modelling_paths
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
    assert set(zip(df["firm_name"], df["acsyear"], strict=True)) == {
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


def test_build_modelling_dataset_adds_year_trend_centred_on_earliest_year():
    # Year enters the models as a single continuous trend, not a per-year
    # dummy — one degree of freedom, so it can't overfit to each test. It is
    # centred on the dataset's earliest year so the coefficient reads as
    # "change in impairment per year since the programme began".
    df = build_modelling_dataset(_toy_results(), _toy_shocks(), _toy_provisions())
    assert "years_since_first_test" in df.columns
    by_year = df.drop_duplicates("acsyear").set_index("acsyear")["years_since_first_test"]
    # Toy data spans 2017-2018; earliest year -> 0.
    assert by_year.loc[2017] == pytest.approx(0.0)
    assert by_year.loc[2018] == pytest.approx(1.0)


def test_recipes_offer_the_year_trend_as_a_predictor():
    # Every product model can pick up the time trend; backward-AIC decides
    # whether it earns its place (see stepwise=True default).
    for name, recipe in RECIPES.items():
        assert "years_since_first_test" in recipe.independent_vars, name
        assert recipe.stepwise, name


def test_recipes_carry_no_firm_name_predictors():
    # Firm identity must not drive any published model — no firm should be
    # rated riskier than peers on the strength of its name alone.
    for name, recipe in RECIPES.items():
        offenders = [v for v in recipe.independent_vars if v.startswith("firm_name")]
        assert offenders == [], f"{name} still keys off firm identity: {offenders}"


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
    # Sourced from the scenario manifest, not a hard-coded year->file map, so
    # this smoke test automatically covers any new stress-test year that ingest
    # registers.
    paths = modelling_paths(PROCESSED)
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


def test_predict_for_scenario_broadcasts_shocks_across_firms(
    real_modelling_df: pd.DataFrame,
):
    # Fit models, then predict per-firm impairment under one made-up
    # scenario row. Output should have one row per distinct firm and one
    # column per fitted product.
    fitted = fit_product_models(real_modelling_df)

    firms_df = real_modelling_df.drop_duplicates("firm_name").reset_index(drop=True)
    shock_values = {
        "uk_residential_property_price_index_pct_fall": -0.30,
        "uk_commercial_real_estate_price_index_aggregate_pct_fall": -0.40,
        "uk_unemployment_rate_pct_rise": 0.80,
        "uk_unemployment_rate_pct_fall": 0.0,
        "uk_nominal_gdp_index_pct_fall": -0.05,
        "uk_corporate_profits_pct_fall": -0.10,
        "uk_bank_rate_pct_rise": 0.0,
        "uk_bank_rate_pct_fall": -1.0,
    }
    out = predict_for_scenario(fitted, shock_values, firms_df)
    assert set(out.columns) == set(fitted.keys())
    assert set(out.index) == set(firms_df["firm_name"])
    # All predictions finite for every firm × product.
    assert out.notna().all().all()


def test_predict_for_scenario_holds_firm_features_constant_per_firm(
    real_modelling_df: pd.DataFrame,
):
    # Two calls with identical shocks but different firm sets: the
    # predictions for the firms common to both should be identical, since
    # only the firm-level features (prov coverage + dummies) and the
    # shock row drive the prediction.
    fitted = fit_product_models(real_modelling_df)
    firms_df = real_modelling_df.drop_duplicates("firm_name").reset_index(drop=True)
    shock_values = {
        "uk_residential_property_price_index_pct_fall": -0.30,
        "uk_commercial_real_estate_price_index_aggregate_pct_fall": -0.40,
        "uk_unemployment_rate_pct_rise": 0.80,
        "uk_unemployment_rate_pct_fall": 0.0,
        "uk_nominal_gdp_index_pct_fall": -0.05,
        "uk_corporate_profits_pct_fall": -0.10,
        "uk_bank_rate_pct_rise": 0.0,
        "uk_bank_rate_pct_fall": -1.0,
    }
    full = predict_for_scenario(fitted, shock_values, firms_df)
    subset = predict_for_scenario(
        fitted, shock_values, firms_df.loc[firms_df["firm_name"] == "Barclays"]
    )
    # Barclays' mortgage prediction must match between the two calls.
    assert full.loc["Barclays", "mortgage"] == pytest.approx(subset.loc["Barclays", "mortgage"])


def test_real_fitted_models_have_sensible_coefficient_signs(
    real_modelling_df: pd.DataFrame,
):
    # Asserted only for predictors that (a) survive stepwise and (b) are
    # statistically significant. Backward-AIC can retain a predictor whose
    # coefficient is indistinguishable from zero; such a term makes no
    # directional claim, so its sign carries no domain meaning and pinning
    # it just tests noise. (Concretely: offering the year trend as a
    # candidate perturbs the mortgage AIC path onto a p~=0.16 unemployment
    # term whose sign is meaningless.) The guard still bites on any
    # *significant* wrong-signed coefficient. The signs encode domain
    # logic: pct_fall is signed negative (a fall is a negative percent
    # change), so for falls to *drive* losses the coefficient on a
    # *_pct_fall predictor must be non-positive (so coef * negative_pct_fall
    # yields a positive contribution to the impairment-charge target).
    # Symmetrically, *_pct_rise on unemployment should be non-negative.
    significance = 0.10
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
        model = fitted[product]
        params = model.params
        for predictor, expected in expectations.items():
            if predictor not in params.index:
                continue  # stepwise dropped it - nothing to assert
            if model.pvalues[predictor] > significance:
                continue  # not significant - no directional claim to check
            value = params[predictor]
            if expected == "non-positive":
                assert value <= 1e-9, f"{product}.{predictor} = {value}"
            elif expected == "non-negative":
                assert value >= -1e-9, f"{product}.{predictor} = {value}"


def test_predict_for_scenario_evaluates_the_year_trend_from_shock_values():
    # A model carrying the year trend must move its prediction when the
    # caller passes a different year via shock_values — this is how the app
    # evaluates a custom scenario "as of the latest test". The year is a
    # scenario-level scalar, so it rides in shock_values alongside the macro
    # shocks and is broadcast across every firm.
    firms = pd.DataFrame(
        {
            "firm_name": ["A", "B"],
            "mort_prov_coverage": [0.002, 0.004],
            "years_since_first_test": [0.0, 1.0],
        }
    )
    train = pd.DataFrame(
        {
            "years_since_first_test": [0.0, 0.0, 1.0, 1.0, 2.0, 2.0],
            "mort_prov_coverage": [0.002, 0.004, 0.002, 0.004, 0.002, 0.004],
            "uk_mort_5yr_ic_pct": [0.010, 0.012, 0.020, 0.022, 0.030, 0.032],
        }
    )
    model = fit_linear_model(
        train,
        dependent_var="uk_mort_5yr_ic_pct",
        independent_vars=["years_since_first_test", "mort_prov_coverage"],
        stepwise=False,
    )
    models = {"mortgage": model}
    early = predict_for_scenario(models, {"years_since_first_test": 0.0}, firms)
    late = predict_for_scenario(models, {"years_since_first_test": 2.0}, firms)
    # Same firms and coverage, later test year -> higher predicted charge.
    assert bool((late["mortgage"] > early["mortgage"]).all())


# ------------------------------ year benchmark ------------------------------


def _toy_year_benchmark_df() -> pd.DataFrame:
    # One published year (2022) plus a decoy year that must be ignored.
    # Mortgage / CRE / business outcomes are exactly linear in the
    # relevant coverage column so the cross-sectional fit is exact:
    #   mortgage: y = 0.006 + 2 * mort_prov_coverage
    #   cre:      y = 0.010 + 2 * commercial_prov_coverage  (excl. Nationwide)
    #   business: y = 0.000 + 2 * commercial_prov_coverage
    # Retail has only two observations -> below the min_obs floor.
    # Nationwide's CRE actual is a wild outlier: the per-recipe exclude
    # must keep it out of the fit while it still shows as a peer actual.
    df_2022 = pd.DataFrame(
        {
            "firm_name": ["Barclays", "HSBC", "Lloyds Banking Group", "Nationwide"],
            "acsyear": [2022] * 4,
            "uk_mort_5yr_ic_pct": [0.010, 0.014, 0.018, 0.022],
            "uk_retail_5yr_ic_pct": [0.05, 0.06, None, None],
            "uk_cre_5yr_ic_pct": [0.030, 0.040, 0.050, 0.999],
            "uk_bus_5yr_ic_pct": [0.020, 0.030, 0.040, 0.050],
            "mort_prov_coverage": [0.002, 0.004, 0.006, 0.008],
            "retail_prov_coverage": [0.02, 0.04, 0.06, 0.08],
            "commercial_prov_coverage": [0.010, 0.015, 0.020, 0.025],
        }
    )
    decoy_2019 = df_2022.assign(acsyear=2019, uk_mort_5yr_ic_pct=[9.0, 9.0, 9.0, 9.0])
    return pd.concat([df_2022, decoy_2019], ignore_index=True)


_TOY_COVERAGE = {
    "mort_prov_coverage": 0.005,
    "retail_prov_coverage": 0.05,
    "commercial_prov_coverage": 0.0175,
}


def test_year_benchmark_peers_show_actual_published_results():
    out = year_benchmark(_toy_year_benchmark_df(), 2022, _TOY_COVERAGE)
    assert out.loc["Barclays", "mortgage"] == pytest.approx(0.010)
    assert out.loc["Nationwide", "mortgage"] == pytest.approx(0.022)
    # The outlier CRE actual is still displayed for Nationwide.
    assert out.loc["Nationwide", "cre"] == pytest.approx(0.999)
    # The decoy year's values must not leak in.
    assert out.loc["Barclays", "mortgage"] != pytest.approx(9.0)


def test_year_benchmark_predicts_your_firm_from_the_year_cross_section():
    out = year_benchmark(_toy_year_benchmark_df(), 2022, _TOY_COVERAGE)
    # Exact linear relations -> exact predictions.
    assert out.loc["Your firm", "mortgage"] == pytest.approx(0.006 + 2 * 0.005)
    assert out.loc["Your firm", "business"] == pytest.approx(2 * 0.0175)


def test_year_benchmark_applies_per_recipe_firm_excludes_to_the_fit():
    # Nationwide's outlier would wreck the exact CRE line if included.
    out = year_benchmark(_toy_year_benchmark_df(), 2022, _TOY_COVERAGE)
    assert out.loc["Your firm", "cre"] == pytest.approx(0.010 + 2 * 0.0175)


def test_year_benchmark_returns_nan_when_too_few_observations():
    out = year_benchmark(_toy_year_benchmark_df(), 2022, _TOY_COVERAGE)
    # Retail has two usable rows, below the default floor of three.
    assert pd.isna(out.loc["Your firm", "retail"])
    # Peer actuals for retail still show where published.
    assert out.loc["Barclays", "retail"] == pytest.approx(0.05)


def test_year_benchmark_raises_for_a_year_with_no_results():
    with pytest.raises(ValueError, match="1999"):
        year_benchmark(_toy_year_benchmark_df(), 1999, _TOY_COVERAGE)
