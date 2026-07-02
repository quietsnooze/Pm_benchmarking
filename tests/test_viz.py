"""Tests for the pure chart-builder helpers used by the Streamlit app."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from uk_stress_benchmark.viz import (
    actual_vs_expected_figure,
    benchmark_strip_figure,
    predictions_heatmap,
)


def _toy_predictions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "firm_name": ["Barclays", "Barclays", "HSBC", "HSBC"],
            "acsyear": [2017, 2018, 2017, 2018],
            "actual": [0.01, 0.012, 0.008, 0.01],
            "prediction": [0.011, 0.011, 0.0079, 0.0095],
        }
    )


def test_actual_vs_expected_figure_returns_a_plotly_figure_with_title():
    fig = actual_vs_expected_figure(_toy_predictions(), title="Mortgage AvE")
    assert isinstance(fig, go.Figure)
    assert fig.layout["title"]["text"] == "Mortgage AvE"


def test_actual_vs_expected_figure_includes_every_input_row():
    df = _toy_predictions()
    fig = actual_vs_expected_figure(df, title="Test")
    # All 4 (firm, year) tuples should appear in the figure's traces.
    points: list[tuple[float, float]] = []
    for trace in fig.data:
        if trace.x is None or trace.y is None:
            continue
        points.extend(zip(trace.x, trace.y, strict=True))
    expected_points = list(zip(df["actual"], df["prediction"], strict=True))
    for p in expected_points:
        assert any(abs(p[0] - x) < 1e-9 and abs(p[1] - y) < 1e-9 for x, y in points), p


def test_actual_vs_expected_figure_axes_share_a_common_range():
    # The 45-degree reference line is only meaningful if x and y axes
    # share the same range.
    df = _toy_predictions()
    fig = actual_vs_expected_figure(df, title="Test")
    assert fig.layout["xaxis"]["range"] == fig.layout["yaxis"]["range"]


def test_actual_vs_expected_figure_handles_nan_predictions():
    # Firms whose prediction comes back NaN (missing predictor) shouldn't
    # break chart-building — they're just dropped from the scatter.
    df = pd.DataFrame(
        {
            "firm_name": ["Barclays", "HSBC"],
            "acsyear": [2017, 2017],
            "actual": [0.01, 0.008],
            "prediction": [0.011, float("nan")],
        }
    )
    fig = actual_vs_expected_figure(df, title="Test")
    assert isinstance(fig, go.Figure)  # didn't raise


def _toy_benchmark() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "mortgage": [0.012, 0.008, 0.015, 0.010],
            "retail": [0.06, 0.04, 0.09, 0.05],
        },
        index=pd.Index(["Barclays", "HSBC", "Lloyds", "Your firm"], name="firm_name"),
    )


def test_benchmark_strip_figure_returns_a_plotly_figure():
    fig = benchmark_strip_figure(_toy_benchmark(), highlight="Your firm")
    assert isinstance(fig, go.Figure)


def test_benchmark_strip_figure_plots_every_value():
    predictions = _toy_benchmark()
    fig = benchmark_strip_figure(predictions, highlight="Your firm")
    plotted: list[float] = []
    for trace in fig.data:
        if trace.x is not None:
            plotted.extend(float(v) for v in trace.x)
    for product in predictions.columns:
        for value in predictions[product]:
            assert any(abs(value - x) < 1e-9 for x in plotted), (product, value)


def test_benchmark_strip_figure_separates_highlight_from_peers():
    # The highlighted firm must live in its own trace(s) so it can carry a
    # distinct marker — peers and highlight are never mixed in one trace.
    predictions = _toy_benchmark()
    fig = benchmark_strip_figure(predictions, highlight="Your firm")
    for trace in fig.data:
        if trace.y is None:
            continue
        names = set(trace.y)
        assert not ({"Your firm"} < names), "highlight mixed into a peer trace"
    highlight_values = {float(v) for v in predictions.loc["Your firm"]}
    highlight_plotted: set[float] = set()
    for trace in fig.data:
        if trace.y is not None and set(trace.y) == {"Your firm"}:
            highlight_plotted.update(float(v) for v in trace.x)
    assert highlight_values == highlight_plotted


def test_benchmark_strip_figure_without_highlight_plots_peers_only():
    predictions = _toy_benchmark().drop(index="Your firm")
    fig = benchmark_strip_figure(predictions, highlight=None)
    assert isinstance(fig, go.Figure)
    plotted_names: set[str] = set()
    for trace in fig.data:
        if trace.y is not None:
            plotted_names.update(trace.y)
    assert plotted_names == {"Barclays", "HSBC", "Lloyds"}


def test_benchmark_strip_figure_drops_nan_values_without_raising():
    predictions = _toy_benchmark()
    predictions.loc["HSBC", "retail"] = float("nan")
    fig = benchmark_strip_figure(predictions, highlight="Your firm")
    assert isinstance(fig, go.Figure)
    for trace in fig.data:
        if trace.x is not None:
            assert all(x == x for x in trace.x), "NaN leaked into a trace"


def test_predictions_heatmap_returns_figure_with_firms_and_products():
    predictions = pd.DataFrame(
        {"mortgage": [0.012, 0.008], "retail": [0.06, 0.04]},
        index=pd.Index(["Barclays", "HSBC"], name="firm_name"),
    )
    fig = predictions_heatmap(predictions, title="Test")
    assert isinstance(fig, go.Figure)
    assert fig.layout["title"]["text"] == "Test"
    # Heatmap data x-axis covers products, y-axis covers firms.
    heatmap_trace = fig.data[0]
    assert set(heatmap_trace.x) == {"Mortgage", "Retail"}
    assert set(heatmap_trace.y) == {"Barclays", "HSBC"}
