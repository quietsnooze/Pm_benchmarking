"""Streamlit app — benchmark stressed loan losses against the UK banks.

Single-page app: pick a Bank of England ACS scenario (or adjust its
shocks), describe your own loan book with three provision-coverage
numbers, and read off where a firm like yours would sit among the UK
stress-test participants. The regression machinery that powers the
benchmark lives in :mod:`uk_stress_benchmark.pipeline` and stays out of
sight — a "How the benchmark is built" section at the foot of the page
holds the full detail for readers who want it.

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
    year_benchmark,
)
from uk_stress_benchmark.provisions import load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenario_index import modelling_paths
from uk_stress_benchmark.scenarios import build_low_point_shocks
from uk_stress_benchmark.viz import actual_vs_expected_figure, benchmark_strip_figure

PROCESSED = Path(__file__).resolve().parent / "processed_inputs"

YOUR_FIRM = "Your firm"

GITHUB_URL = "https://github.com/quietsnooze/Pm_benchmarking"
LINKEDIN_URL = "https://www.linkedin.com/in/pemcintyre/"

# Sentinel for the scenario picker's "design your own" entry.
_CUSTOM = "custom"

# Display names for the four modelled products, in reading order.
_PRODUCT_LABELS: dict[str, str] = {
    "mortgage": "Mortgages",
    "retail": "Retail unsecured",
    "cre": "Commercial real estate",
    "business": "Business lending",
}

# Short trading names for chart axes — the full legal names stay in the
# prose and tables.
_SHORT_FIRM_NAMES: dict[str, str] = {
    "Lloyds Banking Group": "Lloyds",
    "The Royal Bank of Scotland Group": "RBS",
}

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

# What-if slider definitions. Each: (column-name, label, min, max, step,
# as_pct). Percent sliders display whole percent points (the model wants
# fractions, converted on read). Bank-rate moves stay as multiples of the
# rate itself — the rate is small, so even modest absolute moves come out
# as huge percentage changes.
_SHOCK_SLIDERS: list[tuple[str, str, float, float, float, bool]] = [
    ("uk_residential_property_price_index_pct_fall", "House price fall", -50.0, 0.0, 1.0, True),
    (
        "uk_commercial_real_estate_price_index_aggregate_pct_fall",
        "Commercial real estate price fall",
        -60.0,
        0.0,
        1.0,
        True,
    ),
    ("uk_unemployment_rate_pct_rise", "Unemployment rate rise", 0.0, 200.0, 5.0, True),
    ("uk_unemployment_rate_pct_fall", "Unemployment rate fall", -20.0, 0.0, 1.0, True),
    ("uk_nominal_gdp_index_pct_fall", "Nominal GDP fall", -15.0, 5.0, 0.5, True),
    ("uk_corporate_profits_pct_fall", "Corporate profits fall", -30.0, 0.0, 1.0, True),
    ("uk_bank_rate_pct_rise", "Bank Rate rise (multiple)", 0.0, 20.0, 0.5, False),
    ("uk_bank_rate_pct_fall", "Bank Rate fall (multiple)", -1.0, 0.0, 0.05, False),
]

# The three firm-level inputs the benchmark needs: (coverage column,
# label, help text). Values are entered as % of book.
_COVERAGE_INPUTS: list[tuple[str, str, str]] = [
    (
        "mort_prov_coverage",
        "Mortgage provisions (% of book)",
        "Balance-sheet provisions held against the mortgage book, before stress.",
    ),
    (
        "retail_prov_coverage",
        "Retail unsecured provisions (% of book)",
        "Provisions held against credit cards and other unsecured retail lending.",
    ),
    (
        "commercial_prov_coverage",
        "Commercial provisions (% of book)",
        "Provisions held against commercial real estate and business lending.",
    ),
]

# Headline shocks shown as chips next to the scenario picker.
_CHIP_SHOCKS: list[tuple[str, str]] = [
    ("uk_residential_property_price_index_pct_fall", "House prices"),
    ("uk_commercial_real_estate_price_index_aggregate_pct_fall", "CRE prices"),
    ("uk_unemployment_rate_pct_rise", "Unemployment rate"),
    ("uk_nominal_gdp_index_pct_fall", "Nominal GDP"),
]

# ------------------------------ theming ------------------------------------

# Colour / type tokens mirrored in .streamlit/config.toml and viz.py.
# Gilt (#8F6B1E) is reserved for "your firm" — it appears in the chart
# marker and nowhere else, so gilt always means "you".
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@500;600&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap');

.block-container { max-width: 1100px; padding-top: 3rem; }

h1, h2, h3 {
    font-family: 'Spectral', Georgia, serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    color: #1C2A33;
}
h1 { font-size: 2.7rem !important; line-height: 1.12 !important; }

.eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #0E5E67;
    margin: 0 0 0.35rem 0;
}
.lede {
    font-size: 1.13rem;
    line-height: 1.55;
    color: #3D4A52;
    max-width: 46rem;
    margin: 0.4rem 0 0.2rem 0;
}
.byline { font-size: 0.88rem; color: #5C5648; margin-top: 0.9rem; }
.byline a { color: #0E5E67; text-decoration: none; border-bottom: 1px solid #CFCCC0; }

h2.step { margin-top: 2.6rem; }
h2.step .num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.05rem;
    color: #0E5E67;
    margin-right: 0.75rem;
}

.chips { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.3rem 0 0.6rem 0; }
.chip {
    background: #F0EEE7;
    border: 1px solid #E2DFD4;
    border-radius: 6px;
    padding: 0.32rem 0.62rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #1C2A33;
    white-space: nowrap;
}
.chip .lbl { color: #5C5648; margin-right: 0.45rem; font-family: 'Source Sans 3', sans-serif; }

.footer {
    margin-top: 3.5rem;
    padding-top: 1.1rem;
    border-top: 1px solid #E2DFD4;
    font-size: 0.85rem;
    color: #5C5648;
}
.footer a { color: #0E5E67; text-decoration: none; border-bottom: 1px solid #CFCCC0; }
</style>
"""


def _step_header(number: int, title: str) -> None:
    st.markdown(
        f'<h2 class="step"><span class="num">{number}</span>{title}</h2>',
        unsafe_allow_html=True,
    )


# ----------------------------- data plumbing -------------------------------


@st.cache_data(show_spinner="Loading firm results / provisions…")
def _load_firm_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        load_results(PROCESSED / "firm_results.csv"),
        load_provisions(PROCESSED / "firm_provisions.csv"),
    )


@st.cache_data(show_spinner="Computing low-point shocks…")
def _load_shocks() -> pd.DataFrame:
    return build_low_point_shocks(
        modelling_paths(PROCESSED),
        variables=_CANONICAL_VARS,
        impute={"UK corporate profits": ["UK nominal GDP"]},
    )


@st.cache_resource(show_spinner="Calibrating the benchmark…")
def _fit_everything() -> tuple[pd.DataFrame, dict]:
    results, provisions = _load_firm_data()
    shocks = _load_shocks()
    modelling_df = build_modelling_dataset(results, shocks, provisions)
    fitted = fit_product_models(modelling_df)
    return modelling_df, fitted


@st.cache_resource(show_spinner="Calibrating on recent stress tests…")
def _fit_recent_models() -> tuple[list[int], dict]:
    """Alternative calibration: only the three most recent stress tests."""
    mdf, _ = _fit_everything()
    years = sorted(int(y) for y in pd.Series(mdf["acsyear"]).unique())[-3:]
    recent = mdf.loc[pd.Series(mdf["acsyear"]).isin(years)]
    return years, fit_product_models(recent)


@st.cache_data
def _published_years() -> list[int]:
    """Years with genuinely published 5-year outcomes.

    Loaded without the 5yr-from-3yr imputation the modelling dataset
    uses, so a year whose "outcomes" are imputed (2014) is never offered
    as a published benchmark.
    """
    raw = load_results(PROCESSED / "firm_results.csv", impute_missing=False)
    dep_cols = [r.dependent_var for r in RECIPES.values()]
    mask = raw[dep_cols].notna().any(axis=1)
    return sorted(int(y) for y in raw.loc[mask, "acsyear"].unique())


def _per_product_dataset(modelling_df: pd.DataFrame, product: str) -> pd.DataFrame:
    """Apply a recipe's per-product exclude (e.g. CRE drops Nationwide)."""
    recipe = RECIPES[product]
    if not recipe.exclude_firms:
        return modelling_df
    excl = {f.lower() for f in recipe.exclude_firms}
    mask = ~modelling_df["firm_name"].str.lower().isin(excl)
    return modelling_df.loc[mask]


def _with_your_firm(firms_df: pd.DataFrame, coverage: dict[str, float]) -> pd.DataFrame:
    """Append a synthetic "your firm" row: user coverages, no firm dummies."""
    row: dict[str, object] = {c: 0.0 for c in firms_df.columns if c.startswith("firm_name_")}
    row["firm_name"] = YOUR_FIRM
    row.update(coverage)
    return pd.concat([firms_df, pd.DataFrame([row])], ignore_index=True)


# --------------------------------- page ------------------------------------

st.set_page_config(
    page_title="UK stress-loss benchmark",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(_CSS, unsafe_allow_html=True)

modelling_df, fitted_models = _fit_everything()
shocks_df = _load_shocks()
acs_years = sorted(modelling_paths(PROCESSED))
peer_firms = sorted(modelling_df["firm_name"].unique())
_acsyears = pd.Series(modelling_df["acsyear"])
year_lo, year_hi = int(_acsyears.min()), int(_acsyears.max())

# --- Hero -------------------------------------------------------------------

st.markdown(
    f'<p class="eyebrow">UK bank stress testing · Bank of England scenarios '
    f"{year_lo}–{year_hi}</p>",
    unsafe_allow_html=True,
)
st.markdown("# Benchmark your stressed losses against the UK banks")
st.markdown(
    f"""<p class="lede">Set a stress scenario, describe your loan book in three
numbers, and see the five-year impairment charge a firm like yours would report
next to {", ".join(peer_firms[:-1])} and {peer_firms[-1]} — calibrated on every
firm-level result the Bank of England has published for its concurrent stress
tests, {year_lo} to {year_hi}.</p>
<p class="byline">Built by Peter McIntyre ·
<a href="{LINKEDIN_URL}">LinkedIn</a> ·
<a href="{GITHUB_URL}">Source &amp; methodology on GitHub</a></p>""",
    unsafe_allow_html=True,
)

# --- Step 1: scenario ---------------------------------------------------------

_step_header(1, "Set the scenario")

published_years = _published_years()
recent_years, recent_models = _fit_recent_models()


def _scenario_label(choice: object) -> str:
    if choice == _CUSTOM:
        return "Design your own scenario"
    return f"{choice} Bank of England stress test"


pick_col, side_col = st.columns([1, 2], vertical_alignment="bottom")
with pick_col:
    scenario_choice = st.selectbox(
        "Scenario",
        options=[*published_years, _CUSTOM],
        index=len(published_years) - 1,
        format_func=_scenario_label,
    )

is_custom = scenario_choice == _CUSTOM
calibration = "all"
shock_values: dict[str, float] = {}
scenario_year = int(st.session_state.get("_scenario_year", published_years[-1]))

if not is_custom:
    scenario_year = int(scenario_choice)
    # Remember the chosen year (and re-anchor the custom-mode sliders to
    # it), so "show me ACS 2022, then tweak it" works by switching modes.
    if st.session_state.get("_scenario_year") != scenario_year:
        st.session_state["_scenario_year"] = scenario_year
        for _slider_col, *_ in _SHOCK_SLIDERS:
            st.session_state.pop(_slider_col, None)

    year_row = shocks_df.loc[scenario_year]
    with side_col:
        chips = "".join(
            f'<span class="chip"><span class="lbl">{label}</span>{year_row[col]:+.0%}</span>'
            for col, label in _CHIP_SHOCKS
            if col in year_row.index and pd.notna(year_row[col])
        )
        st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)
    st.caption(
        "A published stress test's shocks are fixed — every firm faced the same "
        "scenario. Pick “Design your own scenario” to move the shocks yourself."
    )
else:
    with side_col:
        calibration = st.selectbox(
            "Calibration",
            options=["all", "recent"],
            format_func=lambda c: (
                f"Model calibrated on all stress tests ({year_lo}–{year_hi})"
                if c == "all"
                else "Model calibrated on the last three "
                f"({', '.join(str(y) for y in recent_years)})"
            ),
        )

    defaults_row = shocks_df.loc[scenario_year]
    with st.expander("Adjust the shocks", expanded=True):
        st.caption(
            f"Sliders start from the {scenario_year} stress test's shocks. Each "
            "shock is the worst point of the scenario's five-year path, as a "
            "change from the starting level. Bank Rate moves are multiples of "
            "the rate itself — a 5× rise of a 0.5% rate takes it to 3%."
        )
        slider_cols = st.columns(2)
        for i, (col, label, lo, hi, step, as_pct) in enumerate(_SHOCK_SLIDERS):
            with slider_cols[i % 2]:
                default_val = (
                    float(defaults_row.get(col, 0.0)) if col in defaults_row.index else 0.0
                )
                if as_pct:
                    default_val *= 100
                # Clip default into the slider's range so it never throws.
                default_val = max(lo, min(hi, default_val))
                if as_pct:
                    fmt = "%.1f%%" if step < 1 else "%.0f%%"
                else:
                    fmt = "×%.2f" if step < 0.5 else "×%.1f"
                shown = st.slider(
                    label,
                    min_value=lo,
                    max_value=hi,
                    value=default_val,
                    step=step,
                    format=fmt,
                    key=col,
                )
                shock_values[col] = shown / 100 if as_pct else shown

# --- Step 2: your firm --------------------------------------------------------

_step_header(2, "Describe your firm")
st.caption(
    "Provision coverage — provisions already held, as a share of each book — "
    "is the only firm-specific input the benchmark needs. Defaults are the "
    "peer medians."
)

firms_df = modelling_df.drop_duplicates("firm_name").reset_index(drop=True)
coverage_inputs: dict[str, float] = {}
coverage_cols = st.columns(3)
for (cov_col, label, help_text), ui_col in zip(_COVERAGE_INPUTS, coverage_cols, strict=True):
    peer_median_pct = float(pd.Series(firms_df[cov_col]).median()) * 100
    with ui_col:
        entered = st.number_input(
            label,
            min_value=0.0,
            max_value=25.0,
            value=round(peer_median_pct, 2),
            step=0.05,
            format="%.2f",
            help=help_text,
        )
    coverage_inputs[cov_col] = entered / 100

# --- Step 3: the benchmark ----------------------------------------------------

_step_header(3, "Read the benchmark")

if is_custom:
    models_in_use = fitted_models if calibration == "all" else recent_models
    scoring_df = _with_your_firm(firms_df, coverage_inputs)
    # A custom scenario has no test year of its own, so evaluate any time
    # trend the models kept "as of the latest published test". The trend is
    # a scenario-level scalar centred on the earliest year, so its latest
    # value is simply the maximum in the modelling data. Models where
    # stepwise dropped the trend ignore this key.
    year_shock = {"years_since_first_test": float(modelling_df["years_since_first_test"].max())}
    predictions = predict_for_scenario(models_in_use, {**shock_values, **year_shock}, scoring_df)
    _recent_list = ", ".join(str(y) for y in recent_years)
    calibration_note = (
        f"calibrated on every published stress test ({year_lo}–{year_hi})"
        if calibration == "all"
        else f"calibrated on the last three stress tests ({_recent_list})"
    )
    st.markdown(
        f"Predicted five-year impairment charge, as a percentage of each book, "
        f"under your custom scenario — {calibration_note}. "
        f"The gilt diamond is your firm."
    )
    scale_note = (
        "Note that each panel has its own scale — mortgage loss rates are an order of "
        "magnitude smaller than unsecured retail. Predictions can dip below zero "
        "where the scenario sits outside the calibration range; read those as "
        "'negligible', not as a forecast of write-backs."
    )
else:
    predictions = year_benchmark(modelling_df, scenario_year, coverage_inputs)
    st.markdown(
        f"Peer dots show the **actual published results** of the {scenario_year} "
        f"stress test — five-year impairment charge as a percentage of each book. "
        f"Your firm (the gilt diamond) is placed on that year's peer cross-section "
        f"using your provision coverage."
    )
    scale_note = (
        "Note that each panel has its own scale — mortgage loss rates are an order "
        "of magnitude smaller than unsecured retail. Peer values are as published; "
        "only your firm's marker is modelled. Where too few firms published a "
        "product that year, your firm's marker is omitted."
    )

predictions = predictions.rename(columns=_PRODUCT_LABELS)
_ordered = [c for c in _PRODUCT_LABELS.values() if c in predictions.columns]
predictions = predictions.loc[:, _ordered].dropna(axis=1, how="all")

st.plotly_chart(
    benchmark_strip_figure(predictions.rename(index=_SHORT_FIRM_NAMES), highlight=YOUR_FIRM),
    width="stretch",
    config={"displayModeBar": False},
)
st.caption(scale_note)

with st.expander("Benchmark table"):
    st.dataframe(predictions.style.format("{:.2%}"), width="stretch")

# --- Methodology (the quiet part) ----------------------------------------------

st.markdown("---")

with st.expander("How the benchmark is built"):
    st.markdown(
        f"""
Every published Bank of England concurrent stress test ({year_lo}–{year_hi})
reports, for each participating firm, the five-year impairment charge on each
major UK lending book. This app regresses those outcomes on the **worst point of each
scenario's macro paths** (house prices, CRE prices, unemployment, GDP,
corporate profits, Bank Rate) plus each firm's **pre-stress provision
coverage** — one ordinary-least-squares model per product, with backward-AIC
variable selection. Your benchmark is simply that model evaluated at your
scenario and your coverage levels.

**Firm identity is deliberately excluded.** No model is allowed to rate a firm
as riskier than its peers on the strength of its name — every prediction is
driven only by the scenario and the loan book you describe, never by who you
are. A single continuous **time trend** (years since the first test) is also
offered to each product and retained by AIC only where it earns its place,
letting the fit express whether stress outcomes have drifted over the
programme's life without overfitting to any individual year; custom scenarios
evaluate that trend as of the most recent published test.

Three calibrations sit behind the scenario picker. A **custom scenario** uses
the cross-scenario model above, fitted either to every published test (the
default) or, via the dropdown, to only the three most recent. Benchmarking
against a **published stress test** works differently: within a single test
every firm faces the same macro shocks, so those carry no cross-firm
information — peers therefore show their actual published results, and your
firm is placed by regressing that year's outcomes on provision coverage alone
(a small cross-section: treat it as a peer positioning, not a forecast). The
2014 test is not offered as a published benchmark because its five-year
outcomes are imputed from the three-year figures. The model detail below is
for the all-years reference calibration.

The methodology is a Python port of an R analysis originally built for this
purpose; the port reproduces the R coefficients to floating-point precision
against a 2019-vintage gold reference. Data, code and tests are on
[GitHub](https://github.com/quietsnooze/Pm_benchmarking). App version
v{__version__}.
"""
    )

    fit_summary = pd.DataFrame(
        {
            "Product": [_PRODUCT_LABELS[p] for p in fitted_models],
            "R²": [f"{m.rsquared:.3f}" for m in fitted_models.values()],
            "Observations": [int(m.nobs) for m in fitted_models.values()],
        }
    ).set_index("Product")
    st.table(fit_summary)

    product_tabs = st.tabs([_PRODUCT_LABELS[p] for p in fitted_models])
    for tab, (product, model) in zip(product_tabs, fitted_models.items(), strict=True):
        with tab:
            recipe = RECIPES[product]
            product_df = _per_product_dataset(modelling_df, product)
            scored = predict_with_model(product_df, model, actual_col=recipe.dependent_var)
            scored = scored.assign(firm_name=scored["firm_name"].replace(_SHORT_FIRM_NAMES))
            fig = actual_vs_expected_figure(
                scored,
                title=f"{_PRODUCT_LABELS[product]} — actual vs. predicted impairment",
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

            params = pd.DataFrame(
                {
                    "coefficient": model.params,
                    "std_err": model.bse,
                    "t": model.tvalues,
                    "p": model.pvalues,
                }
            )
            st.dataframe(params.style.format("{:.4f}"), width="stretch")

            with st.expander("Full statsmodels summary"):
                st.text(str(model.summary()))

    with st.expander("Underlying data"):
        st.markdown("**Modelling dataset** — one row per firm × ACS year.")
        st.dataframe(
            modelling_df.drop(
                columns=[c for c in modelling_df.columns if c.startswith("firm_name_")]
            ),
            width="stretch",
        )
        st.markdown("**Low-point shocks** — the scenario features, by ACS year.")
        st.dataframe(shocks_df.style.format("{:.3f}"), width="stretch")

st.markdown(
    f"""<div class="footer">Peter McIntyre ·
<a href="{LINKEDIN_URL}">LinkedIn</a> ·
<a href="{GITHUB_URL}">GitHub</a> ·
Public BoE data · Not investment advice, not a regulatory model.</div>""",
    unsafe_allow_html=True,
)
