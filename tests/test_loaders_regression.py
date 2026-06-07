"""Regression tests: exercise the loaders against the real processed_inputs/
CSVs committed in the repo. These guard against drift between what the
loaders expect and what the ingest pipeline actually produces — a class of
bug the synthetic tmp_path tests can't catch.

Kept separate from the unit tests so a regression failure points clearly at
"the data and the loader disagree" rather than "the loader logic is wrong"."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.provisions import load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenario_index import modelling_paths

PROCESSED = Path(__file__).resolve().parent.parent / "processed_inputs"


def test_manifest_resolves_the_newer_scenarios_to_existing_csvs():
    paths = modelling_paths(PROCESSED)
    for year, name in [
        (2021, "scenario-2021-stress.csv"),
        (2022, "scenario-2022-stress.csv"),
        (2025, "scenario-2025-stress.csv"),
    ]:
        assert year in paths, f"{year} should be a modelled scenario in the manifest"
        assert paths[year].name == name
        assert paths[year].exists()


def test_2021_is_scenario_coverage_only_not_a_training_year():
    # The 2021 Solvency Stress Test scenario is registered (available for
    # what-if / app coverage), but its results are deliberately not pooled into
    # the regression, so it must appear in the manifest yet not in firm_results.
    assert 2021 in modelling_paths(PROCESSED)
    results = load_results(PROCESSED / "firm_results.csv")
    assert 2021 not in set(results["acsyear"])


@pytest.fixture(scope="module")
def real_results() -> pd.DataFrame:
    return load_results(PROCESSED / "firm_results.csv")


@pytest.fixture(scope="module")
def real_provisions() -> pd.DataFrame:
    return load_provisions(PROCESSED / "firm_provisions.csv")


def test_real_firm_results_covers_the_legacy_and_newer_years(real_results: pd.DataFrame):
    years = set(real_results["acsyear"].unique())
    # The original 2014-2019 ACS series must always be present...
    assert {2014, 2015, 2016, 2017, 2018, 2019}.issubset(years)
    # ...along with the newer years pooled as training (2022/23 ACS, 2025 BCST).
    assert {2022, 2025}.issubset(years)
    # 2021 SST is intentionally NOT a training year (scenario-only); see
    # test_2021_is_scenario_coverage_only_not_a_training_year.
    assert 2021 not in years


def test_real_firm_results_imputes_2014_5yr_from_3yr(real_results: pd.DataFrame):
    # 2014 BoE published only 3yr rates; imputation must populate the 5yr cols
    # for the three imputable products (mortgage / retail / CRE).
    yr2014 = real_results.loc[real_results["acsyear"] == 2014]
    assert not yr2014.empty
    assert bool(yr2014["uk_mort_5yr_ic_pct"].notna().all())
    assert bool(yr2014["uk_retail_5yr_ic_pct"].notna().all())
    assert bool(yr2014["uk_cre_5yr_ic_pct"].notna().all())
    # Business lending has no 3yr analogue — must remain NaN for 2014.
    assert bool(yr2014["uk_bus_5yr_ic_pct"].isna().all())


def test_real_firm_provisions_preserves_standard_chartered_nans(
    real_provisions: pd.DataFrame,
):
    # Standard Chartered publishes no UK retail/mortgage book — NaN coverage
    # is the correct value, not a parsing artifact.
    sc = real_provisions.set_index("firm_name").loc["Standard Chartered"]
    assert pd.isna(sc["mort_prov_coverage"])
    assert pd.isna(sc["retail_prov_coverage"])
    assert sc["commercial_prov_coverage"] == pytest.approx(0.013517)


def test_real_provisions_firms_are_a_subset_of_results_firms(
    real_results: pd.DataFrame,
    real_provisions: pd.DataFrame,
):
    # The valid_firms check should pass when given the firm set from results.
    # If this regresses, it points at a firm-naming mismatch between the two
    # ingest paths — exactly what the valid_firms guard exists to catch.
    results_firms = set(real_results["firm_name"].unique())
    # Should not raise:
    load_provisions(PROCESSED / "firm_provisions.csv", valid_firms=results_firms)
