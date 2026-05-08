"""Tidy loader for ``processed_inputs/firm_results.csv``.

The CSV is produced by :mod:`uk_stress_benchmark.aggregate_firm_results` and
holds one row per firm × ACS year, with both 3-year and 5-year impairment-
charge percentages per product (where BoE published them). This module hides
the small but meaningful "impute 5yr from 3yr" rule that the legacy R
``st_build_results(imputeMissing=TRUE)`` applied: BoE's 2014 stress test
only published 3-year rates, and the legacy modelling code treats those as
proxies for 5-year rates so 2014 rows can join the cross-year regression.

Public surface:
    load_results(path, *, impute_missing=True) -> pd.DataFrame
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Products where 5-year rates can be imputed from 3-year rates when the
# 5-year value is missing. Business lending was not split out separately
# until 2015, so it has no 3-year column to fall back on.
_IMPUTABLE_PRODUCTS: tuple[str, ...] = ("mort", "retail", "cre")


def load_results(
    path: Path | str,
    *,
    impute_missing: bool = True,
) -> pd.DataFrame:
    """Load the tidy firm-results CSV.

    Parameters
    ----------
    path : Path | str
        Location of the CSV (typically ``processed_inputs/firm_results.csv``).
    impute_missing : bool, default ``True``
        When ``True``, fill missing 5-year impairment-charge percentages
        for mortgage / retail / CRE products from the corresponding 3-year
        values on the same row. Mirrors the legacy R ``st_build_results``
        behaviour — needed so the 2014 cohort (3-year-only data) can
        contribute to a cross-year 5-year-rate regression. ``uk_bus_5yr_ic_pct``
        has no 3-year analogue and is never imputed.

    Returns
    -------
    pd.DataFrame
        One row per ``(firm_name, acsyear)``, with ``acsyear`` as ``int64``
        and value columns as ``float64`` (NaN for missing).
    """
    df = pd.read_csv(path)
    df["acsyear"] = df["acsyear"].astype("int64")

    if impute_missing:
        for product in _IMPUTABLE_PRODUCTS:
            five_yr = f"uk_{product}_5yr_ic_pct"
            three_yr = f"uk_{product}_3yr_ic_pct"
            if three_yr in df.columns and five_yr in df.columns:
                df[five_yr] = df[five_yr].fillna(df[three_yr])

    return df
