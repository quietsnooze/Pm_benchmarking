"""The scenario manifest — the contract between scenario ingest and analysis.

The ingest layer publishes one tidy CSV per scenario sheet
(``scenario-{year}-{kind}.csv``), but *which* of those is the canonical
stressed scenario to feed the per-product regression is a per-year judgement
(2014-2016 publish a single "stress" scenario; 2017+ use "acs"; base / BES /
non-participant scenarios are never modelled). Historically that judgement was
re-encoded by every consumer as a hard-coded ``year -> kind`` map.

This module makes ingest record it **once**, in ``processed_inputs/scenarios.csv``,
and hands analysis code a year-agnostic lookup. Adding a new stress-test year
becomes a pure ingest-config change: downstream code never branches on year.

Public surface:
    ScenarioRecord                       (one manifest row)
    write(records, processed_dir)        -> Path        (ingest writes the manifest)
    modelling_paths(processed_dir)       -> dict[int, Path]   (analysis reads it)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

MANIFEST_NAME = "scenarios.csv"
_COLUMNS = ("acsyear", "role", "model_input", "path")


@dataclass(frozen=True)
class ScenarioRecord:
    """One extracted scenario CSV and its role in the analysis.

    Attributes
    ----------
    acsyear : int
        The stress-test year the scenario belongs to.
    role : str
        Scenario flavour as published, e.g. ``"stress"`` / ``"base"`` /
        ``"acs"`` / ``"bes"`` / ``"non-participants"``.
    path : str
        The CSV filename, relative to ``processed_inputs/``.
    model_input : bool
        Whether this is *the* canonical stressed scenario fed to the
        per-product regression for ``acsyear``. Exactly one record per year
        should set this true.
    """

    acsyear: int
    role: str
    path: str
    model_input: bool


def write(records: Iterable[ScenarioRecord], processed_dir: Path) -> Path:
    """Write the scenario manifest to ``processed_dir/scenarios.csv``."""
    frame = pd.DataFrame(
        [
            {"acsyear": r.acsyear, "role": r.role, "model_input": r.model_input, "path": r.path}
            for r in records
        ],
        columns=list(_COLUMNS),
    ).sort_values(["acsyear", "role"])
    out_path = processed_dir / MANIFEST_NAME
    frame.to_csv(out_path, index=False)
    return out_path


def modelling_paths(processed_dir: Path) -> dict[int, Path]:
    """Return ``{acsyear: scenario_csv_path}`` for the canonical modelled scenarios.

    Reads the manifest written by :func:`write` and returns, for each year,
    the absolute path to the single scenario CSV flagged ``model_input``.
    Raises if a year flags more than one — the manifest must name exactly one
    modelling scenario per year.
    """
    frame = pd.read_csv(processed_dir / MANIFEST_NAME)
    chosen = frame.loc[frame["model_input"].astype(bool)]

    paths: dict[int, Path] = {}
    for row in chosen.itertuples(index=False):
        year = int(row.acsyear)
        if year in paths:
            raise ValueError(f"scenario manifest names more than one modelling scenario for {year}")
        paths[year] = processed_dir / str(row.path)
    return paths
