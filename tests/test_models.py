"""Tests for the modeling primitives — dummy expansion, LM fitting, prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from uk_stress_benchmark.models import (
    add_dummies,
    fit_linear_model,
    predict_with_model,
)


def test_add_dummies_creates_one_hot_columns_with_snake_case_suffixes():
    df = pd.DataFrame({"firm_name": ["Barclays", "HSBC", "Santander UK"]})
    out = add_dummies(df, "firm_name")
    assert "firm_name_barclays" in out.columns
    assert "firm_name_hsbc" in out.columns
    assert "firm_name_santander_uk" in out.columns


def test_add_dummies_preserves_original_column_and_other_columns():
    df = pd.DataFrame({"firm_name": ["Barclays", "HSBC"], "value": [1.0, 2.0]})
    out = add_dummies(df, "firm_name")
    assert "firm_name" in out.columns
    assert list(out["firm_name"]) == ["Barclays", "HSBC"]
    assert list(out["value"]) == [1.0, 2.0]


def test_add_dummies_marks_correct_row_for_each_category():
    df = pd.DataFrame({"firm_name": ["Barclays", "HSBC", "Barclays"]})
    out = add_dummies(df, "firm_name")
    assert list(out["firm_name_barclays"]) == [True, False, True]
    assert list(out["firm_name_hsbc"]) == [False, True, False]


def test_fit_linear_model_recovers_known_coefficients():
    # y = 1 + 2*x exactly, no noise. OLS should recover intercept ~ 1,
    # coefficient on x ~ 2.
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, size=50)
    df = pd.DataFrame({"x": x, "y": 1 + 2 * x})
    model = fit_linear_model(df, dependent_var="y", independent_vars=["x"])
    assert model.params["const"] == pytest.approx(1.0, abs=1e-9)
    assert model.params["x"] == pytest.approx(2.0, abs=1e-9)


def test_fit_linear_model_with_include_all_firms_picks_up_firm_dummies():
    rng = np.random.default_rng(0)
    n = 60
    df = pd.DataFrame(
        {
            "x": rng.uniform(0, 1, size=n),
            "firm_name_barclays": rng.integers(0, 2, size=n).astype(bool),
            "firm_name_hsbc": rng.integers(0, 2, size=n).astype(bool),
            "noise": rng.normal(size=n),
            "y": rng.normal(size=n),
        }
    )
    model = fit_linear_model(
        df,
        dependent_var="y",
        independent_vars=["x"],
        include_all_firms=True,
    )
    # firm_name_* columns should be in the fit; "noise" should not.
    assert "firm_name_barclays" in model.params.index
    assert "firm_name_hsbc" in model.params.index
    assert "noise" not in model.params.index
    assert "x" in model.params.index


def test_fit_linear_model_stepwise_drops_pure_noise_predictor():
    # y depends only on x. A second predictor "noise" is pure random noise
    # uncorrelated with y. Backward stepwise by AIC should drop "noise".
    rng = np.random.default_rng(123)
    n = 200
    x = rng.uniform(0, 10, size=n)
    df = pd.DataFrame(
        {
            "x": x,
            "noise": rng.normal(size=n),
            "y": 1 + 2 * x + rng.normal(scale=0.1, size=n),
        }
    )
    full = fit_linear_model(df, dependent_var="y", independent_vars=["x", "noise"], stepwise=False)
    stepped = fit_linear_model(
        df, dependent_var="y", independent_vars=["x", "noise"], stepwise=True
    )
    # Full model has both predictors; stepped has dropped noise.
    assert "noise" in full.params.index
    assert "noise" not in stepped.params.index
    assert "x" in stepped.params.index


def test_predict_with_model_returns_fitted_values_on_training_data():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    df = pd.DataFrame({"x": x, "y": 1 + 2 * x})
    model = fit_linear_model(df, dependent_var="y", independent_vars=["x"])
    scored = predict_with_model(df, model)
    assert "prediction" in scored.columns
    np.testing.assert_allclose(scored["prediction"], df["y"], atol=1e-9)


def test_predict_with_model_attaches_actual_column_when_requested():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [3.0, 5.0, 7.0]})
    model = fit_linear_model(df, dependent_var="y", independent_vars=["x"])
    scored = predict_with_model(df, model, actual_col="y")
    assert "actual" in scored.columns
    assert list(scored["actual"]) == [3.0, 5.0, 7.0]


def test_predict_with_model_uses_only_columns_the_model_kept():
    # After stepwise drops "noise", predict_with_model should not require
    # "noise" to be present in the scoring frame.
    rng = np.random.default_rng(7)
    n = 100
    x = rng.uniform(0, 10, size=n)
    fit_df = pd.DataFrame(
        {
            "x": x,
            "noise": rng.normal(size=n),
            "y": 1 + 2 * x + rng.normal(scale=0.05, size=n),
        }
    )
    model = fit_linear_model(
        fit_df, dependent_var="y", independent_vars=["x", "noise"], stepwise=True
    )

    score_df = pd.DataFrame({"x": [0.0, 5.0, 10.0]})  # no "noise" column
    scored = predict_with_model(score_df, model)
    assert "prediction" in scored.columns
    assert scored["prediction"].notna().all()
