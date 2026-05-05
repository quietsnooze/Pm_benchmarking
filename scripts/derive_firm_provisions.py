"""One-off conversion: legacy provisions XLSX -> processed_inputs/firm_provisions.csv.

The 2019 firm-level provisions-coverage file under
``old_version/stress test benchmarks/pillar 3 disclosures/2019 provisions coverage by firm.xlsx``
is a manual compilation from multiple firms' Pillar 3 disclosures — there's
no public URL to download it from. This script transcribes the workbook
into the canonical CSV shape so the rest of the analytics pipeline depends
only on a committed CSV (not on the local-only XLSX).

Run once, manually, when bootstrapping a fresh clone (or whenever the legacy
workbook is updated)::

    uv run python scripts/derive_firm_provisions.py

Output: ``processed_inputs/firm_provisions.csv`` — committed; becomes the
source of truth for downstream loaders.

This script is *not* registered as a console script in ``pyproject.toml``
because it depends on the local-only ``old_version/`` directory and isn't
part of the reproducible-from-clean ingest pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Map legacy short firm codes (used in the source XLSX and the legacy
# results.csv) to the canonical long form used by aggregate_firm_results.
_FIRM_NAME_MAP: dict[str, str] = {
    "Barclays": "Barclays",
    "HSBC": "HSBC",
    "LBG": "Lloyds Banking Group",
    "Nationwide": "Nationwide",
    "RBS": "The Royal Bank of Scotland Group",
    "SanUK": "Santander UK",
    "SCB": "Standard Chartered",
}

_OUTPUT_COLS: list[str] = [
    "firm_name",
    "mort_prov_coverage",
    "retail_prov_coverage",
    "commercial_prov_coverage",
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_xlsx = (
        repo_root
        / "old_version"
        / "stress test benchmarks"
        / "pillar 3 disclosures"
        / "2019 provisions coverage by firm.xlsx"
    )
    out_csv = repo_root / "processed_inputs" / "firm_provisions.csv"

    if not src_xlsx.exists():
        raise SystemExit(f"Source not found: {src_xlsx}")

    df = pd.read_excel(src_xlsx, sheet_name=0)
    df = df.rename(
        columns={
            "Firm name": "firm_short",
            "mort prov coverage": "mort_prov_coverage",
            "retail prov coverage": "retail_prov_coverage",
            "commercial prov coverage": "commercial_prov_coverage",
        }
    )
    df["firm_name"] = df["firm_short"].map(_FIRM_NAME_MAP)
    unmapped = df.loc[df["firm_name"].isna() & df["firm_short"].notna(), "firm_short"]
    if not unmapped.empty:
        print(f"warn: dropping unmapped firm codes: {unmapped.tolist()}")
        df = df.dropna(subset=["firm_name"])

    out = df[_OUTPUT_COLS].sort_values("firm_name").reset_index(drop=True)
    # Round to 6 decimal places to scrub IEEE-754 float artifacts that the
    # legacy XLSX picked up (e.g. 0.0028 stored as 0.0028000000000000004).
    # Coverage ratios are rounded percentages — 6 dp is well below the
    # source's effective precision.
    for col in _OUTPUT_COLS[1:]:
        out[col] = out[col].round(6)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    print(f"Wrote {len(out)} rows -> {out_csv.relative_to(repo_root)}")
    print(f"Firms: {sorted(out['firm_name'].tolist())}")


if __name__ == "__main__":
    main()
