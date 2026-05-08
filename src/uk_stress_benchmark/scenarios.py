"""Low-point-shock feature engineering for BoE ACS economic scenarios.

For a single scenario, the feature is the percentage fall (or rise) of each
economic variable relative to the year_zero quarter, taken at the worst
point across the projection horizon. These shocks are the inputs to the
per-product impairment-charge regressions.

Public surface:
    compute_low_point_shocks(df, *, variables) -> pd.Series
    build_low_point_shocks(paths, *, variables) -> pd.DataFrame
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Variables that aren't published directly by BoE but are derived in this
# module by rebasing a published series so year_zero == 100. Mathematically
# their pct_fall / pct_rise equal those of the source column; the alias
# exists so the legacy R feature set can be reproduced verbatim.
_DERIVED_INDICES: dict[str, str] = {
    "UK nominal GDP index": "UK nominal GDP",
}

# Input aliases: map a canonical analysis name to the actual CSV column.
# The BoE workbooks publish "Bank Rate" without the UK prefix, but the
# legacy R analysis named the feature uk_bank_rate. Accepting the
# UK-prefixed name keeps the output slugs consistent.
_INPUT_ALIASES: dict[str, str] = {
    "UK Bank Rate": "Bank Rate",
}


def _snake_case(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return s


def compute_low_point_shocks(
    df: pd.DataFrame, *, variables: list[str]
) -> pd.Series:
    """Compute per-variable pct_fall and pct_rise for one scenario.

    Parameters
    ----------
    df : pd.DataFrame
        Tidy scenario frame with a ``period_kind`` column. Must contain
        exactly one ``year_zero`` row plus zero-or-more ``projection`` rows.
        ``history`` rows are ignored.
    variables : list[str]
        Column names (in canonical BoE casing, e.g. ``"UK nominal GDP"``) to
        compute shocks for. May include the derived alias
        ``"UK nominal GDP index"`` even though it isn't a column in ``df``.

    Returns
    -------
    pd.Series
        Indexed by ``{snake_var}_pct_fall`` and ``{snake_var}_pct_rise`` for
        each variable. Values are signed: pct_fall is <= 0, pct_rise is >= 0.
    """
    df = df.copy()
    yz_mask = df["period_kind"] == "year_zero"

    for derived, source in _DERIVED_INDICES.items():
        if derived in variables and source in df.columns:
            yz_source = df.loc[yz_mask, source].iloc[0]
            df[derived] = df[source] / yz_source * 100

    relevant = df[df["period_kind"].isin(["year_zero", "projection"])]
    year_zero = df.loc[yz_mask].iloc[0]

    shocks: dict[str, float] = {}
    for var in variables:
        column = _INPUT_ALIASES.get(var, var)
        slug = _snake_case(var)
        if column not in df.columns:
            # 2014's BoE workbook lacks some variables (e.g. corporate
            # profits). Emit NaN rather than crashing so build_low_point_shocks
            # can still produce a row for the missing year.
            shocks[f"{slug}_pct_fall"] = float("nan")
            shocks[f"{slug}_pct_rise"] = float("nan")
            continue
        denom = year_zero[column]
        pct_change = relevant[column] / denom - 1
        shocks[f"{slug}_pct_fall"] = pct_change.min()
        shocks[f"{slug}_pct_rise"] = pct_change.max()
    return pd.Series(shocks)


def build_low_point_shocks(
    paths: dict[int, Path | str], *, variables: list[str]
) -> pd.DataFrame:
    """Compute low-point shocks for many scenarios and stack into one frame.

    Parameters
    ----------
    paths : dict[int, Path | str]
        ``{acsyear: csv_path}`` — one tidy scenario CSV per acsyear, each
        already carrying the ``period_kind`` column produced by
        :mod:`uk_stress_benchmark.extract_scenarios`.
    variables : list[str]
        Variable names passed through to :func:`compute_low_point_shocks`.

    Returns
    -------
    pd.DataFrame
        Indexed by ``acsyear`` (sorted), with one column per
        ``{slug}_pct_fall`` / ``{slug}_pct_rise``.
    """
    rows: dict[int, pd.Series] = {}
    for acsyear, path in paths.items():
        df = pd.read_csv(path)
        rows[acsyear] = compute_low_point_shocks(df, variables=variables)
    out = pd.DataFrame(rows).T.sort_index()
    out.index.name = "acsyear"
    return out
