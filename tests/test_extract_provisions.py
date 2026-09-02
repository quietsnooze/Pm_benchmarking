"""Tests for extract_provisions — verified through the public surface by writing
synthetic EBA Transparency Exercise credit-risk CSVs to tmp_path."""

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.extract_provisions import build_panel, extract_coverage

_LABEL_EXPOSURE = "Original Exposure - by exposure class (SA_and_IRB)"
_LABEL_PROVISIONS = "Value adjustments and provisions - by exposure class (SA_and_IRB)"

_LLOYDS_LEI = "549300PPXHEU2JF0AM85"

_COLUMNS = [
    "LEI_Code",
    "NSA",
    "Period",
    "Item",
    "Label",
    "Portfolio",
    "Country",
    "Country_rank",
    "Exposure",
    "Status",
    "Perf_Status",
    "NACE_codes",
    "Amount",
]


def _row(
    lei=_LLOYDS_LEI,
    period=201812,
    label=_LABEL_EXPOSURE,
    portfolio=2,
    country=30,
    exposure=406,
    status=0,
    amount=0.0,
    perf_status=0,
    nsa="EBA_GB_LLOYDS",
    item="",
    country_rank=1,
    nace="",
):
    return {
        "LEI_Code": lei,
        "NSA": nsa,
        "Period": period,
        "Item": item,
        "Label": label,
        "Portfolio": portfolio,
        "Country": country,
        "Country_rank": country_rank,
        "Exposure": exposure,
        "Status": status,
        "Perf_Status": perf_status,
        "NACE_codes": nace,
        "Amount": amount,
    }


def _write_csv(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows, columns=_COLUMNS).to_csv(path, index=False)
    return path


def test_extract_coverage_computes_hand_checked_ratios(tmp_path: Path):
    rows = [
        # mortgage: IRB 406 + SA 501
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
        _row(label=_LABEL_EXPOSURE, portfolio=1, exposure=501, amount=5000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        _row(label=_LABEL_PROVISIONS, portfolio=1, exposure=501, amount=10),
        # retail: IRB 409 + IRB 410 + SA 404
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=409, amount=1000),
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=410, amount=2000),
        _row(label=_LABEL_EXPOSURE, portfolio=1, exposure=404, amount=3000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=409, amount=10),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=410, amount=20),
        _row(label=_LABEL_PROVISIONS, portfolio=1, exposure=404, amount=30),
        # commercial: IRB 303 + SA 303
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=303, amount=4000),
        _row(label=_LABEL_EXPOSURE, portfolio=1, exposure=303, amount=6000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=303, amount=40),
        _row(label=_LABEL_PROVISIONS, portfolio=1, exposure=303, amount=60),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["firm_name"] == "Lloyds Banking Group"
    assert row["mort_prov_coverage"] == pytest.approx((50 + 10) / (20000 + 5000))
    assert row["retail_prov_coverage"] == pytest.approx((10 + 20 + 30) / (1000 + 2000 + 3000))
    assert row["commercial_prov_coverage"] == pytest.approx((40 + 60) / (4000 + 6000))


def test_extract_coverage_ignores_irrelevant_rows(tmp_path: Path):
    rows = [
        # In-scope mortgage rows for the requested period.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        # Different period entirely — must not leak in.
        _row(period=201712, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=999999),
        # Country 0 (all-countries total) and country 5 (some other country) —
        # not UK, must be excluded from the default country="GB" query.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, country=0, amount=999999),
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, country=5, amount=999999),
        # "of which" sub-code (408) must not be folded into 406/501.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=408, amount=999999),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=408, amount=999999),
        # Status 2 (a defaulted/non-defaulted breakdown row) must be excluded.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, status=2, amount=999999),
        # Portfolio 0 (total SA+IRB) must be excluded — would double count.
        _row(label=_LABEL_EXPOSURE, portfolio=0, exposure=406, amount=999999),
        # Unknown LEI must be ignored entirely.
        _row(
            lei="UNKNOWNLEI0000000000",
            label=_LABEL_EXPOSURE,
            portfolio=2,
            exposure=406,
            amount=999999,
        ),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["firm_name"] == "Lloyds Banking Group"
    assert row["mort_prov_coverage"] == pytest.approx(50 / 20000)


def test_extract_coverage_country_00_selects_all_countries_total(tmp_path: Path):
    rows = [
        # UK-only rows (country 30) — must be excluded when querying "00".
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, country=30, amount=20000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, country=30, amount=50),
        # All-countries total rows (country 0) — the ones country="00" wants.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, country=0, amount=80000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, country=0, amount=400),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812, country="00")

    assert len(result) == 1
    row = result.iloc[0]
    assert row["mort_prov_coverage"] == pytest.approx(400 / 80000)


def test_extract_coverage_missing_denominator_is_nan_for_that_product_only(tmp_path: Path):
    rows = [
        # Mortgage: only provisions, no exposure row at all -> NaN.
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        # Commercial: exposure present and non-zero -> a real ratio.
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=303, amount=4000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=303, amount=40),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    row = result.iloc[0]
    assert pd.isna(row["mort_prov_coverage"])
    assert pd.isna(row["retail_prov_coverage"])
    assert row["commercial_prov_coverage"] == pytest.approx(40 / 4000)


def test_extract_coverage_duplicate_lei_for_same_firm_raises(tmp_path: Path):
    rows = [
        _row(
            lei="G5GSEF7VJP5I7OUK5573",  # Barclays Bank PLC
            label=_LABEL_EXPOSURE,
            portfolio=2,
            exposure=406,
            amount=20000,
        ),
        _row(
            lei="213800LBQA1Y9L22JB70",  # Barclays PLC (group) — same firm, same period
            label=_LABEL_EXPOSURE,
            portfolio=2,
            exposure=406,
            amount=20000,
        ),
        _row(
            lei="G5GSEF7VJP5I7OUK5573",
            label=_LABEL_PROVISIONS,
            portfolio=2,
            exposure=406,
            amount=50,
        ),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    with pytest.raises(ValueError, match="Barclays"):
        extract_coverage(csv_path, period=201812)


def test_extract_coverage_missing_expected_label_raises_listing_labels_present(tmp_path: Path):
    rows = [
        _row(label="Some Other Table (SA_and_IRB)", portfolio=2, exposure=406, amount=20000),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    with pytest.raises(ValueError, match="Some Other Table"):
        extract_coverage(csv_path, period=201812)


def test_extract_coverage_missing_required_column_raises_naming_it_and_the_file(tmp_path: Path):
    rows = [_row()]
    df = pd.DataFrame(rows, columns=_COLUMNS).drop(columns=["Status"])
    csv_path = tmp_path / "tr_cre.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Status") as exc_info:
        extract_coverage(csv_path, period=201812)
    assert "tr_cre.csv" in str(exc_info.value)


def test_extract_coverage_no_label_column_raises_predates_labelled_schema(tmp_path: Path):
    rows = [_row()]
    df = pd.DataFrame(rows, columns=_COLUMNS).drop(columns=["Label"])
    csv_path = tmp_path / "tr_cre.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="predates the labelled schema"):
        extract_coverage(csv_path, period=201812)


def test_build_panel_skips_absent_files_and_notes_them(tmp_path: Path):
    manifest = {
        2018: ("eba-transparency-2018-tr_cre.csv", 201712),
        2019: ("eba-transparency-2019-tr_cre.csv", 201812),
    }
    _write_csv(
        tmp_path / "eba-transparency-2018-tr_cre.csv",
        [
            _row(period=201712, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
            _row(period=201712, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        ],
    )
    # 2019 file deliberately absent.

    panel, notes = build_panel(tmp_path, manifest=manifest)

    assert list(panel["acsyear"]) == [2018]
    assert panel.loc[0, "firm_name"] == "Lloyds Banking Group"
    assert panel.loc[0, "mort_prov_coverage"] == pytest.approx(50 / 20000)
    assert list(panel.columns) == [
        "firm_name",
        "acsyear",
        "mort_prov_coverage",
        "retail_prov_coverage",
        "commercial_prov_coverage",
    ]
    assert any("eba-transparency-2019-tr_cre.csv" in note for note in notes)


def test_build_panel_rounds_coverage_to_6dp_and_sorts_by_firm_then_year(tmp_path: Path):
    manifest = {
        2018: ("eba-transparency-2018-tr_cre.csv", 201712),
        2019: ("eba-transparency-2019-tr_cre.csv", 201812),
    }
    _write_csv(
        tmp_path / "eba-transparency-2018-tr_cre.csv",
        [
            _row(period=201712, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=3),
            _row(period=201712, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=1),
        ],
    )
    _write_csv(
        tmp_path / "eba-transparency-2019-tr_cre.csv",
        [
            _row(period=201812, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
            _row(period=201812, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        ],
    )

    panel, _notes = build_panel(tmp_path, manifest=manifest)

    assert list(panel["acsyear"]) == [2018, 2019]
    assert panel.loc[0, "mort_prov_coverage"] == round(1 / 3, 6)


def test_build_panel_with_no_files_present_returns_empty_panel_with_columns(tmp_path: Path):
    manifest = {2018: ("eba-transparency-2018-tr_cre.csv", 201712)}

    panel, notes = build_panel(tmp_path, manifest=manifest)

    assert panel.empty
    assert list(panel.columns) == [
        "firm_name",
        "acsyear",
        "mort_prov_coverage",
        "retail_prov_coverage",
        "commercial_prov_coverage",
    ]
    assert any("eba-transparency-2018-tr_cre.csv" in note for note in notes)
    assert not (
        Path(__file__).resolve().parents[1] / "processed_inputs" / "firm_provisions_annual.csv"
    ).exists()


def test_extract_coverage_tolerates_lowercase_lei_code_column(tmp_path: Path):
    rows = [
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
    ]
    df = pd.DataFrame(rows, columns=_COLUMNS).rename(columns={"LEI_Code": "LEI_code"})
    csv_path = tmp_path / "tr_cre.csv"
    df.to_csv(csv_path, index=False)

    result = extract_coverage(csv_path, period=201812)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["firm_name"] == "Lloyds Banking Group"
    assert row["mort_prov_coverage"] == pytest.approx(50 / 20000)


def test_extract_coverage_raises_when_only_provisions_label_is_missing(tmp_path: Path):
    # Exposure rows exist but no provisions rows for the period: without a
    # guard every product would come out as a plausible-looking 0.0.
    rows = [
        _row(
            label="Original Exposure - by exposure class (SA_and_IRB)",
            portfolio=2,
            exposure=406,
            amount=20000,
        ),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    with pytest.raises(ValueError, match="Value adjustments and provisions"):
        extract_coverage(csv_path, period=201812)


def test_extract_coverage_reads_latin1_encoded_file(tmp_path: Path):
    # Real EBA tr_cre.csv files are Latin-1, not UTF-8 (bank names carry
    # accented characters). Write a fixture with a Latin-1 byte (0xf3 = o
    # acute) in the NSA column and confirm the parser reads it rather than
    # raising UnicodeDecodeError.
    rows = [
        _row(label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000, nsa="España"),
        _row(label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50, nsa="España"),
    ]
    csv_path = tmp_path / "tr_cre.csv"
    pd.DataFrame(rows, columns=_COLUMNS).to_csv(csv_path, index=False, encoding="latin-1")

    result = extract_coverage(csv_path, period=201812)

    assert len(result) == 1
    assert result.iloc[0]["firm_name"] == "Lloyds Banking Group"
    assert result.iloc[0]["mort_prov_coverage"] == pytest.approx(50 / 20000)


def test_extract_coverage_uk_only_lender_falls_back_to_total(tmp_path: Path):
    # A UK-only lender (Nationwide) reports no geographic breakdown: every
    # row is Country 0 (total). Its total is its UK book, so coverage is
    # computed from the total rows rather than dropping the firm.
    rows = [
        _row(
            lei="549300XFX12G42QIKN82",
            country=0,
            label=_LABEL_EXPOSURE,
            portfolio=2,
            exposure=406,
            amount=20000,
        ),
        _row(
            lei="549300XFX12G42QIKN82",
            country=0,
            label=_LABEL_PROVISIONS,
            portfolio=2,
            exposure=406,
            amount=50,
        ),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    assert result.iloc[0]["firm_name"] == "Nationwide"
    assert result.iloc[0]["mort_prov_coverage"] == pytest.approx(50 / 20000)


def test_extract_coverage_diversified_firm_ignores_total_when_uk_present(tmp_path: Path):
    # A firm with a distinct UK (30) slice AND an all-countries total (0)
    # must use only its UK rows; its global total must not be counted, or
    # coverage would be wrong and the exposure double-counted.
    rows = [
        _row(country=30, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=20000),
        _row(country=30, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=50),
        _row(country=0, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=999999),
        _row(country=0, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=88888),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    assert result.iloc[0]["mort_prov_coverage"] == pytest.approx(50 / 20000)


def test_extract_coverage_maps_banco_santander_uk_slice_to_santander_uk(tmp_path: Path):
    # Santander UK is consolidated into Banco Santander in the exercise;
    # its book is the UK (Country 30) slice of Banco Santander's rows. The
    # firm resolves to "Santander UK" and uses only its UK slice, not the
    # group's global total.
    banco = "5493006QMFDDMYWIAM13"
    rows = [
        _row(lei=banco, country=30, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=10000),
        _row(lei=banco, country=30, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=25),
        _row(lei=banco, country=0, label=_LABEL_EXPOSURE, portfolio=2, exposure=406, amount=500000),
        _row(
            lei=banco, country=0, label=_LABEL_PROVISIONS, portfolio=2, exposure=406, amount=44444
        ),
    ]
    csv_path = _write_csv(tmp_path / "tr_cre.csv", rows)

    result = extract_coverage(csv_path, period=201812)

    assert result.iloc[0]["firm_name"] == "Santander UK"
    assert result.iloc[0]["mort_prov_coverage"] == pytest.approx(25 / 10000)
