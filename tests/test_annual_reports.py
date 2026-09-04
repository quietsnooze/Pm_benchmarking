"""Tests for annual_reports — the loader/validator for the hand-transcribed
mortgage & unsecured-retail coverage panel. Verified through the public
surface by writing small CSVs to tmp_path."""

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.annual_reports import (
    REQUIRED_COLUMNS,
    check_sanity,
    load_annual_reports,
)

_HEADER = list(REQUIRED_COLUMNS)


def _row(
    firm_name="Lloyds Banking Group",
    acsyear=2019,
    product="mortgage",
    allowance="1462",
    gross_loans="289237",
    coverage="",
    basis="IFRS9",
    entity="Lloyds Banking Group",
    currency="GBP",
    source_url="http://example/ara.pdf",
    source_table="Table 1.11a",
    source_page="126",
    notes="",
):
    return {
        "firm_name": firm_name,
        "acsyear": acsyear,
        "product": product,
        "allowance": allowance,
        "gross_loans": gross_loans,
        "coverage": coverage,
        "basis": basis,
        "entity": entity,
        "currency": currency,
        "source_url": source_url,
        "source_table": source_table,
        "source_page": source_page,
        "notes": notes,
    }


def _write(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows, columns=_HEADER).to_csv(path, index=False)
    return path


def test_load_recomputes_blank_coverage_from_allowance_and_gross(tmp_path: Path):
    csv = _write(tmp_path / "ar.csv", [_row(allowance="1462", gross_loans="289237", coverage="")])

    df = load_annual_reports(csv)

    assert df.loc[0, "coverage"] == pytest.approx(1462 / 289237)


def test_load_raises_when_typed_coverage_disagrees_with_allowance_over_gross(tmp_path: Path):
    # Guard against a fat-fingered coverage that doesn't match the two
    # primary figures it is supposed to be derived from.
    csv = _write(
        tmp_path / "ar.csv",
        [_row(allowance="1462", gross_loans="289237", coverage="0.05")],
    )

    with pytest.raises(ValueError, match="coverage"):
        load_annual_reports(csv)


def test_load_accepts_typed_coverage_that_matches(tmp_path: Path):
    csv = _write(
        tmp_path / "ar.csv",
        [_row(allowance="1462", gross_loans="289237", coverage="0.005055")],
    )

    df = load_annual_reports(csv)

    assert df.loc[0, "coverage"] == pytest.approx(1462 / 289237, rel=1e-3)


def test_load_raises_on_missing_required_column(tmp_path: Path):
    df = pd.DataFrame([_row()], columns=_HEADER).drop(columns=["basis"])
    csv = tmp_path / "ar.csv"
    df.to_csv(csv, index=False)

    with pytest.raises(ValueError, match="basis"):
        load_annual_reports(csv)


def test_load_raises_on_unknown_product(tmp_path: Path):
    csv = _write(tmp_path / "ar.csv", [_row(product="commercial")])

    with pytest.raises(ValueError, match="product"):
        load_annual_reports(csv)


def test_load_raises_on_unknown_basis(tmp_path: Path):
    csv = _write(tmp_path / "ar.csv", [_row(basis="IFRS-nine")])

    with pytest.raises(ValueError, match="basis"):
        load_annual_reports(csv)


def test_load_tolerates_fully_blank_numeric_row_as_documented_gap(tmp_path: Path):
    # A firm-year with no product split reported: allowance/gross/coverage all
    # blank, a note explaining why. Must load without error and stay NaN.
    csv = _write(
        tmp_path / "ar.csv",
        [
            _row(
                allowance="",
                gross_loans="",
                coverage="",
                notes="Only a blended retail line reported; no mortgage/unsecured split.",
            )
        ],
    )

    df = load_annual_reports(csv)

    assert pd.isna(df.loc[0, "coverage"])
    assert pd.isna(df.loc[0, "allowance"])


def test_load_raises_on_partially_blank_numeric_row(tmp_path: Path):
    # allowance present but gross blank is an incomplete transcription, not a
    # documented gap — refuse it rather than silently emitting NaN coverage.
    csv = _write(tmp_path / "ar.csv", [_row(allowance="1462", gross_loans="", coverage="")])

    with pytest.raises(ValueError, match="gross_loans|incomplete"):
        load_annual_reports(csv)


def test_check_sanity_flags_out_of_range_mortgage_coverage(tmp_path: Path):
    # Mortgage sane band ~0.05-0.6%. 5% is an order of magnitude too high —
    # flagged, but not fatal (a genuine outlier may be real and noted).
    csv = _write(
        tmp_path / "ar.csv",
        [_row(product="mortgage", allowance="5000", gross_loans="100000", coverage="")],
    )
    df = load_annual_reports(csv)

    flags = check_sanity(df)

    assert any("mortgage" in f for f in flags)


def test_check_sanity_flags_out_of_range_unsecured_coverage(tmp_path: Path):
    csv = _write(
        tmp_path / "ar.csv",
        [
            _row(
                product="unsecured_retail",
                allowance="1",
                gross_loans="100000",
                coverage="",
            )
        ],
    )
    df = load_annual_reports(csv)

    flags = check_sanity(df)

    assert any("unsecured_retail" in f for f in flags)


def test_check_sanity_silent_on_in_range_values(tmp_path: Path):
    csv = _write(
        tmp_path / "ar.csv",
        [
            _row(product="mortgage", allowance="1462", gross_loans="289237", coverage=""),
            _row(
                product="unsecured_retail",
                allowance="980",
                gross_loans="27990",
                coverage="",
            ),
        ],
    )
    df = load_annual_reports(csv)

    assert check_sanity(df) == []
