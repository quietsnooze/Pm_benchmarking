"""Tests for the low-point-shock feature engineering module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.scenarios import (
    build_low_point_shocks,
    compute_low_point_shocks,
)

PROCESSED = Path(__file__).resolve().parent.parent / "processed_inputs"


def test_pct_fall_and_pct_rise_relative_to_year_zero():
    # year_zero = 100, projection drops to 90 (-10%) and rises to 110 (+10%).
    # pct_fall is the worst drop, pct_rise is the worst rise — both relative
    # to year_zero.
    df = pd.DataFrame(
        {
            "quarter": ["Q4 2016", "Q1 2017", "Q2 2017", "Q3 2017"],
            "period_kind": ["year_zero", "projection", "projection", "projection"],
            "UK nominal GDP": [100.0, 90.0, 95.0, 110.0],
        }
    )
    shocks = compute_low_point_shocks(df, variables=["UK nominal GDP"])
    assert shocks["uk_nominal_gdp_pct_fall"] == pytest.approx(-0.10)
    assert shocks["uk_nominal_gdp_pct_rise"] == pytest.approx(0.10)


def test_uk_nominal_gdp_index_shocks_use_the_pre_derived_column():
    # The rebased UK nominal GDP index column is added upstream by
    # extract_scenarios.add_uk_nominal_gdp_index, so by the time
    # compute_low_point_shocks sees the frame it's already there with
    # year_zero == 100. This test confirms the shocks function reads that
    # column directly — no in-module rebase.
    df = pd.DataFrame(
        {
            "quarter": ["Q4 2016", "Q1 2017"],
            "period_kind": ["year_zero", "projection"],
            "UK nominal GDP": [500_000.0, 450_000.0],
            "UK nominal GDP index": [100.0, 90.0],
        }
    )
    shocks = compute_low_point_shocks(df, variables=["UK nominal GDP index"])
    assert shocks["uk_nominal_gdp_index_pct_fall"] == pytest.approx(-0.10)
    assert shocks["uk_nominal_gdp_index_pct_rise"] == pytest.approx(0.0)


def test_build_low_point_shocks_returns_dataframe_indexed_by_acsyear():
    # Orchestration: run compute_low_point_shocks across multiple scenario
    # CSVs and assemble the results into a single DataFrame keyed by acsyear.
    paths = {
        2017: PROCESSED / "scenario-2017-acs.csv",
        2018: PROCESSED / "scenario-2018-acs.csv",
    }
    df = build_low_point_shocks(paths, variables=["UK nominal GDP"])
    assert df.index.tolist() == [2017, 2018]
    assert df.index.name == "acsyear"
    assert df.loc[2017, "uk_nominal_gdp_pct_fall"] == pytest.approx(
        -0.043631, abs=1e-5
    )


def test_real_data_low_point_shocks_match_legacy_r_gold():
    # End-to-end regression: build low-point shocks for all six ACS years
    # using the canonical 7-variable feature set, and compare against the
    # legacy R output (eco_scenarios_low_point.csv). This guards against
    # methodology drift from the R port.
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
    mine = build_low_point_shocks(paths, variables=canonical_vars)

    gold_path = (
        Path(__file__).resolve().parent.parent
        / "old_version"
        / "stress test benchmarks"
        / "eco_scenarios_low_point.csv"
    )
    gold = pd.read_csv(gold_path).set_index("acsyear")

    # 2014's BoE workbook doesn't publish UK corporate profits. The Python
    # port honestly returns NaN; the legacy R emitted 0 / 0.1007... from a
    # bind_rows column-union quirk (NA-padded values that summarise_if then
    # filled in unexpectedly). Mask those two cells before comparing.
    expected = gold.copy()
    expected.loc[2014, "uk_corporate_profits_pct_fall"] = float("nan")
    expected.loc[2014, "uk_corporate_profits_pct_rise"] = float("nan")

    pd.testing.assert_frame_equal(
        mine[expected.columns], expected, check_dtype=False, atol=1e-10
    )


def test_uk_bank_rate_alias_maps_to_bank_rate_column():
    # The 2015-2019 BoE workbooks call this column "Bank Rate" (no UK
    # prefix), but the legacy R analysis named the corresponding feature
    # uk_bank_rate. Asking for "UK Bank Rate" should pull values from the
    # "Bank Rate" column and emit the shocks under the uk_bank_rate slug.
    df = pd.DataFrame(
        {
            "quarter": ["Q4 2016", "Q1 2017"],
            "period_kind": ["year_zero", "projection"],
            "Bank Rate": [0.25, 0.10],
        }
    )
    shocks = compute_low_point_shocks(df, variables=["UK Bank Rate"])
    assert "uk_bank_rate_pct_fall" in shocks.index
    assert shocks["uk_bank_rate_pct_fall"] == pytest.approx(-0.6)
    assert shocks["uk_bank_rate_pct_rise"] == pytest.approx(0.0)


def test_pct_rise_is_zero_when_projection_only_falls():
    # year_zero is included in the min/max sweep, so a scenario where every
    # projection quarter falls produces pct_rise=0 (the "rise" coming from
    # year_zero itself, since x/x - 1 = 0).
    df = pd.DataFrame(
        {
            "quarter": ["Q4 2016", "Q1 2017", "Q2 2017"],
            "period_kind": ["year_zero", "projection", "projection"],
            "UK unemployment rate": [5.0, 4.5, 4.0],
        }
    )
    shocks = compute_low_point_shocks(df, variables=["UK unemployment rate"])
    assert shocks["uk_unemployment_rate_pct_fall"] == pytest.approx(-0.20)
    assert shocks["uk_unemployment_rate_pct_rise"] == pytest.approx(0.0)
