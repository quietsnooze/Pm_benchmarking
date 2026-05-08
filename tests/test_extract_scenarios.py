import pandas as pd
import pytest

from uk_stress_benchmark.extract_scenarios import (
    add_uk_nominal_gdp_index,
    clean_scenario_frame,
)


def test_keeps_only_quarter_anchored_rows():
    # Mirrors the actual layout: col A is unnamed, contains quarter labels
    # interspersed with section dividers and trailing footnote text.
    df = pd.DataFrame(
        {
            "Unnamed: 0": [
                "Historical data",
                "Q1 2000",
                "Q2 2000",
                None,
                "Stress projection",
                "Q1 2018",
                "Sources: ...",
            ],
            "UK real GDP": [None, 100, 101, None, None, 105, "explanatory note"],
        }
    )
    cleaned = clean_scenario_frame(df)
    assert list(cleaned["quarter"]) == ["Q1 2000", "Q2 2000", "Q1 2018"]


def test_drops_fully_empty_columns():
    df = pd.DataFrame(
        {
            "Unnamed: 0": ["Q1 2000", "Q2 2000"],
            "UK real GDP": [100, 101],
            "Unnamed: 5": [None, None],  # divider column with no data
        }
    )
    cleaned = clean_scenario_frame(df)
    assert "Unnamed: 5" not in cleaned.columns
    assert "UK real GDP" in cleaned.columns


def test_renames_first_column_to_quarter_even_when_already_named():
    df = pd.DataFrame(
        {
            "Reporting period": ["Q1 2000", "Q2 2000"],
            "UK real GDP": [100, 101],
        }
    )
    cleaned = clean_scenario_frame(df)
    assert cleaned.columns[0] == "quarter"
    assert "Reporting period" not in cleaned.columns


def test_handles_quarter_padding_variants():
    # Some BoE workbooks use a single space between Q-digit and year, others
    # have stretched whitespace; both should be accepted.
    df = pd.DataFrame(
        {
            "Unnamed: 0": ["Q1 2000", "Q2  2001", "Q3\t2002", "noise"],
            "x": [1, 2, 3, 4],
        }
    )
    cleaned = clean_scenario_frame(df)
    assert list(cleaned["quarter"]) == ["Q1 2000", "Q2  2001", "Q3\t2002"]
    assert "noise" not in cleaned["quarter"].values


def test_adds_uk_nominal_gdp_index_rebased_to_year_zero_equals_100():
    # The legacy R built uk_nominal_gdp_index in st_build_scenarios by
    # rebasing UK nominal GDP so the year_zero quarter == 100. Here that
    # derivation lives in extract_scenarios so every scenario CSV carries
    # the column directly.
    df = pd.DataFrame(
        {
            "quarter": ["Q3 2016", "Q4 2016", "Q1 2017", "Q2 2017"],
            "period_kind": ["history", "year_zero", "projection", "projection"],
            "UK nominal GDP": [490_000.0, 500_000.0, 450_000.0, 525_000.0],
        }
    )
    out = add_uk_nominal_gdp_index(df)
    assert "UK nominal GDP index" in out.columns
    assert out.loc[0, "UK nominal GDP index"] == pytest.approx(98.0)
    assert out.loc[1, "UK nominal GDP index"] == pytest.approx(100.0)
    assert out.loc[2, "UK nominal GDP index"] == pytest.approx(90.0)
    assert out.loc[3, "UK nominal GDP index"] == pytest.approx(105.0)


def test_add_uk_nominal_gdp_index_is_noop_when_source_column_missing():
    # 2014's BoE workbook is fine (UK nominal GDP is renamed in via the
    # column-rename map) but defensive: if a future workbook lacks the
    # source column, the helper should leave the frame alone rather than
    # crash.
    df = pd.DataFrame(
        {
            "quarter": ["Q4 2016", "Q1 2017"],
            "period_kind": ["year_zero", "projection"],
            "Some other variable": [1.0, 2.0],
        }
    )
    out = add_uk_nominal_gdp_index(df)
    assert "UK nominal GDP index" not in out.columns
    assert list(out.columns) == ["quarter", "period_kind", "Some other variable"]


def test_recognises_2014_stress_scenario_divider():
    # The 2014 BoE workbook uses "Stress scenario" (with trailing space)
    # instead of "Projections". Same semantics — the cleaned frame should
    # mark history / year_zero / projection accordingly.
    df = pd.DataFrame(
        {
            "Unnamed: 0": [
                "Historical data",
                "Q3 2013",
                "Q4 2013",
                "Stress scenario ",
                "Q1 2014",
            ],
            "UK real GDP": [None, 99, 100, None, 95],
        }
    )
    cleaned = clean_scenario_frame(df)
    assert list(cleaned["period_kind"]) == ["history", "year_zero", "projection"]


def test_assigns_period_kind_around_projections_divider():
    # Real BoE sheets are: "Historical data", quarter rows, "Projections" divider,
    # more quarter rows. The cleaned frame should label history vs projection,
    # and tag the last history row as year_zero (the T0 used as denominator
    # for low-point shock calculations).
    df = pd.DataFrame(
        {
            "Unnamed: 0": [
                "Historical data",
                "Q1 2017",
                "Q2 2017",
                "Projections",
                "Q3 2017",
                "Q4 2017",
            ],
            "UK real GDP": [None, 100, 101, None, 102, 103],
        }
    )
    cleaned = clean_scenario_frame(df)
    assert list(cleaned["quarter"]) == ["Q1 2017", "Q2 2017", "Q3 2017", "Q4 2017"]
    assert list(cleaned["period_kind"]) == [
        "history",
        "year_zero",
        "projection",
        "projection",
    ]
