"""Plotly chart builders used by the Streamlit app.

Pure functions: each returns a :class:`plotly.graph_objects.Figure` so
they can be unit-tested without involving Streamlit. The Streamlit layer
itself is exempt from tests per the project's testing policy.

All figures share one visual language ("BoE institutional"): paper-white
surface, ink text, teal data marks, and a gilt accent that is reserved
for the user's own firm — it appears nowhere else, so wherever gilt
shows up on the page it means "you".

Public surface:
    actual_vs_expected_figure(df, *, title) -> plotly.graph_objects.Figure
    benchmark_strip_figure(predictions, *, highlight, title) -> plotly.graph_objects.Figure
    predictions_heatmap(predictions, *, title) -> plotly.graph_objects.Figure
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Design tokens — kept in sync with .streamlit/config.toml and the CSS in
# app.py. Colours validated (contrast + colour-vision-deficiency) against
# the paper surface.
_PAPER = "#FAFAF7"
_INK = "#1C2A33"
_MUTED = "#5C5648"
_GRID = "#E7E5DC"
_TEAL = "#0C82A6"  # peer data marks
_TEAL_DEEP = "#0E5E67"  # reference lines
_GILT = "#8F6B1E"  # highlight marker — "your firm", used for nothing else

# Sequential ramp for magnitude (light -> dark maroon). Light end kept
# subtle because heatmap cells always print their value.
_SEVERITY_RAMP = [
    "#F2DCE3",
    "#E3BACA",
    "#D096AE",
    "#B96E90",
    "#9C476F",
    "#77254E",
    "#4E0F32",
]

# Fixed-order categorical palette for firm identity, validated for CVD
# separation and >= 3:1 contrast on the paper surface. One floor-band
# pair (rose vs teal) is relieved by the per-firm marker symbols below.
_FIRM_COLOURS = ["#0C82A6", "#5A55C4", "#B98214", "#D0568A", "#3E8A46", "#943B24"]
_FIRM_SYMBOLS = ["circle", "square", "diamond", "triangle-up", "cross", "x"]

_FONT_BODY = "Source Sans 3, Source Sans Pro, sans-serif"
_FONT_MONO = "IBM Plex Mono, ui-monospace, monospace"


def _apply_house_style(fig: go.Figure) -> go.Figure:
    """Shared layout: surfaces, fonts, recessive grid and axes."""
    fig.update_layout(
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PAPER,
        font={"family": _FONT_BODY, "color": _INK, "size": 14},
        hoverlabel={
            "bgcolor": _INK,
            "font": {"family": _FONT_MONO, "color": _PAPER, "size": 13},
            "bordercolor": _INK,
        },
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    fig.update_xaxes(
        gridcolor=_GRID,
        linecolor=_GRID,
        zerolinecolor=_GRID,
        tickfont={"family": _FONT_MONO, "size": 12, "color": _MUTED},
        title_font={"size": 13, "color": _MUTED},
    )
    fig.update_yaxes(
        gridcolor=_GRID,
        linecolor=_GRID,
        zerolinecolor=_GRID,
        tickfont={"family": _FONT_BODY, "size": 13, "color": _INK},
        title_font={"size": 13, "color": _MUTED},
    )
    # Styling an absent figure title creates an empty title object that
    # plotly.js renders as the literal string "undefined".
    if fig.layout["title"]["text"]:  # pyright: ignore[reportIndexIssue]
        fig.update_layout(title_font={"family": _FONT_BODY, "color": _INK, "size": 16})
    return fig


def actual_vs_expected_figure(df: pd.DataFrame, *, title: str) -> go.Figure:
    """Scatter the model's predictions against the observed values.

    A 45-degree reference line is drawn so over- / under-prediction is
    immediately visible. Points are coloured by ``firm_name`` (with a
    distinct marker symbol per firm as a colour-blind-safe secondary
    encoding); the ``acsyear`` sits in the hover, so a single chart shows
    every (firm, scenario) outcome at once without label clutter.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ``actual``, ``prediction``, ``firm_name``,
        ``acsyear``. Rows where either ``actual`` or ``prediction`` is
        NaN are dropped before plotting.
    title : str
        Figure title (e.g. ``"Mortgage AvE"``).

    Returns
    -------
    plotly.graph_objects.Figure
        Ready to pass to ``st.plotly_chart``.
    """
    plot_df = df.dropna(subset=["actual", "prediction"]).copy()

    fig = px.scatter(
        plot_df,
        x="actual",
        y="prediction",
        color="firm_name",
        symbol="firm_name",
        color_discrete_sequence=_FIRM_COLOURS,
        symbol_sequence=_FIRM_SYMBOLS,
        hover_data=["firm_name", "acsyear", "actual", "prediction"],
        title=title,
    )
    fig.update_traces(marker={"size": 9, "line": {"width": 1, "color": _PAPER}})

    # Square axis range covering both actual and prediction; keeps the
    # 45-degree reference line interpretable. Floor at 0 since impairment
    # charge percentages are non-negative in the observed data.
    upper = max(
        plot_df["actual"].max() if not plot_df.empty else 0.0,
        plot_df["prediction"].max() if not plot_df.empty else 0.0,
        1e-6,
    )
    lim = upper * 1.1
    fig.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=lim,
        y1=lim,
        line={"dash": "dot", "width": 1, "color": _TEAL_DEEP},
    )
    fig.update_layout(
        xaxis={"range": [0, lim], "title": "Actual", "tickformat": ".1%"},
        yaxis={"range": [0, lim], "title": "Predicted", "tickformat": ".1%"},
        showlegend=True,
        legend={"title": "", "orientation": "h", "y": -0.18},
    )
    return _apply_house_style(fig)


def benchmark_strip_figure(
    predictions: pd.DataFrame,
    *,
    highlight: str | None = None,
    title: str | None = None,
) -> go.Figure:
    """Dot-plot small multiples: where each firm sits, per product.

    One panel per product (its own x-scale — product loss rates differ
    by an order of magnitude, so a shared axis would flatten the small
    books). Within a panel, firms are sorted by predicted impairment so
    the ranking reads top-down. Peers are teal dots; the ``highlight``
    firm — "you" — is a gilt diamond in its own trace.

    Parameters
    ----------
    predictions : pd.DataFrame
        Indexed by ``firm_name``, one column per product, values are
        predicted 5-year impairment-charge rates (fractions, not
        percent). Output of
        :func:`uk_stress_benchmark.pipeline.predict_for_scenario`.
        NaN cells are dropped panel-by-panel.
    highlight : str | None
        Index label to single out (e.g. ``"Your firm"``). ``None`` — or
        a label absent from the index — draws peers only.
    title : str | None
        Optional figure title.

    Returns
    -------
    plotly.graph_objects.Figure
        Ready to pass to ``st.plotly_chart``.
    """
    products = list(predictions.columns)
    # One panel per row: plotly subplot grids don't reflow on small
    # screens, and a benchmark read on a phone matters here.
    n_cols = 1
    n_rows = len(products)

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[str(p) for p in products],
        vertical_spacing=0.42 / n_rows,
    )

    legend_shown = {"peer": False, "you": False}
    for i, product in enumerate(products):
        row, col = divmod(i, n_cols)
        series = pd.Series(predictions[product]).dropna().sort_values()
        peers = series if highlight is None else series.drop(index=highlight, errors="ignore")
        fig.add_trace(
            go.Scatter(
                x=peers.values,
                y=peers.index,
                mode="markers",
                name="UK peers",
                marker={"color": _TEAL, "size": 10},
                showlegend=not legend_shown["peer"],
                legendgroup="peer",
                hovertemplate="%{y}<br>%{x:.2%}<extra></extra>",
            ),
            row=row + 1,
            col=col + 1,
        )
        legend_shown["peer"] = True
        if highlight is not None and highlight in series.index:
            fig.add_trace(
                go.Scatter(
                    x=[series.loc[highlight]],
                    y=[highlight],
                    mode="markers",
                    name=highlight,
                    marker={
                        "color": _GILT,
                        "symbol": "diamond",
                        "size": 14,
                        "line": {"width": 2, "color": _PAPER},
                    },
                    showlegend=not legend_shown["you"],
                    legendgroup="you",
                    hovertemplate=f"{highlight}<br>%{{x:.2%}}<extra></extra>",
                ),
                row=row + 1,
                col=col + 1,
            )
            legend_shown["you"] = True

    fig.update_xaxes(tickformat=".1%", rangemode="tozero")
    fig.update_yaxes(automargin=True)
    fig.update_layout(
        height=max(300, 215 * n_rows),
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.08,
            "x": 0,
            "title": "",
        },
    )
    if title is not None:
        fig.update_layout(title=title)
    _apply_house_style(fig)
    fig.update_annotations(font={"family": _FONT_BODY, "size": 14, "color": _INK})
    return fig


def predictions_heatmap(predictions: pd.DataFrame, *, title: str) -> go.Figure:
    """Render a (firm x product) predicted-impairment-charge heatmap.

    Parameters
    ----------
    predictions : pd.DataFrame
        Indexed by ``firm_name``, one column per product, values are
        predicted 5-year impairment-charge percentages. Output of
        :func:`uk_stress_benchmark.pipeline.predict_for_scenario`.
    title : str
        Figure title.

    Returns
    -------
    plotly.graph_objects.Figure
        Sequential-maroon heatmap with cell labels formatted as
        percentages. Every cell prints its value, so the light end of
        the ramp stays readable.
    """
    z = predictions.values * 100  # percent points for readability
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[c.title() for c in predictions.columns],
            y=list(predictions.index),
            colorscale=_SEVERITY_RAMP,
            colorbar={
                "title": "IC %",
                "outlinewidth": 0,
                "tickfont": {"family": _FONT_MONO, "size": 12},
            },
            xgap=2,
            ygap=2,
            text=[[f"{v:.2f}%" for v in row] for row in z],
            texttemplate="%{text}",
            textfont={"family": _FONT_MONO, "size": 12},
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        xaxis={"title": "Product"},
        yaxis={"title": "Firm", "autorange": "reversed"},
    )
    return _apply_house_style(fig)
