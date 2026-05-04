"""Tests for build_firm_results — verifies behaviour through the public surface
by constructing synthetic Annex CSVs in tmp_path and asserting on the
returned frame."""

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.aggregate_firm_results import build_firm_results


def _write_table(directory: Path, year: str, table_id: str, rows: list[dict]) -> Path:
    path = directory / f"{year}_table-{table_id}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_2014_populates_only_3yr_columns_with_5yr_left_nan(tmp_path: Path):
    _write_table(
        tmp_path,
        "2014",
        "1",
        [
            {"firm": "Barclays", "col_1": "0.9%", "col_2": "22.3%", "col_3": "5.0%"},
            {"firm": "HSBC", "col_1": "0.6%", "col_2": "7.0%", "col_3": "6.5%"},
        ],
    )

    result = build_firm_results(tmp_path)

    barclays = result.set_index("firm_name").loc["Barclays"]
    assert barclays["acsyear"] == "2014"
    assert barclays["uk_mort_3yr_ic_pct"] == pytest.approx(0.009)
    assert barclays["uk_retail_3yr_ic_pct"] == pytest.approx(0.223)
    assert barclays["uk_cre_3yr_ic_pct"] == pytest.approx(0.05)
    # 2014 BoE didn't publish 5-year rates — those columns must remain NaN.
    assert pd.isna(barclays["uk_mort_5yr_ic_pct"])
    assert pd.isna(barclays["uk_retail_5yr_ic_pct"])
    assert pd.isna(barclays["uk_cre_5yr_ic_pct"])
    assert pd.isna(barclays["uk_bus_5yr_ic_pct"])


def test_hyphen_and_endash_sentinels_become_nan(tmp_path: Path):
    _write_table(
        tmp_path,
        "2017",
        "A5A",
        [
            {
                "firm": "Standard Chartered",
                "col_1": "-",
                "col_2": "–",
                "col_3": "-",
                "col_4": "7.6",
            },
        ],
    )

    result = build_firm_results(tmp_path)

    sc = result.set_index("firm_name").loc["Standard Chartered"]
    assert pd.isna(sc["uk_mort_5yr_ic_pct"])
    assert pd.isna(sc["uk_retail_5yr_ic_pct"])
    assert pd.isna(sc["uk_cre_5yr_ic_pct"])
    assert sc["uk_bus_5yr_ic_pct"] == pytest.approx(0.076)


def test_royal_bank_of_scotland_normalised_to_group_form(tmp_path: Path):
    # 2017 A5.C (not in our mappings) drops "Group" — but if a row anywhere
    # uses the short form, the canonical output must always be the long form
    # so the rest of the analytics pipeline sees one consistent firm name.
    _write_table(
        tmp_path,
        "2017",
        "A5A",
        [
            {
                "firm": "The Royal Bank of Scotland",
                "col_1": "1.0",
                "col_2": "21.8",
                "col_3": "6.4",
                "col_4": "9.0",
            },
        ],
    )

    result = build_firm_results(tmp_path)

    assert "The Royal Bank of Scotland Group" in result["firm_name"].values
    assert "The Royal Bank of Scotland" not in result["firm_name"].values


def test_2015_2a_and_2c_combine_into_one_firm_row_with_3yr_and_5yr(tmp_path: Path):
    # Table 2A is 5-year rates (cols 1-4 = mort/retail/CRE/business).
    # Table 2C is 3-year rates (cols 1-3 used; col_4 ignored — legacy has no
    # uk_bus_3yr_ic_pct).
    _write_table(
        tmp_path,
        "2015",
        "2A",
        [
            {"firm": "Barclays", "col_1": "0.2", "col_2": "24.6", "col_3": "3.5", "col_4": "6.6"},
        ],
    )
    _write_table(
        tmp_path,
        "2015",
        "2C",
        [
            {"firm": "Barclays", "col_1": "0.3", "col_2": "16.9", "col_3": "2.7", "col_4": "5.0"},
        ],
    )

    result = build_firm_results(tmp_path)

    assert len(result) == 1
    barclays = result.iloc[0]
    # 5-year from 2A
    assert barclays["uk_mort_5yr_ic_pct"] == pytest.approx(0.002)
    assert barclays["uk_bus_5yr_ic_pct"] == pytest.approx(0.066)
    # 3-year from 2C
    assert barclays["uk_mort_3yr_ic_pct"] == pytest.approx(0.003)
    assert barclays["uk_retail_3yr_ic_pct"] == pytest.approx(0.169)
    assert barclays["uk_cre_3yr_ic_pct"] == pytest.approx(0.027)


def test_unmapped_table_is_ignored(tmp_path: Path):
    # 2015 Table 2B is the £-billion equivalent of 2A; not in _TABLE_MAPPINGS.
    _write_table(
        tmp_path,
        "2015",
        "2B",
        [
            {"firm": "Barclays", "col_1": "0.3", "col_2": "7.2", "col_3": "0.3", "col_4": "3.1"},
        ],
    )

    result = build_firm_results(tmp_path)

    assert result.empty
    # The frame should still expose the canonical column shape even when empty.
    assert "uk_mort_5yr_ic_pct" in result.columns
    assert "firm_name" in result.columns
