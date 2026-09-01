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
from uk_stress_benchmark.per_firm import fit_per_firm_models
from uk_stress_benchmark.pipeline import (
    RECIPES,
    build_modelling_dataset,
    fit_product_models,
    predict_for_scenario,
    year_benchmark,
)
from uk_stress_benchmark.provisions import load_btl, load_provisions
from uk_stress_benchmark.results import load_results
from uk_stress_benchmark.scenario_index import modelling_paths
from uk_stress_benchmark.scenarios import build_low_point_shocks
from uk_stress_benchmark.viz import actual_vs_expected_figure, benchmark_strip_figure

PROCESSED = Path(__file__).resolve().parent / "processed_inputs"

YOUR_FIRM = "Your firm"

GITHUB_URL = "https://github.com/quietsnooze/Pm_benchmarking"
LINKEDIN_URL = "https://www.linkedin.com/in/pemcintyre/"

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

.block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 2rem; }

h1, h2, h3 {
    font-family: 'Spectral', Georgia, serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    color: #1C2A33;
}
h1 { font-size: 2.9rem !important; line-height: 1.08 !important; margin-bottom: 0 !important; }

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
    max-width: 40rem;
    margin: 0.5rem 0 0 0;
}
.byline { font-size: 0.88rem; color: #5C5648; margin-top: 0.95rem; }
.byline a { color: #0E5E67; text-decoration: none; border-bottom: 1px solid #CFCCC0; }

/* Hero band — the one filled surface on the page. Uses the paper-tint
   secondary background so it reads as a masthead, not a coloured banner. */
.hero-band {
    background: #F0EEE7;
    border: 1px solid #E2DFD4;
    border-radius: 16px;
    padding: 2rem 2.1rem;
    margin: 0.3rem 0 1.6rem 0;
    display: flex;
    gap: 2rem;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
}
.hero-main { flex: 1 1 30rem; min-width: 0; }
.hero-stats {
    flex: 0 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-left: 1.7rem;
    border-left: 1px solid #DAD6C9;
}
.stat .n {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.55rem;
    color: #0E5E67;
    line-height: 1;
}
.stat .l {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.78rem;
    color: #5C5648;
    margin-top: 0.25rem;
    letter-spacing: 0.01em;
}

/* Section headers inside the control / results cards. */
.card-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #0E5E67;
    margin: 0 0 0.15rem 0;
}
.card-eyebrow .step { color: #5C5648; margin-right: 0.5rem; }
.card-title { font-size: 1.4rem !important; margin: 0 0 0.1rem 0 !important; }
.card-sub { font-size: 0.92rem; color: #5C5648; line-height: 1.45; margin: 0.3rem 0 0.4rem 0; }
.result-lead { font-size: 1.0rem; color: #3D4A52; line-height: 1.5; margin: 0.2rem 0 0.6rem 0; }
.result-lead strong { color: #1C2A33; }

.chips { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0 0.3rem 0; }
.chip {
    background: #FAFAF7;
    border: 1px solid #E2DFD4;
    border-radius: 6px;
    padding: 0.32rem 0.62rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #1C2A33;
    white-space: nowrap;
}
.chip .lbl { color: #5C5648; margin-right: 0.45rem; font-family: 'Source Sans 3', sans-serif; }

/* Bordered containers become the app's cards — a touch more radius than
   the Streamlit default; background left as the page paper so the plotly
   surfaces sit flush inside them. */
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }

.footer {
    margin-top: 2.6rem;
    padding-top: 1.1rem;
    border-top: 1px solid #E2DFD4;
    font-size: 0.85rem;
    color: #5C5648;
}
.footer a { color: #0E5E67; text-decoration: none; border-bottom: 1px solid #CFCCC0; }

@media (max-width: 640px) {
    .block-container { padding-top: 1.4rem; }
    h1 { font-size: 2.05rem !important; }
    .lede { font-size: 1.02rem; }
    .hero-band { padding: 1.4rem 1.25rem; gap: 1.2rem; }
    .hero-stats {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 1rem 1.7rem;
        padding-left: 0;
        padding-top: 1.1rem;
        border-left: none;
        border-top: 1px solid #DAD6C9;
        width: 100%;
    }
}
</style>
"""


def _card_head(step: str, eyebrow: str, title: str, sub: str | None = None) -> None:
    """Mono eyebrow + serif title for a card section, optional sub-line."""
    html = (
        f'<p class="card-eyebrow"><span class="step">{step}</span>{eyebrow}</p>'
        f'<h3 class="card-title">{title}</h3>'
    )
    if sub:
        html += f'<p class="card-sub">{sub}</p>'
    st.markdown(html, unsafe_allow_html=True)


# ----------------------------- data plumbing -------------------------------


def _provisions_path() -> Path:
    """Prefer the annual (firm x acsyear) provisions panel when ingest has built it.

    ``firm_provisions_annual.csv`` comes from ``uv run extract-provisions``
    (EBA transparency-exercise data, see SOURCES.md); until it exists the
    static 2019 snapshot in ``firm_provisions.csv`` is used as before.
    """
    annual = PROCESSED / "firm_provisions_annual.csv"
    return annual if annual.exists() else PROCESSED / "firm_provisions.csv"


@st.cache_data(show_spinner="Loading firm results / provisions…")
def _load_firm_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    results = load_results(PROCESSED / "firm_results.csv")
    # valid_firms makes a firm-name spelling drift between the results and
    # provisions files fail loudly instead of silently dropping the firm in
    # the inner join downstream.
    known = set(results["firm_name"])
    return (
        results,
        load_provisions(_provisions_path(), valid_firms=known),
        load_btl(PROCESSED / "firm_btl.csv", valid_firms=known),
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
    results, provisions, btl = _load_firm_data()
    shocks = _load_shocks()
    modelling_df = build_modelling_dataset(results, shocks, provisions, btl=btl)
    fitted = fit_product_models(modelling_df)
    return modelling_df, fitted


@st.cache_resource(show_spinner="Calibrating on recent stress tests…")
def _fit_recent_models() -> tuple[list[int], dict]:
    """Alternative calibration: only the three most recent stress tests."""
    mdf, _ = _fit_everything()
    years = sorted(int(y) for y in pd.Series(mdf["acsyear"]).unique())[-3:]
    recent = mdf.loc[pd.Series(mdf["acsyear"]).isin(years)]
    return years, fit_product_models(recent)


@st.cache_resource(show_spinner="Fitting a model per firm…")
def _fit_per_firm():
    """Per-firm diagnostics, scored against the all-years pooled baseline."""
    mdf, fitted = _fit_everything()
    return fit_per_firm_models(mdf, baseline_models=fitted)


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

# Everything the two-column app region reads is prepared up front, so the
# controls column and the results column can be written in one pass.
published_years = _published_years()
recent_years, recent_models = _fit_recent_models()
# With a per-year provisions panel, a firm has one row per acsyear; keep
# its most recent year's coverage rather than drop_duplicates' default
# first-row (oldest) pick.
firms_df = (
    modelling_df.sort_values("acsyear")
    .drop_duplicates("firm_name", keep="last")
    .reset_index(drop=True)
)

# --- Hero band --------------------------------------------------------------

# Factual "at a glance" tiles fill the desktop right rail; they wrap under the
# masthead on a phone. Numbers are mono/teal — never gilt, which stays "you".
_hero_stats = [
    (str(len(peer_firms)), "UK banks in the panel"),
    (str(len(fitted_models)), "loan books modelled"),
    (f"{year_lo}–{year_hi}", f"{len(published_years)} published stress tests"),
]
_stats_html = "".join(
    f'<div class="stat"><div class="n">{n}</div><div class="l">{lbl}</div></div>'
    for n, lbl in _hero_stats
)
st.markdown(
    f"""<div class="hero-band">
  <div class="hero-main">
    <p class="eyebrow">UK bank stress testing · Bank of England scenarios \
{year_lo}–{year_hi}</p>
    <h1>Benchmark your stressed losses against the UK banks</h1>
    <p class="lede">Set a stress scenario, describe your loan book in three
numbers, and see the five-year impairment charge a firm like yours would report
next to {", ".join(peer_firms[:-1])} and {peer_firms[-1]} — calibrated on every
firm-level result the Bank of England has published for its concurrent stress
tests, {year_lo} to {year_hi}.</p>
    <p class="byline">Built by Peter McIntyre ·
<a href="{LINKEDIN_URL}">LinkedIn</a> ·
<a href="{GITHUB_URL}">Source &amp; methodology on GitHub</a></p>
  </div>
  <div class="hero-stats">{_stats_html}</div>
</div>""",
    unsafe_allow_html=True,
)

# --- App region: controls (left) | benchmark (right) --------------------------

# Two independent columns rendered in one pass. The controls column runs
# first, so every widget value it collects is in scope by the time the
# results column computes and draws the benchmark. On a phone Streamlit
# stacks the columns, putting the controls above the result — the natural
# read order — with no horizontal scroll.
controls_col, results_col = st.columns([5, 7], gap="large")

# ---- Controls: scenario + firm ------------------------------------------------

with controls_col:
    with st.container(border=True):
        _card_head("01", "Scenario", "Set the scenario")

        mode = st.segmented_control(
            "Scenario type",
            options=["Published stress test", "Design your own"],
            default="Published stress test",
            label_visibility="collapsed",
            key="scenario_mode",
        )
        is_custom = mode == "Design your own"
        calibration = "all"
        shock_values: dict[str, float] = {}
        scenario_year = int(st.session_state.get("_scenario_year", published_years[-1]))

        if not is_custom:
            scenario_year = int(
                st.selectbox(
                    "Bank of England stress test",
                    options=published_years,
                    index=len(published_years) - 1,
                    format_func=lambda y: f"{y} ACS stress test",
                )
            )
            # Remember the chosen year (and re-anchor the custom-mode sliders
            # to it), so "show me ACS 2022, then tweak it" works by switching
            # modes.
            if st.session_state.get("_scenario_year") != scenario_year:
                st.session_state["_scenario_year"] = scenario_year
                for _slider_col, *_ in _SHOCK_SLIDERS:
                    st.session_state.pop(_slider_col, None)

            year_row = shocks_df.loc[scenario_year]
            chips = "".join(
                f'<span class="chip"><span class="lbl">{label}</span>{year_row[col]:+.0%}</span>'
                for col, label in _CHIP_SHOCKS
                if col in year_row.index and pd.notna(year_row[col])
            )
            st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)
            st.caption(
                "A published stress test's shocks are fixed — every firm faced the "
                "same scenario. Switch to “Design your own” to move the shocks "
                "yourself."
            )
        else:
            calibration = (
                st.segmented_control(
                    "Calibration",
                    options=["all", "recent"],
                    default="all",
                    format_func=lambda c: "All tests" if c == "all" else "Last three",
                )
                or "all"
            )
            _recent_list = ", ".join(str(y) for y in recent_years)
            st.caption(
                f"Model fitted to every published test ({year_lo}–{year_hi}), or "
                f"only the three most recent ({_recent_list})."
            )

            defaults_row = shocks_df.loc[scenario_year]
            with st.expander("Adjust the shocks", expanded=True):
                st.caption(
                    f"Sliders start from the {scenario_year} stress test's shocks. "
                    "Each shock is the worst point of the scenario's five-year path, "
                    "as a change from the starting level. Bank Rate moves are "
                    "multiples of the rate itself — a 5× rise of a 0.5% rate takes "
                    "it to 3%."
                )
                # Single column: the control rail is narrow, so side-by-side
                # sliders would be cramped on desktop and reorder awkwardly when
                # Streamlit stacks them on a phone.
                for col, label, lo, hi, step, as_pct in _SHOCK_SLIDERS:
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

    with st.container(border=True):
        _card_head(
            "02",
            "Your firm",
            "Describe your firm",
            "Provision coverage — provisions already held, as a share of each book — "
            "is the only firm-specific input the benchmark needs. Defaults are the "
            "peer medians.",
        )
        # Stacked, not side-by-side: three number inputs read cleanly down the
        # narrow rail and need no special-casing when the layout collapses.
        coverage_inputs: dict[str, float] = {}
        for cov_col, label, help_text in _COVERAGE_INPUTS:
            peer_median_pct = float(pd.Series(firms_df[cov_col]).median()) * 100
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

        # Buy-to-let share of the mortgage book is a structural mortgage-risk
        # input. It's only rendered as a live control when the fitted mortgage
        # model actually selected it (backward-AIC may drop it); otherwise your
        # firm inherits the peer-median share so predictions still resolve and
        # we don't show a control that moves nothing.
        peer_btl_median = float(pd.Series(firms_df["btl_share"]).median())
        if "btl_share" in fitted_models["mortgage"].params.index:
            btl_entered = st.number_input(
                "Buy-to-let share of mortgage book (%)",
                min_value=0.0,
                max_value=100.0,
                value=round(peer_btl_median * 100, 1),
                step=1.0,
                format="%.1f",
                help=(
                    "Buy-to-let balances as a share of your mortgage book. A higher "
                    "BTL share tends to raise modelled stressed mortgage losses."
                ),
            )
            your_btl = btl_entered / 100
        else:
            your_btl = peer_btl_median
        firm_inputs = {**coverage_inputs, "btl_share": your_btl}

# ---- Results: the benchmark ---------------------------------------------------

with results_col, st.container(border=True):
    _card_head("03", "Benchmark", "Read the benchmark")

    if is_custom:
        models_in_use = fitted_models if calibration == "all" else recent_models
        scoring_df = _with_your_firm(firms_df, firm_inputs)
        predictions = predict_for_scenario(models_in_use, shock_values, scoring_df)
        _recent_list = ", ".join(str(y) for y in recent_years)
        calibration_note = (
            f"calibrated on every published stress test ({year_lo}–{year_hi})"
            if calibration == "all"
            else f"calibrated on the last three stress tests ({_recent_list})"
        )
        st.markdown(
            f'<p class="result-lead">Predicted five-year impairment charge, as a '
            f"percentage of each book, under your custom scenario — "
            f"{calibration_note}. The gilt diamond is your firm.</p>",
            unsafe_allow_html=True,
        )
        scale_note = (
            "Each panel has its own scale — mortgage loss rates are an order of "
            "magnitude smaller than unsecured retail. Predictions can dip below "
            "zero where the scenario sits outside the calibration range; read "
            "those as 'negligible', not as a forecast of write-backs."
        )
        download_name = "benchmark_custom.csv"
    else:
        predictions = year_benchmark(modelling_df, scenario_year, coverage_inputs)
        st.markdown(
            f'<p class="result-lead">Peer dots show the <strong>actual published '
            f"results</strong> of the {scenario_year} stress test — five-year "
            f"impairment charge as a percentage of each book. Your firm (the gilt "
            f"diamond) is placed on that year's peer cross-section using your "
            f"provision coverage.</p>",
            unsafe_allow_html=True,
        )
        scale_note = (
            "Each panel has its own scale — mortgage loss rates are an order of "
            "magnitude smaller than unsecured retail. Peer values are as "
            "published; only your firm's marker is modelled. Where too few firms "
            "published a product that year, your firm's marker is omitted."
        )
        download_name = f"benchmark_{scenario_year}.csv"

    predictions = predictions.rename(columns=_PRODUCT_LABELS)
    _ordered = [c for c in _PRODUCT_LABELS.values() if c in predictions.columns]
    predictions = predictions.loc[:, _ordered].dropna(axis=1, how="all")

    st.plotly_chart(
        benchmark_strip_figure(predictions.rename(index=_SHORT_FIRM_NAMES), highlight=YOUR_FIRM),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(scale_note)

    # CSV export of the same table, in percentage points (matching the
    # "% of book" framing on screen) so it opens ready to reuse.
    csv_bytes = (predictions * 100).round(4).rename_axis("firm").to_csv().encode("utf-8")
    st.download_button(
        "Download benchmark table (CSV)",
        data=csv_bytes,
        file_name=download_name,
        mime="text/csv",
        width="stretch",
    )
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
are. The mortgage model additionally offers each firm's **buy-to-let share**
of its mortgage book — a structural risk driver the macro shocks and provision
coverage don't capture — as a stepwise candidate, kept only if it improves the
fit. It is a single static figure per firm (see the source notes on GitHub),
applied across every year rather than tracked test-by-test.

Three calibrations sit behind the scenario picker. A **custom scenario** uses
the cross-scenario model above, fitted either to every published test (the
default) or, via the calibration toggle, to only the three most recent. Benchmarking
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

# --- Per-firm accuracy (research view) -----------------------------------------

# The headline benchmark refuses to key off firm identity. This section does
# the opposite as a research aside: a separate regression per firm, fitted on
# that firm's own history, to show how well — and whether better than the
# pooled model — each firm's losses can be reproduced.

with st.expander("How accurate is the model for each firm?"):
    st.markdown(
        f"""
The headline benchmark deliberately ignores firm identity. This research view
does the opposite: it fits a **separate regression for each firm**, using only
that firm's own {year_lo}–{year_hi} stress-test history, to ask how closely a
firm-specific model tracks that one firm's published losses — and whether it
beats the pooled model.

Only the macro shocks move within a single firm's rows (its provision coverage
and buy-to-let share are fixed), so each firm-product model regresses that
firm's outcomes on scenario severity, with forward-stepwise selection kept
small enough for the handful of stress tests a firm has faced. Read these as an
**overfitting diagnostic, not a forecast**: with so few points per firm a high
R² shows the *shape* of the relationship, not out-of-sample skill. The honest
column is **firm-model RMSE vs pooled RMSE** — where a firm's own model has a
much lower error than the pooled model scored on the same rows, that firm's
losses carry structure the one-size-fits-all benchmark misses.
"""
    )

    per_firm = _fit_per_firm()
    acc = per_firm.accuracy

    # Headline: firm × product in-sample R².
    r2 = (
        acc.pivot(index="firm_name", columns="product", values="r_squared")
        .rename(columns=_PRODUCT_LABELS)
        .rename(index=_SHORT_FIRM_NAMES)
    )
    r2 = r2.loc[:, [c for c in _PRODUCT_LABELS.values() if c in r2.columns]]
    st.markdown("**In-sample R² — the share of each firm's own loss variation the fit explains.**")
    st.dataframe(r2.style.format("{:.0%}", na_rep="—"), width="stretch")

    # Detail: one row per firm-product, firm-specific error against the pooled
    # model's error on the very same rows.
    detail = acc.assign(
        product=acc["product"].map(_PRODUCT_LABELS),
        predictors=acc["predictors"].map(lambda drivers: ", ".join(drivers) if drivers else "—"),
    ).rename(
        columns={
            "firm_name": "Firm",
            "product": "Product",
            "n_obs": "Stress tests",
            "n_predictors": "Drivers",
            "predictors": "Selected drivers",
            "r_squared": "R²",
            "r_squared_adj": "Adj. R²",
            "rmse": "Firm-model RMSE",
            "pooled_rmse": "Pooled RMSE",
        }
    )
    st.markdown("**Per-firm fit detail** — firm-specific error vs the pooled model, same rows.")
    st.dataframe(
        detail.style.format(
            {
                "R²": "{:.2f}",
                "Adj. R²": "{:.2f}",
                "Firm-model RMSE": "{:.3%}",
                "Pooled RMSE": "{:.3%}",
            },
            na_rep="—",
        ),
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "Download per-firm accuracy (CSV)",
        data=acc.to_csv(index=False).encode("utf-8"),
        file_name="per_firm_accuracy.csv",
        mime="text/csv",
        width="stretch",
    )

st.markdown(
    f"""<div class="footer">Peter McIntyre ·
<a href="{LINKEDIN_URL}">LinkedIn</a> ·
<a href="{GITHUB_URL}">GitHub</a> ·
Public BoE data · Not investment advice, not a regulatory model.</div>""",
    unsafe_allow_html=True,
)
