"""Extract macroeconomic scenario tables from BoE variable-paths workbooks.

Each BoE concurrent-stress-test scenario is published as an Excel workbook
with several sheets: the macroeconomic variables (one or more of base / ACS /
BES / "stress (s)"), yield curves, plus auxiliary disclaimers and source
notes. The legacy R analysis only consumed the macroeconomic-variables
sheet(s); this module does the same, flattening each relevant sheet into one
CSV per scenario in ``processed_inputs/``.

Public surface:
    extract_scenario(xlsx_path, out_dir) -> list[Path]
    clean_scenario_frame(df)             -> pd.DataFrame   (testable helper)

The sheet name, header-row index, and output filename are pinned per-workbook
in the ``_CONFIGS`` table below — BoE's column ordering and sheet naming
drift year-to-year, so a hand-maintained map is the simplest honest answer.
Update the table when a new scenario year is added.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Per-workbook config. Each entry: (sheet name, 0-indexed header row, output
# CSV name). Sheets that aren't macroeconomic-variables tables (Disclaimer,
# Sources and definitions, Yield curves, FAME Persistence, Index) are
# deliberately omitted.
_CONFIGS: dict[str, list[tuple[str, int, str]]] = {
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx": [
        ("Data", 0, "scenario-2014-stress.csv"),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx": [
        ("Macroeconomic variables (b) ", 1, "scenario-2015-base.csv"),
        ("Macroeconomic variables (s)", 1, "scenario-2015-stress.csv"),
    ],
    "variable-paths-for-the-2016-stress-test.xlsx": [
        ("Macroeconomic variables (b) ", 1, "scenario-2016-base.csv"),
        ("Macroeconomic variables (s)", 1, "scenario-2016-stress.csv"),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx": [
        ("Macroeconomic variables (Base) ", 1, "scenario-2017-base.csv"),
        ("Macroeconomic variables (ACS)", 1, "scenario-2017-acs.csv"),
        ("Macroeconomic variables (BES)", 1, "scenario-2017-bes.csv"),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx": [
        ("Macroeconomic variables (Base)", 1, "scenario-2018-base.csv"),
        ("Macroeconomic variables (ACS)", 1, "scenario-2018-acs.csv"),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx": [
        ("Macroeconomic variables (Base) ", 1, "scenario-2019-base.csv"),
        ("Macroeconomic variables (ACS)", 1, "scenario-2019-acs.csv"),
    ],
    "variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.XLSX": [
        (
            "Stress scenario - Rates Down ",
            1,
            "scenario-2019-non-participants-rates-down.csv",
        ),
        (
            "Stress scenario - Rates Up ",
            1,
            "scenario-2019-non-participants-rates-up.csv",
        ),
    ],
}

# Quarter label used as the row-key in col A of every macro-variables sheet,
# e.g. "Q1 2000". Used both to identify data rows and to drop section
# dividers like "Historical data" / "Stress projection" / "Sources:".
_QUARTER_RE = re.compile(r"^Q[1-4]\s+\d{4}$")


@dataclass
class ExtractReport:
    csv_paths: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)


def clean_scenario_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy a raw scenario DataFrame freshly read from a BoE workbook sheet.

    - Rename the (typically unnamed) first column to ``quarter``.
    - Keep only rows whose ``quarter`` matches the ``Qx YYYY`` pattern,
      dropping section divider rows ("Historical data", "Stress projection")
      and any trailing notes.
    - Drop columns that are entirely empty (BoE workbooks use blank columns
      as visual section separators).
    """
    out = df.copy()
    first_col = out.columns[0]
    out = out.rename(columns={first_col: "quarter"})
    quarter_strings = out["quarter"].astype(str)
    keep = quarter_strings.str.match(_QUARTER_RE.pattern, na=False)
    out = out[keep]
    out = out.dropna(axis=1, how="all")
    out = out.reset_index(drop=True)
    return out


def extract_scenario(xlsx_path: Path, out_dir: Path) -> list[Path]:
    """Extract every configured scenario sheet from ``xlsx_path`` to CSV.

    Raises ``KeyError`` if the workbook isn't registered in ``_CONFIGS``.
    """
    config = _CONFIGS.get(xlsx_path.name)
    if config is None:
        raise KeyError(f"No scenario config registered for {xlsx_path.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for sheet_name, header_row, out_name in config:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=header_row)
        cleaned = clean_scenario_frame(df)
        out_path = out_dir / out_name
        cleaned.to_csv(out_path, index=False)
        written.append(out_path)
    return written


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    raw_dir = repo_root / "raw_inputs"
    out_dir = repo_root / "processed_inputs"
    report = ExtractReport()
    for name in _CONFIGS:
        xlsx_path = raw_dir / name
        if not xlsx_path.exists():
            report.skipped.append((xlsx_path, "not in raw_inputs/"))
            print(f"{name}: SKIPPED (not in raw_inputs/)")
            continue
        try:
            paths = extract_scenario(xlsx_path, out_dir)
        except Exception as exc:
            report.errors.append((xlsx_path, f"{type(exc).__name__}: {exc}"))
            print(f"{name}: ERROR {type(exc).__name__}: {exc}")
            continue
        report.csv_paths.extend(paths)
        print(f"{name}: {len(paths)} CSV(s) -> {[p.name for p in paths]}")
    print(f"\nTotal: {len(report.csv_paths)} CSV(s) -> {out_dir.relative_to(repo_root)}")
    if report.skipped:
        print(f"Skipped {len(report.skipped)}; missing workbooks: ", end="")
        print(", ".join(p.name for p, _ in report.skipped))
    if report.errors:
        print(f"Errors {len(report.errors)}:")
        for p, msg in report.errors:
            print(f"  {p.name}: {msg}")


if __name__ == "__main__":
    main()
