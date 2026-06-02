"""Streamlit app — UK bank stress-test impairment-charge benchmarking.

Single-page app that loads the processed BoE ACS scenario data, fits the
four product OLS models defined in :mod:`uk_stress_benchmark.pipeline`,
and lets the user explore both the historical fits and a what-if
scenario where they pick the shock magnitudes themselves.

The actual library logic (loaders, feature engineering, modelling) is
exercised by the test suite — this file is the rendering / interaction
layer only and is exempt from tests per the project policy.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from uk_stress_benchmark import __version__
from uk_stress_benchmark.models import predict_with_model
from uk_stress_benchmark.pipeline import (
    RECIPES,
    build_modelling_dataset,
    fit_product_models,
    predict_for_scenario,
)
from uk_stress_benchmark.provisions import load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenarios import build_low_point_shocks
from uk_stress_benchmark.viz import actual_vs_expected_figure, predictions_heatmap

PROCESSED = Path(__file__).resolve().parent / "processed_inputs"

# Canonical 7-variable feature set fed to build_low_point_shocks. Same
# list the gold regression test pins.
_CANONICAL_VARS: list[str] = [
    "UK residential property price index",
    "UK commercial real estate price index - aggregate",
    "UK unemployment rate",
    "UK nominal GDP index",
    "UK nominal GDP",
    "UK corporate profits",
    "UK Bank Rate",
]

# Stress-scenario CSV file conventions: 2014-2016 published a single
# "stress" scenario; 2017-2019 use "acs" (annual cyclical scenario).
_SCENARIO_KIND: dict[int, str] = {
    2014: "stress",
    2015: "stress",
    2016: "stress",
    2017: "acs",
    2018: "acs",
    2019: "acs",
}

# What-if slider definitions. Each: (column-name, label, min, max, step).
# Bank-rate ranges are wide because the rate itself is small — even
# modest absolute moves come out as huge percentage changes.
_SHOCK_SLIDERS: list[tuple[str, str, float, float, float]] = [
    ("uk_residential_property_price_index_pct_fall", "UK house price fall", -0.50, 0.00, 0.01),
    (
        "uk_commercial_real_estate_price_index_aggregate_pct_fall",
        "UK CRE price fall",
        -0.60,
        0.00,
        0.01,
    ),
    ("uk_unemployment_rate_pct_rise", "UK unemployment rise", 0.00, 2.00, 0.05),
    ("uk_unemployment_rate_pct_fall", "UK unemployment fall", -0.20, 0.00, 0.01),
    ("uk_nominal_gdp_index_pct_fall", "UK nominal GDP fall", -0.15, 0.05, 0.005),
    ("uk_corporate_profits_pct_fall", "UK corporate profits fall", -0.30, 0.00, 0.01),
    ("uk_bank_rate_pct_rise", "Bank Rate rise (multiple)", 0.0, 20.0, 0.5),
    ("uk_bank_rate_pct_fall", "Bank Rate fall (multiple)", -1.0, 0.0, 0.05),
]


# ----------------------------- data plumbing -------------------------------


@st.cache_data(show_spinner="Loading firm results / provisions…")
def _load_firm_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        load_results(PROCESSED / "firm_results.csv"),
        load_provisions(PROCESSED / "firm_provisions.csv"),
    )


@st.cache_data(show_spinner="Computing low-point shocks…")
def _load_shocks() -> pd.DataFrame:
    paths = {y: PROCESSED / f"scenario-{y}-{kind}.csv" for y, kind in _SCENARIO_KIND.items()}
    return build_low_point_shocks(
        paths,
        variables=_CANONICAL_VARS,
        impute={"UK corporate profits": ["UK nominal GDP"]},
    )


@st.cache_resource(show_spinner="Fitting product models…")
def _fit_everything() -> tuple[pd.DataFrame, dict]:
    results, provisions = _load_firm_data()
    shocks = _load_shocks()
    modelling_df = build_modelling_dataset(results, shocks, provisions)
    fitted = fit_product_models(modelling_df)
    return modelling_df, fitted


def _per_product_dataset(modelling_df: pd.DataFrame, product: str) -> pd.DataFrame:
    """Apply a recipe's per-product exclude (e.g. CRE drops Nationwide)."""
    recipe = RECIPES[product]
    if not recipe.exclude_firms:
        return modelling_df
    excl = {f.lower() for f in recipe.exclude_firms}
    return modelling_df[~modelling_df["firm_name"].str.lower().isin(excl)]


# --------------------------------- page ------------------------------------

st.set_page_config(
    page_title="UK stress test benchmarking",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("UK stress test benchmarking")
st.caption(f"v{__version__}  ·  Bank of England ACS 2014–2019")

st.markdown(
    """
This app benchmarks UK banking-system impairment-charge outcomes against the
Bank of England's annual cyclical scenario (ACS) stress tests from 2014 to 2019.
For each lending product (mortgages, retail unsecured, commercial real estate,
business lending) it fits an OLS regression of the firm-level 5-year impairment-
charge percentage on the worst-point shocks observed in each scenario's
projection horizon, plus firm-specific provision-coverage levels.

The fitted models are then used to predict per-firm impairment under a
hypothetical scenario you set via the sliders in the **What-if explorer** below.
Every coefficient, R², and prediction is reproducible from the underlying
public BoE data — see the [GitHub repo](https://github.com/quietsnooze/Pm_benchmarking)
for the methodology and tests (current parity with the legacy R port is
exact to floating-point precision against a 2019-vintage gold reference).
"""
)

modelling_df, fitted_models = _fit_everything()
shocks_df = _load_shocks()

# --- Section 1: Data overview ----------------------------------------------

st.header("Data")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Firms", modelling_df["firm_name"].nunique())
c2.metric(
    "ACS years",
    f"{int(modelling_df['acsyear'].min())}–{int(modelling_df['acsyear'].max())}",
)
c3.metric("Observations", len(modelling_df))
c4.metric("Products modelled", len(fitted_models))

with st.expander("Modelling dataset", expanded=False):
    st.dataframe(
        modelling_df.drop(columns=[c for c in modelling_df.columns if c.startswith("firm_name_")]),
        width="stretch",
    )

with st.expander("Low-point shock features by ACS year", expanded=False):
    st.dataframe(shocks_df.style.format("{:.3f}"), width="stretch")


# --- Section 2: Fitted models ----------------------------------------------

st.header("Fitted models")

product_tabs = st.tabs([p.title() for p in fitted_models])
for tab, (product, model) in zip(product_tabs, fitted_models.items()):
    with tab:
        recipe = RECIPES[product]
        c1, c2 = st.columns(2)
        c1.metric("R²", f"{model.rsquared:.3f}")
        c2.metric("Observations", int(model.nobs))

        product_df = _per_product_dataset(modelling_df, product)
        scored = predict_with_model(product_df, model, actual_col=recipe.dependent_var)
        fig = actual_vs_expected_figure(
            scored, title=f"{product.title()} — actual vs. predicted impairment %"
        )
        st.plotly_chart(fig, width="stretch")

        with st.expander("Coefficient table", expanded=False):
            params = pd.DataFrame(
                {
                    "coefficient": model.params,
                    "std_err": model.bse,
                    "t": model.tvalues,
                    "p": model.pvalues,
                }
            )
            st.dataframe(params.style.format("{:.4f}"), width="stretch")

        with st.expander("statsmodels summary", expanded=False):
            st.text(str(model.summary()))


# --- Section 3: What-if explorer -------------------------------------------

st.header("What-if explorer")
st.write(
    "Pick a starting ACS year (sliders default to its observed shock values) "
    "and adjust the shocks to see predicted impairment charges per firm and "
    "per product. Bank Rate moves are expressed as a percentage change of "
    "the rate itself (so a 5x rise of a 0.5% rate means the rate goes to 3%)."
)

default_year = st.selectbox(
    "Start from ACS year",
    options=sorted(_SCENARIO_KIND.keys()),
    index=3,  # 2017 default
)
defaults_row = shocks_df.loc[default_year]

slider_cols = st.columns(2)
shock_values: dict[str, float] = {}
for i, (col, label, lo, hi, step) in enumerate(_SHOCK_SLIDERS):
    with slider_cols[i % 2]:
        default_val = float(defaults_row.get(col, 0.0)) if col in defaults_row.index else 0.0
        # Clip default into the slider's range so it never throws.
        default_val = max(lo, min(hi, default_val))
        shock_values[col] = st.slider(
            label, min_value=lo, max_value=hi, value=default_val, step=step, key=col
        )

firms_df = modelling_df.drop_duplicates("firm_name").reset_index(drop=True)
predictions = predict_for_scenario(fitted_models, shock_values, firms_df)

st.subheader(f"Predicted 5-year impairment charges (% of book), starting from {default_year}")
st.plotly_chart(
    predictions_heatmap(
        predictions,
        title=f"Predicted impairment charges per firm × product (vs. {default_year} ACS)",
    ),
    width="stretch",
)

with st.expander("Predictions (table)", expanded=False):
    st.dataframe(predictions.style.format("{:.2%}"), width="stretch")

st.caption(
    "Predictions can dip below zero where the OLS extrapolates beyond the calibration "
    "data — those are model artefacts, not viable forecasts."
)
