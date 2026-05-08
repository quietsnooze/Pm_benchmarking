"""Tidy loader for ``processed_inputs/firm_provisions.csv``.

The CSV is produced by ``scripts/derive_firm_provisions.py`` (one-off
transcription of a hand-compiled Pillar 3 summary; see ``SOURCES.md``). This
loader doesn't transform the data — it earns its module by doing two
defensive checks: required columns are present, and (optionally) every firm
named in the CSV is in a caller-supplied known set, catching silent firm-
naming drift between ``firm_results.csv`` and ``firm_provisions.csv``.

Public surface:
    load_provisions(path, *, valid_firms=None) -> pd.DataFrame
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_REQUIRED_COLUMNS: tuple[str, ...] = (
    "firm_name",
    "mort_prov_coverage",
    "retail_prov_coverage",
    "commercial_prov_coverage",
)


def load_provisions(
    path: Path | str,
    *,
    valid_firms: set[str] | None = None,
) -> pd.DataFrame:
    """Load the firm-provisions CSV.

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
        Rows per firm, with all four canonical columns
        (``firm_name`` plus the three ``*_prov_coverage`` columns).
        Missing coverage values come back as NaN.

    Raises
    ------
    ValueError
        If the CSV is missing any of the required columns, or if
        ``valid_firms`` is provided and the CSV contains a firm not in it.
    """
    df = pd.read_csv(path)

    missing = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"firm_provisions CSV missing required column(s): {missing}; "
            f"got {list(df.columns)}"
        )

    if valid_firms is not None:
        unknown = sorted(set(df["firm_name"]) - valid_firms)
        if unknown:
            raise ValueError(
                f"firm_provisions contains firms not in valid_firms: {unknown}"
            )

    return df[list(_REQUIRED_COLUMNS)]
