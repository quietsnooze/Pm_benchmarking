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

PROCESSED = Path(__file__).resolve().parent.parent / "processed_inputs"


@pytest.fixture(scope="module")
def real_results() -> pd.DataFrame:
    return load_results(PROCESSED / "firm_results.csv")


@pytest.fixture(scope="module")
def real_provisions() -> pd.DataFrame:
    return load_provisions(PROCESSED / "firm_provisions.csv")


def test_real_firm_results_loads_and_covers_2014_to_2019(real_results: pd.DataFrame):
    years = sorted(real_results["acsyear"].unique())
    assert years == [2014, 2015, 2016, 2017, 2018, 2019]


def test_real_firm_results_imputes_2014_5yr_from_3yr(real_results: pd.DataFrame):
    # 2014 BoE published only 3yr rates; imputation must populate the 5yr cols
    # for the three imputable products (mortgage / retail / CRE).
    yr2014 = real_results[real_results["acsyear"] == 2014]
    assert not yr2014.empty
    assert yr2014["uk_mort_5yr_ic_pct"].notna().all()
    assert yr2014["uk_retail_5yr_ic_pct"].notna().all()
    assert yr2014["uk_cre_5yr_ic_pct"].notna().all()
    # Business lending has no 3yr analogue — must remain NaN for 2014.
    assert yr2014["uk_bus_5yr_ic_pct"].isna().all()


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
