"""Tests for the scenario manifest — the ingest→analysis contract that says,
per acsyear, which extracted scenario CSV is the canonical stressed scenario
fed to the regression. Decouples downstream code from per-year filename rules.
"""

from __future__ import annotations

import pytest
from uk_stress_benchmark.scenario_index import (
    ScenarioRecord,
    modelling_paths,
    write,
)


def _legacy_records() -> list[ScenarioRecord]:
    # A representative slice: 2017 publishes base / acs / bes but only the ACS
    # path is the modelling input; 2014 publishes a single stress scenario.
    return [
        ScenarioRecord(2014, "stress", "scenario-2014-stress.csv", model_input=True),
        ScenarioRecord(2017, "base", "scenario-2017-base.csv", model_input=False),
        ScenarioRecord(2017, "acs", "scenario-2017-acs.csv", model_input=True),
        ScenarioRecord(2017, "bes", "scenario-2017-bes.csv", model_input=False),
    ]


def test_modelling_paths_returns_only_model_inputs_keyed_by_year(tmp_path):
    write(_legacy_records(), tmp_path)
    paths = modelling_paths(tmp_path)
    # base / bes are excluded; one canonical path per year.
    assert set(paths) == {2014, 2017}
    assert paths[2014] == tmp_path / "scenario-2014-stress.csv"
    assert paths[2017] == tmp_path / "scenario-2017-acs.csv"


def test_modelling_paths_are_absolute_under_processed_dir(tmp_path):
    write(_legacy_records(), tmp_path)
    for p in modelling_paths(tmp_path).values():
        assert p.is_absolute()
        assert p.parent == tmp_path


def test_two_model_inputs_for_one_year_is_an_error(tmp_path):
    bad = [
        ScenarioRecord(2018, "acs", "scenario-2018-acs.csv", model_input=True),
        ScenarioRecord(2018, "base", "scenario-2018-base.csv", model_input=True),
    ]
    write(bad, tmp_path)
    with pytest.raises(ValueError, match="2018"):
        modelling_paths(tmp_path)
