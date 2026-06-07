"""Aggregate per-firm impairment-charge percentages from the BoE Annex CSVs.

The ``extract-tables`` step writes one CSV per BoE results-PDF Annex table to
``processed_inputs/{year}_table-{id}.csv``. Each CSV has columns
``firm, col_1, col_2, ...`` because the original PDF column headers don't
survive text extraction cleanly. This module knows the per-(year, table_id)
column meaning, walks the registered tables, and emits one tidy CSV with the
shape expected by downstream modeling code:

    firm_name | acsyear | uk_mort_3yr_ic_pct | uk_retail_3yr_ic_pct | uk_cre_3yr_ic_pct |
                          uk_mort_5yr_ic_pct | uk_retail_5yr_ic_pct | uk_cre_5yr_ic_pct |
                          uk_bus_5yr_ic_pct

Values are decimals (so 0.5 percent is stored as 0.005); the source PDFs use
"-" or "–" for "not applicable" and those become NaN. Coverage today: ACS
years 2014–2017 (Stage 1a); years 2018–2019 will be added by Stage 1b once
the FSR PDFs are extracted.

Public surface:
    build_firm_results(processed_dir: Path) -> pd.DataFrame
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Per (year, sanitised_table_id), map "col_N" in the extracted CSV to the
# canonical output column. Tables not listed here are ignored — that includes
# the £-billion charge tables (Table 2B / 2D / A5.B / A5.D), the merged
# side-by-side Hong Kong / China and traded-risk tables, and 2014 Table 2
# (which is the £-billion partner of Table 1 and adds no new information).
_TABLE_MAPPINGS: dict[tuple[str, str], dict[str, str]] = {
    ("2014", "1"): {
        "col_1": "uk_mort_3yr_ic_pct",
        "col_2": "uk_retail_3yr_ic_pct",
        "col_3": "uk_cre_3yr_ic_pct",
    },
    ("2015", "2A"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
    ("2015", "2C"): {
        "col_1": "uk_mort_3yr_ic_pct",
        "col_2": "uk_retail_3yr_ic_pct",
        "col_3": "uk_cre_3yr_ic_pct",
        # 2C col_4 (business 3yr) intentionally dropped — legacy results.csv
        # has no uk_bus_3yr_ic_pct column.
    },
    ("2016", "2A"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
    ("2017", "A5A"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
    # 2018 stress-test results were published inside the November 2018 FSR
    # under "Annex 5"; same per-firm × per-product shape as 2017 Table A5.A.
    ("2018", "A5A"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
    # 2019 results were published inside the December 2019 FSR under
    # "Annex 4" (renumbered from A5 to A4); same shape as 2018 Table A5.A.
    ("2019", "A4A"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
    # 2025 Bank Capital Stress Test: bank-specific impairment-charge rates moved
    # to "Annex 3, Table A3.1" but keep the same four-product shape. Columns are
    # mortgage / non-mortgage retail / CRE / business (excluding CRE).
    ("2025", "A31"): {
        "col_1": "uk_mort_5yr_ic_pct",
        "col_2": "uk_retail_5yr_ic_pct",
        "col_3": "uk_cre_5yr_ic_pct",
        "col_4": "uk_bus_5yr_ic_pct",
    },
}

# Firm-name canonicalisation. BoE drops "Group" off "The Royal Bank of
# Scotland Group" in some tables (e.g. 2017 A5.C); we collapse to one form
# so downstream code sees a single firm identity.
_FIRM_CANONICAL: dict[str, str] = {
    "The Royal Bank of Scotland": "The Royal Bank of Scotland Group",
    # RBS rebranded to NatWest Group in 2020; collapse to the legacy identity so
    # the firm has one continuous identity across the 2014-2019 and 2021+ eras
    # (provisions and firm dummies key on the legacy name).
    "NatWest Group": "The Royal Bank of Scotland Group",
}

# Output column order — matches the legacy R `results.csv` shape.
_OUTPUT_COLS: tuple[str, ...] = (
    "firm_name",
    "acsyear",
    "uk_mort_3yr_ic_pct",
    "uk_retail_3yr_ic_pct",
    "uk_cre_3yr_ic_pct",
    "uk_mort_5yr_ic_pct",
    "uk_retail_5yr_ic_pct",
    "uk_cre_5yr_ic_pct",
    "uk_bus_5yr_ic_pct",
)

_FILENAME_RE = re.compile(r"^(?P<year>\d{4})_table-(?P<id>[A-Za-z0-9]+)\.csv$")


def _parse_pct_value(raw: object) -> float:
    """Coerce one Annex cell into a decimal.

    The 2014 PDFs encode percentages as "0.9%"-style strings; 2015+ use bare
    numbers (``0.7`` meaning 0.7 percent). Both end up as decimals (0.009 /
    0.007). "-" (hyphen) and "–" (en dash) are the source-PDF conventions
    for "not applicable" and become NaN.
    """
    if raw is None or bool(pd.isna(raw)):
        return float("nan")
    text = str(raw).strip()
    if text in {"-", "–", ""}:
        return float("nan")
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return float(text) / 100.0
    except ValueError:
        return float("nan")


def build_firm_results(processed_dir: Path) -> pd.DataFrame:
    """Aggregate firm × product impairment-charge percentages across years.

    Reads every ``{year}_table-{id}.csv`` whose ``(year, id)`` is registered
    in ``_TABLE_MAPPINGS``, applies the per-table column mapping, normalises
    firm names, and returns one row per ``(firm_name, acsyear)``. Files
    outside the mapping (£-billion tables, traded-risk losses, merged
    side-by-side tables) are silently ignored.
    """
    rows: dict[tuple[str, str], dict[str, float | str]] = {}

    for csv_path in sorted(processed_dir.glob("*_table-*.csv")):
        match = _FILENAME_RE.match(csv_path.name)
        if match is None:
            continue
        year = match.group("year")
        table_id = match.group("id")
        mapping = _TABLE_MAPPINGS.get((year, table_id))
        if mapping is None:
            continue

        df = pd.read_csv(csv_path, dtype=str)
        for _, raw_row in df.iterrows():
            raw_firm = str(raw_row.get("firm", "")).strip()
            firm = _FIRM_CANONICAL.get(raw_firm, raw_firm)
            if not firm:
                continue
            key = (firm, year)
            if key not in rows:
                rows[key] = {"firm_name": firm, "acsyear": year}
            for src_col, dst_col in mapping.items():
                rows[key][dst_col] = _parse_pct_value(raw_row.get(src_col))

    if not rows:
        return pd.DataFrame(columns=list(_OUTPUT_COLS))

    frame = pd.DataFrame(rows.values())
    # Make sure every canonical column exists even if no source table populated it.
    for col in _OUTPUT_COLS:
        if col not in frame.columns:
            frame[col] = float("nan")
    return (
        frame.loc[:, list(_OUTPUT_COLS)]
        .sort_values(["acsyear", "firm_name"])
        .reset_index(drop=True)
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    processed_dir = repo_root / "processed_inputs"
    out_path = processed_dir / "firm_results.csv"
    frame = build_firm_results(processed_dir)
    frame.to_csv(out_path, index=False)
    print(f"Wrote {len(frame)} rows -> {out_path.relative_to(repo_root)}")
    if not frame.empty:
        print(f"Years: {sorted(frame['acsyear'].unique())}")
        print(f"Firms: {sorted(frame['firm_name'].unique())}")


if __name__ == "__main__":
    main()
