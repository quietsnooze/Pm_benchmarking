"""Load and validate the hand-transcribed annual-report coverage panel.

``processed_inputs/firm_provisions_annual_reports.csv`` holds per-firm,
per-year mortgage and unsecured-retail provision coverage transcribed from
firms' annual reports and Pillar 3 disclosures — the two products the EBA
Transparency Exercise cannot separate for IRB banks (see
``extract_provisions`` and SOURCES.md). Every number is captured with its
numerator (``allowance``), denominator (``gross_loans``), accounting
``basis`` (IAS 39 vs IFRS 9), reporting ``entity``, and full source
provenance, so each ratio can be re-derived and audited from the primary
document.

This module is the one place that reads that file and vouches for it. It
hides the panel's quiet invariants behind two calls:

* :func:`load_annual_reports` reads the CSV and returns a typed frame whose
  ``coverage`` is always ``allowance / gross_loans`` computed here, never a
  hand-typed ratio. It refuses a file that would otherwise pass silently
  wrong — a missing column, an unknown product or basis, a coverage that
  contradicts its own two figures, or a half-filled numeric row (one of
  allowance/gross present, the other blank). A fully-blank numeric row is
  allowed: it records a firm-year whose report gave no mortgage/unsecured
  split, an honest gap rather than a guess.
* :func:`check_sanity` returns human-readable flags for coverage ratios
  outside each product's plausible band. Out-of-range values are surfaced,
  never dropped or clamped: a genuine outlier may be real (and explained in
  the row's ``notes``), so this informs rather than fails the load.

Public surface:
    load_annual_reports(csv_path) -> pd.DataFrame
    check_sanity(panel) -> list[str]
    main() -> None
    REQUIRED_COLUMNS: tuple[str, ...]
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "acsyear",
    "product",
    "allowance",
    "gross_loans",
    "coverage",
    "basis",
    "entity",
    "currency",
    "source_url",
    "source_table",
    "source_page",
    "notes",
)

_VALID_PRODUCTS: frozenset[str] = frozenset({"mortgage", "unsecured_retail"})
_VALID_BASES: frozenset[str] = frozenset({"IAS39", "IFRS9"})

# Plausible coverage band per (basis, product) — allowance / gross loans as a
# ratio. Wider than any single year's spread on purpose: the point is to catch
# a transcription off by an order of magnitude or a numerator/denominator swap,
# not to police normal variation. The IFRS 9 bands are the task's sanity
# ranges (mortgage ~0.05-0.6%, unsecured ~3-12%); the IAS 39 (incurred-loss)
# bands run lower, because incurred-loss provisions are structurally smaller
# than IFRS 9 expected-credit-loss allowances — an IAS 39 unsecured book near
# 1.5% is normal, not an outlier.
_SANE_BANDS: dict[tuple[str, str], tuple[float, float]] = {
    ("IFRS9", "mortgage"): (0.0005, 0.006),
    # floor 2.5% not 3%: a prime UK unsecured book (e.g. HSBC UK) sits just
    # under 3% ECL coverage — real, not an error to flag.
    ("IFRS9", "unsecured_retail"): (0.025, 0.12),
    # ceiling 0.8% not 0.6%: a group mortgage book with a distressed Irish/Ulster
    # tail (RBS/NatWest, IAS 39 era) runs to ~0.66% — real, not an error.
    ("IAS39", "mortgage"): (0.0002, 0.008),
    ("IAS39", "unsecured_retail"): (0.008, 0.10),
}

# coverage recomputed from allowance/gross must match any hand-entered
# coverage to this relative tolerance; looser than float noise because a
# transcribed coverage is typically rounded to a few significant figures.
_COVERAGE_RTOL = 5e-3


def _numeric(series: pd.Series) -> pd.Series:
    """Parse a string column of amounts to float, tolerating thousands commas
    and blank cells (which become NaN)."""
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    cleaned = cleaned.where(~cleaned.isin({"", "nan", "None"}))
    return pd.Series(pd.to_numeric(cleaned, errors="coerce"))


def load_annual_reports(csv_path: Path | str) -> pd.DataFrame:
    """Read the annual-report coverage panel, validating and recomputing coverage.

    Returns a frame with ``allowance``, ``gross_loans`` and ``coverage`` as
    floats (NaN where the source reported no split) and every other column as
    read. ``coverage`` is ``allowance / gross_loans`` computed here; any
    coverage already in the file is treated only as a check.

    Raises ``ValueError`` (naming the file and the offending row) when a
    required column is missing, a ``product`` or ``basis`` is unknown, a
    numeric row is half-filled (exactly one of allowance/gross blank), or a
    hand-entered coverage disagrees with ``allowance / gross_loans``.
    """
    csv_path = Path(csv_path)
    df: pd.DataFrame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path.name}: missing required column(s): {', '.join(missing)}")

    products = df["product"].astype(str).str.strip()
    bad_products = sorted(set(products) - _VALID_PRODUCTS)
    if bad_products:
        raise ValueError(
            f"{csv_path.name}: unknown product value(s) {bad_products}; "
            f"expected one of {sorted(_VALID_PRODUCTS)}"
        )

    bases = df["basis"].astype(str).str.strip()
    bad_bases = sorted(set(bases) - _VALID_BASES)
    if bad_bases:
        raise ValueError(
            f"{csv_path.name}: unknown basis value(s) {bad_bases}; "
            f"expected one of {sorted(_VALID_BASES)}"
        )

    allowance = _numeric(df["allowance"])  # type: ignore[arg-type]
    gross = _numeric(df["gross_loans"])  # type: ignore[arg-type]
    typed_coverage = _numeric(df["coverage"])  # type: ignore[arg-type]

    half_filled = allowance.isna() ^ gross.isna()
    if bool(half_filled.any()):
        i = half_filled.idxmax()
        raise ValueError(
            f"{csv_path.name}: row {i} ({df.loc[i, 'firm_name']} {df.loc[i, 'acsyear']} "
            f"{df.loc[i, 'product']}) is an incomplete transcription — exactly one of "
            "allowance/gross_loans is blank; fill both, or blank both for a documented gap"
        )

    both_present = allowance.notna() & gross.notna()
    coverage = pd.Series(float("nan"), index=df.index, dtype="float64")
    coverage[both_present] = allowance[both_present] / gross[both_present]

    # Any coverage the transcriber did type must match the two primary figures.
    within_tol = (typed_coverage - coverage).abs() <= (coverage.abs() * _COVERAGE_RTOL)
    mismatch = both_present & typed_coverage.notna() & ~within_tol.fillna(False)
    if mismatch.any():
        i = mismatch.idxmax()
        raise ValueError(
            f"{csv_path.name}: row {i} ({df.loc[i, 'firm_name']} {df.loc[i, 'acsyear']} "
            f"{df.loc[i, 'product']}) coverage {typed_coverage[i]} disagrees with "
            f"allowance/gross_loans = {coverage[i]:.6g}"
        )

    out = df.copy()
    out["allowance"] = allowance
    out["gross_loans"] = gross
    out["coverage"] = coverage
    out["acsyear"] = pd.Series(pd.to_numeric(df["acsyear"], errors="coerce")).astype("Int64")
    return out


def check_sanity(panel: pd.DataFrame) -> list[str]:
    """Return one flag string per coverage ratio outside its product's plausible
    band. Empty when every populated ratio is in range. Rows with blank
    coverage (documented gaps) are skipped."""
    flags: list[str] = []
    for _, row in panel.iterrows():
        product = str(row["product"]).strip()
        basis = str(row["basis"]).strip()
        coverage = row["coverage"]
        band = _SANE_BANDS.get((basis, product))
        if band is None or bool(pd.isna(coverage)):
            continue
        low, high = band
        if not (low <= coverage <= high):
            flags.append(
                f"{row['firm_name']} {row['acsyear']} {product} ({basis}): coverage "
                f"{coverage:.4%} outside plausible band {low:.2%}-{high:.2%} — verify or note"
            )
    return flags


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    csv_path = repo_root / "processed_inputs" / "firm_provisions_annual_reports.csv"

    if not csv_path.exists():
        print(f"{csv_path.relative_to(repo_root)} not found; nothing to validate.")
        return

    panel = load_annual_reports(csv_path)
    coverage_col = pd.Series(panel["coverage"])
    populated = int(coverage_col.notna().sum())
    gaps = int(coverage_col.isna().sum())
    print(f"Loaded {len(panel)} rows ({populated} populated, {gaps} documented gap(s)).")

    flags = check_sanity(panel)
    if flags:
        print(f"{len(flags)} sanity flag(s):")
        for flag in flags:
            print(f"  ! {flag}")
    else:
        print("All populated coverage ratios are within plausible bands.")


if __name__ == "__main__":
    main()
