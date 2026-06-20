"""Plotly visualizations used by the SignalFire Streamlit app."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


SIGNALFIRE_COLORS = {
    "navy": "#0B1320",
    "orange": "#FF6B35",
    "gold": "#F7C948",
    "blue": "#2F80ED",
    "green": "#27AE60",
    "gray": "#667085",
}


def _template_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=title,
        template="plotly_white",
        font={"family": "Inter, Arial, sans-serif"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 60, "b": 30},
        legend_title_text="",
    )
    return fig


def top_bar(frame: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> go.Figure:
    data = frame.sort_values(x, ascending=True)
    fig = px.bar(data, x=x, y=y, orientation="h", color=color, color_continuous_scale="Oranges")
    fig.update_traces(marker_line_width=0)
    return _template_layout(fig, title)


def theme_trend_line(frame: pd.DataFrame, theme: str, companies: list[str] | None = None) -> go.Figure:
    data = frame.loc[frame["theme"].eq(theme)].copy()
    if companies:
        data = data.loc[data["company"].isin(companies)]
    fig = px.line(
        data.sort_values("year"),
        x="year",
        y="theme_intensity",
        color="company",
        markers=True,
        hover_data=["industry"],
    )
    fig.update_yaxes(title="Theme intensity")
    return _template_layout(fig, f"{theme} intensity over time")


def industry_heatmap(frame: pd.DataFrame, year: int | None = None) -> go.Figure:
    data = frame.copy()
    if year is not None and "year" in data.columns:
        data = data.loc[data["year"].eq(year)]
    pivot = data.pivot_table(index="industry", columns="theme", values="theme_intensity", aggfunc="mean").fillna(0)
    fig = px.imshow(
        pivot,
        color_continuous_scale="YlOrRd",
        aspect="auto",
        labels={"color": "Intensity"},
    )
    fig.update_xaxes(side="top")
    return _template_layout(fig, "Industry theme penetration")


def company_theme_area(frame: pd.DataFrame, company: str) -> go.Figure:
    data = frame.loc[frame["company"].eq(company)].sort_values("year")
    fig = px.area(data, x="year", y="theme_intensity", color="theme", groupnorm="fraction")
    fig.update_yaxes(title="Share of strategic language", tickformat=".0%")
    return _template_layout(fig, f"{company}: strategic theme mix")


def opportunity_scatter(scorecard: pd.DataFrame, theme_filter: str | None = None) -> go.Figure:
    data = scorecard.copy()
    if theme_filter:
        data = data.loc[data["theme"].eq(theme_filter)]
    fig = px.scatter(
        data,
        x="strategic_momentum_score",
        y="consulting_opportunity_score",
        size="strategic_priority_score",
        color="industry",
        hover_name="company",
        hover_data=["theme", "priority_growth_rate", "transformation_readiness_score"],
    )
    fig.update_xaxes(title="Strategic momentum")
    fig.update_yaxes(title="Consulting opportunity")
    return _template_layout(fig, "Opportunity radar")


def score_gauge(score: float, title: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": "/100"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": SIGNALFIRE_COLORS["orange"]},
                "steps": [
                    {"range": [0, 40], "color": "#F2F4F7"},
                    {"range": [40, 70], "color": "#FFE6D5"},
                    {"range": [70, 100], "color": "#FFB088"},
                ],
            },
        )
    )
    return _template_layout(fig, title)
