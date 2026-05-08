"""Tests for load_provisions — verifies behaviour through the public surface."""

from pathlib import Path

import pandas as pd
import pytest

from uk_stress_benchmark.provisions import load_provisions


def _write_csv(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_returns_canonical_columns_and_preserves_nan(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_provisions.csv",
        [
            {
                "firm_name": "Barclays",
                "mort_prov_coverage": 0.0028,
                "retail_prov_coverage": 0.081,
                "commercial_prov_coverage": 0.008,
            },
            {
                "firm_name": "Standard Chartered",
                "mort_prov_coverage": "",
                "retail_prov_coverage": "",
                "commercial_prov_coverage": 0.013517,
            },
        ],
    )

    df = load_provisions(csv)

    assert list(df.columns) == [
        "firm_name",
        "mort_prov_coverage",
        "retail_prov_coverage",
        "commercial_prov_coverage",
    ]
    sc = df.set_index("firm_name").loc["Standard Chartered"]
    assert pd.isna(sc["mort_prov_coverage"])
    assert pd.isna(sc["retail_prov_coverage"])
    assert sc["commercial_prov_coverage"] == pytest.approx(0.013517)


def test_raises_when_required_column_missing(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_provisions.csv",
        [
            {
                "firm_name": "Barclays",
                "mort_prov_coverage": 0.0028,
                # retail_prov_coverage intentionally missing
                "commercial_prov_coverage": 0.008,
            }
        ],
    )

    with pytest.raises(ValueError, match="retail_prov_coverage"):
        load_provisions(csv)


def test_validates_firms_against_known_set_when_provided(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_provisions.csv",
        [
            {
                "firm_name": "Barclays",
                "mort_prov_coverage": 0.0028,
                "retail_prov_coverage": 0.081,
                "commercial_prov_coverage": 0.008,
            },
            {
                "firm_name": "MysteryBank",
                "mort_prov_coverage": 0.001,
                "retail_prov_coverage": 0.02,
                "commercial_prov_coverage": 0.01,
            },
        ],
    )

    with pytest.raises(ValueError, match="MysteryBank"):
        load_provisions(csv, valid_firms={"Barclays", "HSBC"})


def test_no_validation_error_when_all_firms_known(tmp_path: Path):
    csv = _write_csv(
        tmp_path / "firm_provisions.csv",
        [
            {
                "firm_name": "Barclays",
                "mort_prov_coverage": 0.0028,
                "retail_prov_coverage": 0.081,
                "commercial_prov_coverage": 0.008,
            }
        ],
    )

    # Should not raise.
    df = load_provisions(csv, valid_firms={"Barclays", "HSBC"})
    assert len(df) == 1
