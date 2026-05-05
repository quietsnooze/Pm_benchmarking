from pathlib import Path

import pytest

from uk_stress_benchmark.extract_appendix_tables import (
    extract_appendix_tables,
    parse_table_block,
)

# Hand-typed fixture mirroring the structure of the 2015 Table 2B block, with
# multi-firm names, the £ unit line, multi-line wrapped headers, and a
# Sources: footer that should terminate the block.
FIXTURE_2015_TABLE_2B = """\
Table 2B Projected cumulative five-year impairment charges on UK lending in the stress scenario(a)(b)
£ billions
Mortgage lending Non-mortgage lending Commercial real Lending to businesses
to individuals to individuals estate lending excluding commercial
real estate
Barclays 0.3 7.2 0.3 3.1
HSBC 0.2 1.0 0.3 1.5
Lloyds Banking Group 3.5 4.6 1.4 2.7
Nationwide 0.5 0.7 0.4 -
The Royal Bank of Scotland Group 0.6 2.1 0.9 2.7
Santander UK 0.9 1.3 0.6 0.9
Standard Chartered - - - 0.1
Sources: Participating banks' FDSF data submissions, Bank analysis and calculations.
(a) The HSBC and Standard Chartered impairment charge is calculated by first ...
"""


def _block(text: str) -> list[str]:
    return text.splitlines()


def test_parse_extracts_id_title_unit_and_all_seven_firm_rows():
    table = parse_table_block(_block(FIXTURE_2015_TABLE_2B))

    assert table is not None
    assert table.table_id == "2B"
    assert table.title.startswith("Projected cumulative five-year impairment charges")
    assert table.unit.lower().startswith("£ billion")
    assert len(table.rows) == 7

    # Spot-check a few firms (anchoring the multi-word match)
    rows_by_firm = dict((row[0], row[1:]) for row in table.rows)
    assert rows_by_firm["Barclays"] == ("0.3", "7.2", "0.3", "3.1")
    assert rows_by_firm["Lloyds Banking Group"] == ("3.5", "4.6", "1.4", "2.7")
    assert rows_by_firm["The Royal Bank of Scotland Group"] == (
        "0.6",
        "2.1",
        "0.9",
        "2.7",
    )
    assert rows_by_firm["Standard Chartered"] == ("-", "-", "-", "0.1")


def test_parse_captures_wrapped_header_lines():
    table = parse_table_block(_block(FIXTURE_2015_TABLE_2B))
    assert table is not None
    # The PDF wraps the column headers across three text lines; all three
    # should land in raw_header_lines, in order, before the first data row.
    assert table.raw_header_lines[0].startswith("Mortgage lending")
    assert any("estate lending" in h for h in table.raw_header_lines)


def test_parse_stops_at_sources_footer_and_drops_footnotes():
    table = parse_table_block(_block(FIXTURE_2015_TABLE_2B))
    assert table is not None
    # The Sources: line and the (a) footnote must not be parsed as data rows.
    firms = [row[0] for row in table.rows]
    assert "Sources:" not in firms
    assert not any("HSBC and Standard" in row[0] for row in table.rows)


def test_parse_returns_none_when_block_does_not_start_with_table_header():
    bad = ["Some unrelated text", "Barclays 1 2 3"]
    assert parse_table_block(bad) is None


def test_parse_returns_none_for_empty_block():
    assert parse_table_block([]) is None


# -----------------------------------------------------------------------------
# Integration: 2018 FSR contains the same impairment-charge annex as the
# 2014–2017 results PDFs, but typesets the heading with a U+2011 non-breaking
# hyphen ("bank‑specific") instead of a regular hyphen. The annex regex must
# match both forms; this test runs only when the real PDF is available.
# -----------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FSR_2018 = _REPO_ROOT / "raw_inputs" / "november-2018.pdf"


@pytest.mark.skipif(
    not _FSR_2018.exists(),
    reason="raw_inputs/november-2018.pdf not present (run `uv run sync-sources`)",
)
def test_extracts_2018_fsr_annex_5_impairment_charge_tables(tmp_path):
    report = extract_appendix_tables(_FSR_2018, tmp_path)

    titles = [t.title.lower() for t in report.tables]
    assert any("impairment charge" in title for title in titles), (
        f"expected an impairment-charge table in 2018 FSR; got titles={titles}"
    )
    table_ids = [t.table_id for t in report.tables]
    assert any(tid.startswith("A5") for tid in table_ids), (
        f"expected at least one A5.* table from 2018 FSR; got ids={table_ids}"
    )
