"""Plotly chart builders used by the Streamlit app.

Pure functions: each returns a :class:`plotly.graph_objects.Figure` so
they can be unit-tested without involving Streamlit. The Streamlit layer
itself is exempt from tests per the project's testing policy.

Public surface:
    actual_vs_expected_figure(df, *, title) -> plotly.graph_objects.Figure
    predictions_heatmap(predictions, *, title) -> plotly.graph_objects.Figure
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def actual_vs_expected_figure(df: pd.DataFrame, *, title: str) -> go.Figure:
    """Scatter the model's predictions against the observed values.

    A 45-degree reference line is drawn so over- / under-prediction is
    immediately visible. Points are coloured by ``firm_name`` and
    annotated with the ``acsyear`` so a single chart shows every
    (firm, scenario) outcome at once.

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
    plot_df["acsyear_label"] = plot_df["acsyear"].astype(str)

    fig = px.scatter(
        plot_df,
        x="actual",
        y="prediction",
        color="firm_name",
        text="acsyear_label",
        hover_data=["firm_name", "acsyear", "actual", "prediction"],
        title=title,
    )
    fig.update_traces(textposition="top center")

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
        line={"dash": "dash", "color": "grey"},
    )
    fig.update_layout(
        xaxis={"range": [0, lim], "title": "Actual"},
        yaxis={"range": [0, lim], "title": "Predicted"},
        showlegend=True,
    )
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
        Reds-colorscale heatmap with cell labels formatted as percentages.
    """
    z = predictions.values * 100  # percent points for readability
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[c.title() for c in predictions.columns],
            y=list(predictions.index),
            colorscale="Reds",
            colorbar={"title": "IC %"},
            text=[[f"{v:.2f}%" for v in row] for row in z],
            texttemplate="%{text}",
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        xaxis={"title": "Product"},
        yaxis={"title": "Firm", "autorange": "reversed"},
    )
    return fig
