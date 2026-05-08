"""Low-point-shock feature engineering for BoE ACS economic scenarios.

For a single scenario, the feature is the percentage fall (or rise) of each
economic variable relative to the year_zero quarter, taken at the worst
point across the projection horizon. These shocks are the inputs to the
per-product impairment-charge regressions.

Public surface:
    compute_low_point_shocks(df, *, variables) -> pd.Series
    build_low_point_shocks(paths, *, variables, impute=None) -> pd.DataFrame
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from uk_stress_benchmark.imputation import impute_missing_var

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
        ``history`` rows are ignored. Derived columns such as
        ``UK nominal GDP index`` are expected to be already present —
        the ingest layer (:mod:`uk_stress_benchmark.extract_scenarios`)
        adds them.
    variables : list[str]
        Column names (in canonical BoE casing, e.g. ``"UK nominal GDP"``) to
        compute shocks for. Variables whose column is absent from ``df``
        come back as NaN rather than raising.

    Returns
    -------
    pd.Series
        Indexed by ``{snake_var}_pct_fall`` and ``{snake_var}_pct_rise`` for
        each variable. Values are signed: pct_fall is <= 0, pct_rise is >= 0.
    """
    relevant = df[df["period_kind"].isin(["year_zero", "projection"])]
    year_zero = df[df["period_kind"] == "year_zero"].iloc[0]

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
    paths: dict[int, Path | str],
    *,
    variables: list[str],
    impute: dict[str, list[str]] | None = None,
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
    impute : dict[str, list[str]] | None
        Optional ``{target_var: [predictor_vars]}`` describing imputations to
        apply to the stacked quarterly time-series before computing shocks.
        Mirrors the legacy R workflow's ``st_impute_missing_var`` step. Use
        e.g. ``{"UK corporate profits": ["UK nominal GDP"]}`` to fill 2014's
        missing corporate-profits column from nominal GDP.

    Returns
    -------
    pd.DataFrame
        Indexed by ``acsyear`` (sorted), with one column per
        ``{slug}_pct_fall`` / ``{slug}_pct_rise``.
    """
    # Stack all scenarios with an acsyear tag so imputation can fit one
    # cross-year LM (e.g. corporate profits ~ nominal GDP across 2015-2019)
    # and project the result onto rows where the target column is missing
    # (e.g. all of 2014).
    frames: list[pd.DataFrame] = []
    for acsyear, path in paths.items():
        df = pd.read_csv(path)
        df = df.assign(acsyear=acsyear)
        frames.append(df)
    stacked = pd.concat(frames, ignore_index=True)

    # Drop pre-T0 history rows before imputation. The legacy R's
    # st_build_scenarios kept only year_zero + projection rows in the
    # dataframe it fed to st_impute_missing_var, so the LM coefficients
    # come from forecast-horizon data only. Filtering here matches that.
    stacked = stacked[stacked["period_kind"].isin(["year_zero", "projection"])]

    if impute:
        for target, predictors in impute.items():
            if target not in stacked.columns:
                stacked[target] = pd.NA
            stacked = impute_missing_var(
                stacked, missing_var=target, based_on_vars=predictors
            )

    rows: dict[int, pd.Series] = {}
    for acsyear, group in stacked.groupby("acsyear"):
        rows[int(acsyear)] = compute_low_point_shocks(group, variables=variables)
    out = pd.DataFrame(rows).T.sort_index()
    out.index.name = "acsyear"
    return out
