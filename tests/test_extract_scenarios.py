import pandas as pd

from uk_stress_benchmark.extract_scenarios import clean_scenario_frame


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
