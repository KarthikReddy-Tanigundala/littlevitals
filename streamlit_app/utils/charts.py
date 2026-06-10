"""Plotly chart helpers + shared theme for the LittleVitals app."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---- Design tokens (shared with Power BI theme / CLAUDE.md §24) -------------
TEAL = "#1a6b5e"
INK = "#1c2b29"
GREY = "#8a9a97"
AMBER = "#e0a32e"
CORAL = "#d1495b"
STATUS_COLORS = {
    "Meets Benchmark": "#2e9e6b",
    "At Risk": "#e0a32e",
    "Below Benchmark": "#d1495b",
}
PLOTLY_TEMPLATE = "plotly_white"


def _base(fig: go.Figure, title: str | None = None, height: int = 380) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        font=dict(color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def on_time_trend(trend: pd.DataFrame, benchmark: float = 0.80) -> go.Figure:
    """Line: Cat 2 on-time % by FY for Victoria vs the national benchmark."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["financial_year"], y=trend["vic_on_time"],
        mode="lines+markers", name="Victoria",
        line=dict(color=TEAL, width=3),
    ))
    if "national_on_time" in trend:
        fig.add_trace(go.Scatter(
            x=trend["financial_year"], y=trend["national_on_time"],
            mode="lines+markers", name="National",
            line=dict(color=GREY, width=2, dash="dot"),
        ))
    fig.add_hline(
        y=benchmark, line_dash="dash", line_color="#d1495b",
        annotation_text=f"ACEM target ({benchmark:.0%})", annotation_position="bottom right",
    )
    fig.update_yaxes(tickformat=".0%", title="Cat 2 seen on time")
    return _base(fig, "Category 2 ED on-time performance vs benchmark")


def top_hospitals(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: top hospitals by total ED presentations."""
    df = df.sort_values("total_ed_presentations")
    fig = go.Figure(go.Bar(
        x=df["total_ed_presentations"], y=df["hospital_name"],
        orientation="h", marker_color=TEAL,
        text=df["total_ed_presentations"], texttemplate="%{text:,}", textposition="auto",
    ))
    fig.update_xaxes(title="Total ED presentations")
    return _base(fig, None, height=420)


def hospital_map(df: pd.DataFrame) -> go.Figure:
    """Bubble map of hospitals: size = presentations, colour = rating."""
    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude",
        size="total_ed_presentations", color="scorecard_overall_rating",
        color_discrete_map=STATUS_COLORS,
        hover_name="hospital_name",
        hover_data={"latitude": False, "longitude": False,
                    "lhn_name": True, "median_ed_wait_all_triage": True,
                    "pct_ed_seen_on_time_cat2": ":.0%"},
        size_max=28, zoom=5.4, center={"lat": -37.3, "lon": 145.0},
        mapbox_style="carto-positron",
    )
    return _base(fig, None, height=460)


def funnel_plot(df: pd.DataFrame, indicator: str = "pct_seen_on_time",
                volume: str = "presentations") -> go.Figure:
    """
    Spiegelhalter funnel plot (CLAUDE.md §18.2): indicator vs volume with
    binomial control limits that widen at low volume. Points outside the 99.8%
    limits are 'special cause' outliers — the fair way to compare institutions
    (avoids the league-table fallacy).
    """
    p_bar = float(np.average(df[indicator], weights=df[volume]))
    n_grid = np.linspace(max(df[volume].min() * 0.6, 50), df[volume].max() * 1.1, 200)
    se = np.sqrt(p_bar * (1 - p_bar) / n_grid)

    fig = go.Figure()
    for z, name, dash in [(1.96, "95% limit", "dot"), (3.09, "99.8% limit", "dash")]:
        fig.add_trace(go.Scatter(x=n_grid, y=np.clip(p_bar + z * se, 0, 1),
                                 mode="lines", line=dict(color=GREY, dash=dash, width=1),
                                 name=name, showlegend=True))
        fig.add_trace(go.Scatter(x=n_grid, y=np.clip(p_bar - z * se, 0, 1),
                                 mode="lines", line=dict(color=GREY, dash=dash, width=1),
                                 showlegend=False))
    fig.add_hline(y=p_bar, line_color=TEAL, line_width=2,
                  annotation_text=f"Pooled mean ({p_bar:.0%})")

    # Flag outliers beyond the 99.8% limits.
    se_pts = np.sqrt(p_bar * (1 - p_bar) / df[volume])
    outlier = (df[indicator] > p_bar + 3.09 * se_pts) | (df[indicator] < p_bar - 3.09 * se_pts)
    fig.add_trace(go.Scatter(
        x=df[volume], y=df[indicator], mode="markers+text",
        text=np.where(outlier, df["hospital_name"], ""), textposition="top center",
        textfont=dict(size=10),
        marker=dict(size=11, color=np.where(outlier, "#d1495b", TEAL),
                    line=dict(width=1, color="white")),
        name="Hospital", customdata=df[["hospital_name"]],
        hovertemplate="%{customdata[0]}<br>Volume %{x:,}<br>On-time %{y:.0%}<extra></extra>",
    ))
    fig.update_xaxes(title="ED presentations (Cat 2) — volume")
    fig.update_yaxes(title="Cat 2 seen on time", tickformat=".0%")
    return _base(fig, "Funnel plot — fair comparison of hospital on-time performance", height=460)
