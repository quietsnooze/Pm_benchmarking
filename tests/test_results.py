"""Tests for load_results — verifies behaviour through the public surface
by writing synthetic firm_results.csv files in tmp_path."""

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.results import load_results


def _write_csv(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_imputes_5yr_from_3yr_for_mort_retail_cre_when_5yr_is_missing(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_results.csv",
        [
            {
                "firm_name": "Barclays",
                "acsyear": 2014,
                "uk_mort_3yr_ic_pct": 0.009,
                "uk_retail_3yr_ic_pct": 0.223,
                "uk_cre_3yr_ic_pct": 0.05,
                "uk_mort_5yr_ic_pct": "",
                "uk_retail_5yr_ic_pct": "",
                "uk_cre_5yr_ic_pct": "",
                "uk_bus_5yr_ic_pct": "",
            }
        ],
    )

    df = load_results(csv, impute_missing=True)
    barclays_2014 = df.iloc[0]

    assert barclays_2014["uk_mort_5yr_ic_pct"] == pytest.approx(0.009)
    assert barclays_2014["uk_retail_5yr_ic_pct"] == pytest.approx(0.223)
    assert barclays_2014["uk_cre_5yr_ic_pct"] == pytest.approx(0.05)
    # Business has no 3yr column to impute from — must remain NaN.
    assert pd.isna(barclays_2014["uk_bus_5yr_ic_pct"])


def test_does_not_overwrite_5yr_when_5yr_already_populated(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_results.csv",
        [
            {
                "firm_name": "Barclays",
                "acsyear": 2015,
                "uk_mort_3yr_ic_pct": 0.003,
                "uk_retail_3yr_ic_pct": 0.169,
                "uk_cre_3yr_ic_pct": 0.027,
                "uk_mort_5yr_ic_pct": 0.002,
                "uk_retail_5yr_ic_pct": 0.246,
                "uk_cre_5yr_ic_pct": 0.035,
                "uk_bus_5yr_ic_pct": 0.066,
            }
        ],
    )

    df = load_results(csv, impute_missing=True)
    row = df.iloc[0]

    # 5yr values must still be the original 5yr values, not overwritten by 3yr.
    assert row["uk_mort_5yr_ic_pct"] == pytest.approx(0.002)
    assert row["uk_retail_5yr_ic_pct"] == pytest.approx(0.246)
    assert row["uk_cre_5yr_ic_pct"] == pytest.approx(0.035)


def test_impute_missing_false_preserves_nan_in_5yr_columns(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_results.csv",
        [
            {
                "firm_name": "Barclays",
                "acsyear": 2014,
                "uk_mort_3yr_ic_pct": 0.009,
                "uk_retail_3yr_ic_pct": 0.223,
                "uk_cre_3yr_ic_pct": 0.05,
                "uk_mort_5yr_ic_pct": "",
                "uk_retail_5yr_ic_pct": "",
                "uk_cre_5yr_ic_pct": "",
                "uk_bus_5yr_ic_pct": "",
            }
        ],
    )

    df = load_results(csv, impute_missing=False)
    row = df.iloc[0]

    assert pd.isna(row["uk_mort_5yr_ic_pct"])
    assert pd.isna(row["uk_retail_5yr_ic_pct"])
    assert pd.isna(row["uk_cre_5yr_ic_pct"])


def test_acsyear_returned_as_integer_dtype(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_results.csv",
        [
            {
                "firm_name": "Barclays",
                "acsyear": 2017,
                "uk_mort_3yr_ic_pct": "",
                "uk_retail_3yr_ic_pct": "",
                "uk_cre_3yr_ic_pct": "",
                "uk_mort_5yr_ic_pct": 0.009,
                "uk_retail_5yr_ic_pct": 0.368,
                "uk_cre_5yr_ic_pct": 0.054,
                "uk_bus_5yr_ic_pct": 0.081,
            }
        ],
    )

    df = load_results(csv)

    assert pd.api.types.is_integer_dtype(df["acsyear"]), df["acsyear"].dtype
