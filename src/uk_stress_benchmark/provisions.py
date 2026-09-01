"""Loaders for the static per-firm modelling attributes.

Two committed CSVs carry the firm-level numbers the regression needs, each
from its own disclosure source (see ``SOURCES.md``):

* ``processed_inputs/firm_provisions.csv`` — pre-stress provision coverage
  by product, produced by ``scripts/derive_firm_provisions.py`` from a
  hand-compiled Pillar 3 summary.
* ``processed_inputs/firm_btl.csv`` — buy-to-let share of each firm's
  mortgage book, transcribed by hand from firms' annual reports / Pillar 3
  disclosures. A single figure per firm, applied to every stress-test year.

Neither loader transforms the data — they earn their place by validating
it: required columns must be present, and (optionally) every firm named in
the CSV must be in a caller-supplied known set, catching silent firm-naming
drift between the results and the attribute files.

Public surface:
    load_provisions(path, *, valid_firms=None) -> pd.DataFrame
    load_btl(path, *, valid_firms=None) -> pd.DataFrame
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_PROVISION_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "mort_prov_coverage",
    "retail_prov_coverage",
    "commercial_prov_coverage",
)

_PROVISION_PANEL_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "acsyear",
    "mort_prov_coverage",
    "retail_prov_coverage",
    "commercial_prov_coverage",
)

_BTL_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "btl_share",
)


def _load_firm_attributes(
    path: Path | str,
    required_columns: tuple[str, ...],
    valid_firms: set[str] | None,
) -> pd.DataFrame:
    """Read a per-firm attribute CSV and validate it.

    Checks that ``required_columns`` are all present and, when
    ``valid_firms`` is supplied, that every ``firm_name`` is known. Returns
    the frame projected to exactly ``required_columns`` (in that order), so
    downstream merges see a predictable shape regardless of extra columns
    the CSV might carry.
    """
    df = pd.read_csv(path)

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"{Path(path).name} missing required column(s): {missing}; got {list(df.columns)}"
        )

    if valid_firms is not None:
        unknown = sorted(set(df["firm_name"]) - valid_firms)
        if unknown:
            raise ValueError(f"{Path(path).name} contains firms not in valid_firms: {unknown}")

    return df.loc[:, list(required_columns)]


def load_provisions(
    path: Path | str,
    *,
    valid_firms: set[str] | None = None,
) -> pd.DataFrame:
    """Load the firm provision-coverage CSV.

    Parameters
    ----------
    path : Path | str
        Location of the CSV (typically ``processed_inputs/firm_provisions.csv``).
    valid_firms : set[str] | None, default ``None``
        If provided, every ``firm_name`` value in the CSV must be in this
        set; otherwise a ``ValueError`` is raised listing the unknown
        firms. Useful for catching divergence between the firm vocabulary
        in ``firm_results.csv`` and ``firm_provisions.csv``.

    Returns
    -------
    pd.DataFrame
        If the CSV has no ``acsyear`` column: one row per firm, with the
        four canonical columns (``firm_name`` plus the three
        ``*_prov_coverage`` columns) — a single static figure broadcast
        across every stress-test year. If the CSV does carry ``acsyear``:
        one row per (firm, acsyear), with those five columns in order and
        ``acsyear`` as an integer dtype, giving each firm-year its own
        coverage figure. Missing coverage values come back as NaN either
        way.

    Raises
    ------
    ValueError
        If the CSV is missing any of the required columns, if
        ``valid_firms`` is provided and the CSV contains a firm not in it,
        or (panel shape only) if the same (firm_name, acsyear) pair
        appears more than once.
    """
    has_year = "acsyear" in pd.read_csv(path, nrows=0).columns
    if not has_year:
        return _load_firm_attributes(path, _PROVISION_COLUMNS, valid_firms)

    df = _load_firm_attributes(path, _PROVISION_PANEL_COLUMNS, valid_firms)
    df["acsyear"] = df["acsyear"].astype(int)

    dupes = df.loc[df.duplicated(subset=["firm_name", "acsyear"], keep=False)]
    if not dupes.empty:
        pairs = sorted(set(zip(dupes["firm_name"], dupes["acsyear"], strict=True)))
        raise ValueError(f"{Path(path).name} has duplicate (firm_name, acsyear) rows: {pairs}")

    return df


def load_btl(
    path: Path | str,
    *,
    valid_firms: set[str] | None = None,
) -> pd.DataFrame:
    """Load the firm buy-to-let-share CSV.

    Parameters
    ----------
    path : Path | str
        Location of the CSV (typically ``processed_inputs/firm_btl.csv``).
    valid_firms : set[str] | None, default ``None``
        If provided, every ``firm_name`` value in the CSV must be in this
        set; otherwise a ``ValueError`` is raised listing the unknown firms.

    Returns
    -------
    pd.DataFrame
        Rows per firm, with ``firm_name`` and ``btl_share`` (buy-to-let
        balances as a fraction of the firm's mortgage book, e.g. ``0.15``
        for 15%). Missing shares come back as NaN.

    Raises
    ------
    ValueError
        If the CSV is missing any of the required columns, or if
        ``valid_firms`` is provided and the CSV contains a firm not in it.
    """
    return _load_firm_attributes(path, _BTL_COLUMNS, valid_firms)
