"""Extract macroeconomic scenario tables from BoE variable-paths workbooks.

Each BoE concurrent-stress-test scenario is published as an Excel workbook
with several sheets: the macroeconomic variables (one or more of base / ACS /
BES / "stress (s)"), yield curves, plus auxiliary disclaimers and source
notes. The legacy R analysis only consumed the macroeconomic-variables
sheet(s); this module does the same, flattening each relevant sheet into one
CSV per scenario in ``processed_inputs/``.

Public surface:
    extract_scenario(xlsx_path, out_dir)   -> list[Path]
    clean_scenario_frame(df)               -> pd.DataFrame   (testable helper)
    add_uk_nominal_gdp_index(df)           -> pd.DataFrame   (testable helper)

The sheet name, header-row index, and output filename are pinned per-workbook
in the ``_CONFIGS`` table below — BoE's column ordering and sheet naming
drift year-to-year, so a hand-maintained map is the simplest honest answer.
Update the table when a new scenario year is added.
"""

from __future__ import annotations

import re
from collections.abc import Hashable
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pandas as pd

from uk_stress_benchmark import scenario_index
from uk_stress_benchmark.scenario_index import ScenarioRecord

# 2014's BoE workbook uses a different column-naming convention from the
# 2015-2019 workbooks (no "UK " prefix on UK-specific variables, and a
# different name for the residential property price index). Rename the
# variables this analysis actually uses so the 2014 CSV shares a vocabulary
# with the others. Untouched columns keep their original names.
_RENAMES_2014: dict[str, str] = {
    "Nominal GDP": "UK nominal GDP",
    "Unemployment rate": "UK unemployment rate",
    "House price index": "UK residential property price index",
    "Commercial real estate price index ": "UK commercial real estate price index - aggregate",
}

# The 2025 Bank Capital Stress Test workbook drops the "- aggregate" suffix on
# the CRE index; rename so it shares the analysis vocabulary with 2014-2019.
_RENAMES_2025: dict[str, str] = {
    "UK commercial real estate price index": "UK commercial real estate price index - aggregate",
}


@dataclass(frozen=True)
class _SheetConfig:
    sheet_name: str
    header_row: int  # 0-indexed
    out_name: str
    acsyear: int
    role: str  # "stress" / "base" / "acs" / "bes" / "non-participants"
    model_input: bool = False  # the one canonical stressed scenario per year
    column_renames: dict[str, str] | None = None


# Per-workbook config. Sheets that aren't macroeconomic-variables tables
# (Disclaimer, Sources and definitions, Yield curves, FAME Persistence,
# Index) are deliberately omitted. ``model_input`` marks the single scenario
# per year fed to the regression (2014-2016 publish only "stress"; 2017+ use
# "acs"); base / BES / non-participant scenarios are recorded but not modelled.
_CONFIGS: dict[str, list[_SheetConfig]] = {
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx": [
        _SheetConfig("Data", 0, "scenario-2014-stress.csv", 2014, "stress", True, _RENAMES_2014),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx": [
        _SheetConfig("Macroeconomic variables (b) ", 1, "scenario-2015-base.csv", 2015, "base"),
        _SheetConfig(
            "Macroeconomic variables (s)", 1, "scenario-2015-stress.csv", 2015, "stress", True
        ),
    ],
    "variable-paths-for-the-2016-stress-test.xlsx": [
        _SheetConfig("Macroeconomic variables (b) ", 1, "scenario-2016-base.csv", 2016, "base"),
        _SheetConfig(
            "Macroeconomic variables (s)", 1, "scenario-2016-stress.csv", 2016, "stress", True
        ),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx": [
        _SheetConfig("Macroeconomic variables (Base) ", 1, "scenario-2017-base.csv", 2017, "base"),
        _SheetConfig(
            "Macroeconomic variables (ACS)", 1, "scenario-2017-acs.csv", 2017, "acs", True
        ),
        _SheetConfig("Macroeconomic variables (BES)", 1, "scenario-2017-bes.csv", 2017, "bes"),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx": [
        _SheetConfig("Macroeconomic variables (Base)", 1, "scenario-2018-base.csv", 2018, "base"),
        _SheetConfig(
            "Macroeconomic variables (ACS)", 1, "scenario-2018-acs.csv", 2018, "acs", True
        ),
    ],
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx": [
        _SheetConfig("Macroeconomic variables (Base) ", 1, "scenario-2019-base.csv", 2019, "base"),
        _SheetConfig(
            "Macroeconomic variables (ACS)", 1, "scenario-2019-acs.csv", 2019, "acs", True
        ),
    ],
    "variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.XLSX": [
        _SheetConfig(
            "Stress scenario - Rates Down ",
            1,
            "scenario-2019-non-participants-rates-down.csv",
            2019,
            "non-participants",
        ),
        _SheetConfig(
            "Stress scenario - Rates Up ",
            1,
            "scenario-2019-non-participants-rates-up.csv",
            2019,
            "non-participants",
        ),
    ],
    # 2021 Solvency Stress Test: a single severe macro scenario (one sheet), so
    # it is the modelled input. Header on row 2 and CRE already suffixed.
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2021-scenario.xlsx": [
        _SheetConfig(
            "Macroeconomic variables", 1, "scenario-2021-stress.csv", 2021, "stress", True
        ),
    ],
    # 2022/23 ACS. Header is on the first row (unlike 2015-2019's row 2), and
    # the CRE column already carries the "- aggregate" suffix, so no renames.
    "stress-testing-the-uk-banking-system-variable-paths-for-the-2022-scenarios.xlsx": [
        _SheetConfig("Macroeconomic variables (Base) ", 0, "scenario-2022-base.csv", 2022, "base"),
        _SheetConfig(
            "Macroeconomic variables(Stress)", 0, "scenario-2022-stress.csv", 2022, "stress", True
        ),
    ],
    # 2025 Bank Capital Stress Test: a single severe scenario (no separate base
    # sheet), so it is the modelled input for the year.
    "variable-paths-for-the-2025-bank-capital-stress-test.xlsx": [
        _SheetConfig(
            "Macroeconomic variables",
            1,
            "scenario-2025-stress.csv",
            2025,
            "stress",
            True,
            _RENAMES_2025,
        ),
    ],
}

# Quarter label used as the row-key in col A of every macro-variables sheet,
# e.g. "Q1 2000". Used both to identify data rows and to drop section
# dividers like "Historical data" / "Stress projection" / "Sources:".
_QUARTER_RE = re.compile(r"^Q[1-4]\s+\d{4}$")

# Divider row that BoE puts between historical and projection quarters.
# 2015-2019 workbooks say "Projections"; the 2014 workbook says "Stress
# scenario". Match either, case- and whitespace-tolerant.
_DIVIDER_RE = re.compile(r"^\s*(projections?|stress\s+(scenario|projection))\s*$", re.I)


@dataclass
class ExtractReport:
    csv_paths: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)


def clean_scenario_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy a raw scenario DataFrame freshly read from a BoE workbook sheet.

    - Rename the (typically unnamed) first column to ``quarter``.
    - Keep only rows whose ``quarter`` matches the ``Qx YYYY`` pattern,
      dropping section divider rows ("Historical data", "Projections")
      and any trailing notes.
    - Drop columns that are entirely empty (BoE workbooks use blank columns
      as visual section separators).
    - Add a ``period_kind`` column with values ``"history"`` /
      ``"year_zero"`` / ``"projection"``, derived from the position of the
      "Projections" (or "Stress scenario") divider row. ``year_zero`` is the
      last historical quarter — i.e. T0, the denominator the legacy R code
      used for low-point shock features. If no divider is detected,
      ``period_kind`` is ``pd.NA`` for every row.
    """
    out = df.copy()
    first_col = cast(Hashable, out.columns[0])
    out = out.rename(columns={first_col: "quarter"})
    quarter_strings = out["quarter"].astype(str)

    is_quarter = quarter_strings.str.match(_QUARTER_RE)
    is_divider = quarter_strings.apply(lambda s: isinstance(s, str) and bool(_DIVIDER_RE.match(s)))
    divider_positions = is_divider.loc[is_divider].index
    divider_pos = int(divider_positions[0]) if len(divider_positions) else None

    out = out.loc[is_quarter].copy()
    out = out.dropna(axis=1, how="all")

    if divider_pos is not None:
        # Use original (pre-filter) row indices to compare against divider position.
        kinds = ["history" if int(i) < divider_pos else "projection" for i in out.index]
        # The last "history" row is T0 / year_zero.
        last_history = next(
            (i for i in range(len(kinds) - 1, -1, -1) if kinds[i] == "history"),
            None,
        )
        if last_history is not None:
            kinds[last_history] = "year_zero"
        out["period_kind"] = kinds
    else:
        out["period_kind"] = pd.NA

    out = out.reset_index(drop=True)
    return out


def add_uk_nominal_gdp_index(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``UK nominal GDP index`` column rebased so year_zero == 100.

    Mirrors the legacy R ``st_build_scenarios`` step that derived
    ``uk_nominal_gdp_index = uk_nominal_gdp / first(uk_nominal_gdp) * 100``
    so the rebased series could be fed to the cross-year regression. Doing
    this in the ingest layer means every scenario CSV self-describes its
    rebased index, instead of every analytical consumer having to repeat
    the derivation.

    No-ops (returns ``df`` unchanged) when the source column ``UK nominal
    GDP`` is absent or no ``year_zero`` row is marked.
    """
    if "UK nominal GDP" not in df.columns or "period_kind" not in df.columns:
        return df
    yz_rows = df.loc[df["period_kind"] == "year_zero", "UK nominal GDP"]
    if yz_rows.empty:
        return df
    yz_value = yz_rows.iloc[0]
    out = df.copy()
    out["UK nominal GDP index"] = out["UK nominal GDP"] / yz_value * 100
    return out


def scenario_records() -> list[ScenarioRecord]:
    """Flatten ``_CONFIGS`` into manifest records (one per scenario CSV)."""
    return [
        ScenarioRecord(s.acsyear, s.role, s.out_name, s.model_input)
        for sheets in _CONFIGS.values()
        for s in sheets
    ]


def write_scenario_manifest(out_dir: Path) -> Path:
    """Write the scenario manifest declaring the canonical modelled scenario per year.

    Only scenarios whose CSV is actually present in ``out_dir`` are recorded, so
    the manifest never points downstream at a file a skipped/missing workbook
    didn't produce.
    """
    present = [r for r in scenario_records() if (out_dir / r.path).exists()]
    return scenario_index.write(present, out_dir)


def extract_scenario(xlsx_path: Path, out_dir: Path) -> list[Path]:
    """Extract every configured scenario sheet from ``xlsx_path`` to CSV.

    Raises ``KeyError`` if the workbook isn't registered in ``_CONFIGS``.
    """
    config = _CONFIGS.get(xlsx_path.name)
    if config is None:
        raise KeyError(f"No scenario config registered for {xlsx_path.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for sheet in config:
        df = pd.read_excel(xlsx_path, sheet_name=sheet.sheet_name, header=sheet.header_row)
        cleaned = clean_scenario_frame(df)
        if sheet.column_renames:
            cleaned = cleaned.rename(columns=sheet.column_renames)
        cleaned = add_uk_nominal_gdp_index(cleaned)
        out_path = out_dir / sheet.out_name
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
    manifest_path = write_scenario_manifest(out_dir)
    print(f"Wrote scenario manifest -> {manifest_path.name}")
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
