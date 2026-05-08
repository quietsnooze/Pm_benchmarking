"""Tests for the LM-based NaN imputation helper."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from uk_stress_benchmark.imputation import impute_missing_var


def test_imputes_nan_target_using_single_predictor():
    # target y = 2*x for the observed rows; the one NaN row at x=10 should
    # be filled with the model's prediction (=20).
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 10.0], "y": [2.0, 4.0, 6.0, np.nan]})
    out = impute_missing_var(df, missing_var="y", based_on_vars=["x"])
    assert out.loc[3, "y"] == pytest.approx(20.0)


def test_does_not_overwrite_observed_values():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 10.0], "y": [2.0, 4.0, 6.0, np.nan]})
    out = impute_missing_var(df, missing_var="y", based_on_vars=["x"])
    # Observed values must be preserved exactly, not refit through the LM.
    assert list(out.loc[:2, "y"]) == [2.0, 4.0, 6.0]


def test_preserves_frame_shape_and_other_columns():
    df = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 10.0],
            "y": [2.0, 4.0, 6.0, np.nan],
            "label": ["a", "b", "c", "d"],
        }
    )
    out = impute_missing_var(df, missing_var="y", based_on_vars=["x"])
    assert out.shape == df.shape
    assert list(out.columns) == ["x", "y", "label"]
    assert list(out["label"]) == ["a", "b", "c", "d"]


def test_imputation_with_multiple_predictors():
    # target y = 2*x + 3*z, exact fit, with x and z linearly independent.
    # Imputed value at (x=10, z=5) should be 2*10 + 3*5 = 35.
    df = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 10.0],
            "z": [0.0, 1.0, 5.0, 7.0, 5.0],
            "y": [2.0, 7.0, 21.0, 29.0, np.nan],
        }
    )
    out = impute_missing_var(df, missing_var="y", based_on_vars=["x", "z"])
    assert out.loc[4, "y"] == pytest.approx(35.0)
