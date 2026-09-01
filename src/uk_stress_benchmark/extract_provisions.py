"""Extract annual provision-coverage panel from EBA Transparency Exercise CSVs.

The EBA's EU-wide Transparency Exercise publishes, per exercise year, a long
"tr_cre" credit-risk CSV: one row per (bank, period, item, breakdown). Each
row carries a gross exposure amount or a stock of provisions for one
exposure class, portfolio (standardised / IRB), counterparty country and
default-status breakdown. This module picks out the UK-counterparty,
no-breakdown rows for the three product exposure classes the analysis
tracks (mortgage, unsecured retail, commercial), sums standardised + IRB,
and divides provisions by gross exposure to get a coverage ratio per firm
per product — the annual counterpart of the static, hand-compiled
``processed_inputs/firm_provisions.csv`` (see
``scripts/derive_firm_provisions.py``).

EBA's column naming and exposure-class code list drifted only slightly
across the 2018-2020 exercises (occasional case changes to ``LEI_Code``);
pre-2018 exercises used numeric ``Item`` codes with no ``Label`` column at
all and aren't supported here — ``extract_coverage`` raises a clear error
naming the file rather than silently reading nonsense.

Public surface:
    extract_coverage(csv_path, *, period, country="GB") -> pd.DataFrame
    build_panel(raw_dir, manifest=TRANSPARENCY_MANIFEST) -> (panel, notes)
    main() -> None
    TRANSPARENCY_MANIFEST: dict[int, tuple[str, int]]
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

# Bank LEI -> canonical firm name. Rows for any other LEI are ignored.
_LEI_TO_FIRM: dict[str, str] = {
    "G5GSEF7VJP5I7OUK5573": "Barclays",  # Barclays Bank PLC (2018 exercise)
    "213800LBQA1Y9L22JB70": "Barclays",  # Barclays PLC (group)
    "MLU0ZO3ML4LN2LL2TL39": "HSBC",
    "549300PPXHEU2JF0AM85": "Lloyds Banking Group",
    "2138005O9XJIJN4JPN90": "The Royal Bank of Scotland Group",
    "549300XFX12G42QIKN82": "Nationwide",
    "U4LOSYZ7YG4W3S5F2G91": "Standard Chartered",
    "PTCQB104N23FMNK2RZ28": "Santander UK",
}

_LABEL_EXPOSURE = "Original Exposure - by exposure class (SA_and_IRB)"
_LABEL_PROVISIONS = "Value adjustments and provisions - by exposure class (SA_and_IRB)"

# Every column this module ever reads, for case-insensitive normalisation.
_KNOWN_COLUMNS: tuple[str, ...] = (
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
)

_REQUIRED_COLUMNS: tuple[str, ...] = (
    "LEI_Code",
    "Period",
    "Label",
    "Portfolio",
    "Country",
    "Exposure",
    "Status",
    "Amount",
)

# output product column -> {(portfolio, exposure_code), ...} to sum. Deliberately
# excludes "of which" sub-rows (407/408/411/412/302/304/305) to avoid double
# counting.
_PRODUCT_CODES: dict[str, set[tuple[int, int]]] = {
    "mort_prov_coverage": {(2, 406), (1, 501)},
    "retail_prov_coverage": {(2, 409), (2, 410), (1, 404)},
    "commercial_prov_coverage": {(2, 303), (1, 303)},
}

_PANEL_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "acsyear",
    "mort_prov_coverage",
    "retail_prov_coverage",
    "commercial_prov_coverage",
)

# country param -> accepted stripped-string codes in the source data.
_COUNTRY_CODES: dict[str, set[str]] = {
    "GB": {"30", "GB"},
    "00": {"0", "00"},
}

# ACS year -> (raw EBA tr_cre filename, reference period YYYYMM). 2020 has no
# matching ACS but is kept: it's the only file with a verified download URL,
# so it doubles as the real-data smoke test of this parser, and gives the
# app each firm's most recent coverage.
TRANSPARENCY_MANIFEST: dict[int, tuple[str, int]] = {
    2015: ("eba-transparency-2015-tr_cre.csv", 201412),
    2016: ("eba-transparency-2016-tr_cre.csv", 201512),
    2017: ("eba-transparency-2017-tr_cre.csv", 201612),
    2018: ("eba-transparency-2018-tr_cre.csv", 201712),
    2019: ("eba-transparency-2019-tr_cre.csv", 201812),
    2020: ("eba-transparency-2020-tr_cre.csv", 201912),
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to their canonical case, matched case-insensitively.

    Unknown columns (e.g. a trailing footnote column) pass through untouched.
    """
    lookup = {name.lower(): name for name in _KNOWN_COLUMNS}
    rename = {}
    for col in df.columns:
        canonical = lookup.get(str(col).strip().lower())
        if canonical is not None:
            rename[col] = canonical
    return df.rename(columns=rename)


def extract_coverage(csv_path: Path | str, *, period: int, country: str = "GB") -> pd.DataFrame:
    """Compute per-firm provision coverage for one EBA tr_cre CSV and period.

    Returns one row per firm found in the file for ``period`` (after country
    and status filtering), with columns ``firm_name``,
    ``mort_prov_coverage``, ``retail_prov_coverage``,
    ``commercial_prov_coverage``. A product's coverage is NaN if its
    denominator (gross exposure) is zero or absent.

    Raises ``ValueError`` if a required column is missing (naming the file
    and, when the file has no ``Label`` column at all, saying it predates
    the labelled schema), if either the exposure or the provisions label
    is absent for ``period``, or if two different LEIs mapping to the same
    firm both have rows in ``period`` (which would double count).
    """
    csv_path = Path(csv_path)
    if country not in _COUNTRY_CODES:
        raise ValueError(
            f"Unknown country code {country!r}; expected one of {sorted(_COUNTRY_CODES)}"
        )

    df = _normalise_columns(pd.read_csv(csv_path, dtype=str))

    missing = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
    if "Label" in missing:
        raise ValueError(
            f"{csv_path.name}: no Label column — file predates the labelled schema "
            "(pre-2018 EBA Transparency Exercises used numeric Item codes only)"
        )
    if missing:
        raise ValueError(f"{csv_path.name}: missing required column(s): {', '.join(missing)}")

    period_rows = df.loc[df["Period"].astype(str).str.strip() == str(period).strip()].copy()

    labels = period_rows["Label"].astype(str).str.strip()
    absent = [
        label for label in (_LABEL_EXPOSURE, _LABEL_PROVISIONS) if not (labels == label).any()
    ]
    if absent:
        # Either side missing would silently yield 0.0 (no provisions) or NaN
        # (no exposure) for every firm, so refuse and show what the file has.
        present = sorted(labels.dropna().unique())
        raise ValueError(
            f"{csv_path.name}: expected Label(s) not found for period {period}: {absent}; "
            f"labels present: {present}"
        )
    period_rows["Label"] = labels

    country_codes = _COUNTRY_CODES[country]
    period_rows["Country"] = period_rows["Country"].astype(str).str.strip()
    period_rows["Status"] = period_rows["Status"].astype(str).str.strip()
    if "Perf_Status" in period_rows.columns:
        perf = period_rows["Perf_Status"].astype(str).str.strip()
        perf_ok = perf.isin({"0", "", "nan"})
    else:
        perf_ok = pd.Series(True, index=period_rows.index)

    period_rows["LEI_Code"] = period_rows["LEI_Code"].astype(str).str.strip()
    period_rows["firm_name"] = period_rows["LEI_Code"].map(_LEI_TO_FIRM)

    relevant = period_rows.loc[
        period_rows["Country"].isin(country_codes)
        & (period_rows["Status"] == "0")
        & perf_ok
        & period_rows["firm_name"].notna()
    ].copy()

    lei_per_firm = relevant.groupby("firm_name")["LEI_Code"].unique()
    for firm, leis in lei_per_firm.items():
        if len(leis) > 1:
            raise ValueError(
                f"{csv_path.name}: multiple LEIs map to {firm!r} in period {period}: "
                f"{sorted(leis)} — would double count"
            )

    relevant["Portfolio"] = pd.to_numeric(relevant["Portfolio"], errors="coerce")
    relevant["Exposure"] = pd.to_numeric(relevant["Exposure"], errors="coerce")
    relevant["Amount"] = pd.to_numeric(relevant["Amount"], errors="coerce")
    relevant["_code"] = list(zip(relevant["Portfolio"], relevant["Exposure"], strict=True))

    rows: list[dict[str, object]] = []
    for firm in sorted(relevant["firm_name"].unique()):
        firm_rows = relevant.loc[relevant["firm_name"] == firm]
        row: dict[str, object] = {"firm_name": firm}
        for product, codes in _PRODUCT_CODES.items():
            in_product = firm_rows["_code"].isin(codes)
            denominator = firm_rows.loc[
                in_product & (firm_rows["Label"] == _LABEL_EXPOSURE), "Amount"
            ].sum()
            numerator = firm_rows.loc[
                in_product & (firm_rows["Label"] == _LABEL_PROVISIONS), "Amount"
            ].sum()
            row[product] = (numerator / denominator) if denominator else float("nan")
        rows.append(row)

    return pd.DataFrame(rows, columns=["firm_name", *_PRODUCT_CODES.keys()])


def build_panel(
    raw_dir: Path, manifest: Mapping[int, tuple[str, int]] = TRANSPARENCY_MANIFEST
) -> tuple[pd.DataFrame, list[str]]:
    """Build the annual coverage panel across every manifest entry present in ``raw_dir``.

    Files not present in ``raw_dir`` are skipped (not an error) and noted.
    Returns ``(panel, notes)``: ``panel`` has an ``acsyear`` column and rows
    only for the years whose raw file was present; ``notes`` is a list of
    human-readable lines (one per manifest entry) suitable for printing.
    """
    raw_dir = Path(raw_dir)
    notes: list[str] = []
    frames: list[pd.DataFrame] = []
    for acsyear, (filename, period) in manifest.items():
        csv_path = raw_dir / filename
        if not csv_path.exists():
            notes.append(f"{filename}: SKIPPED (not in raw_inputs/)")
            continue
        coverage = extract_coverage(csv_path, period=period)
        coverage = coverage.copy()
        coverage["acsyear"] = acsyear
        frames.append(coverage)
        notes.append(f"{filename}: {len(coverage)} firm(s) -> acsyear {acsyear}")

    if not frames:
        return pd.DataFrame(columns=list(_PANEL_COLUMNS)), notes

    panel = pd.concat(frames, ignore_index=True).loc[:, list(_PANEL_COLUMNS)]
    for col in _PANEL_COLUMNS[2:]:
        panel[col] = panel[col].round(6)
    panel = panel.sort_values(["firm_name", "acsyear"]).reset_index(drop=True)
    return panel, notes


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    raw_dir = repo_root / "raw_inputs"
    out_path = repo_root / "processed_inputs" / "firm_provisions_annual.csv"

    panel, notes = build_panel(raw_dir)
    for note in notes:
        print(note)

    if panel.empty:
        print(
            "No EBA Transparency Exercise CSVs found in raw_inputs/; "
            "firm_provisions_annual.csv not written."
        )
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out_path, index=False)
    print(f"Wrote {len(panel)} rows -> {out_path.relative_to(repo_root)}")
    print(f"Years: {sorted(panel['acsyear'].unique())}")
    print(f"Firms: {sorted(panel['firm_name'].unique())}")


if __name__ == "__main__":
    main()
