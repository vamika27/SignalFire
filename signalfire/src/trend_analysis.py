"""Trend detection for strategic priorities."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def min_max(series: pd.Series) -> pd.Series:
    """Scale a numeric series to 0-100 while handling constants."""

    values = pd.to_numeric(series, errors="coerce").fillna(0)
    spread = values.max() - values.min()
    if spread == 0:
        return pd.Series(np.where(values > 0, 50.0, 0.0), index=series.index)
    return (values - values.min()) / spread * 100


def calculate_growth_rates(company_theme_scores: pd.DataFrame) -> pd.DataFrame:
    """Calculate year-over-year growth and acceleration by company/theme."""

    if company_theme_scores.empty:
        return company_theme_scores.copy()

    frame = company_theme_scores.sort_values(["ticker", "theme", "year"]).copy()
    group_cols = ["ticker", "theme"]
    frame["prior_intensity"] = frame.groupby(group_cols)["theme_intensity"].shift(1)
    frame["priority_growth_rate"] = (
        (frame["theme_intensity"] - frame["prior_intensity"])
        / frame["prior_intensity"].replace(0, np.nan)
        * 100
    )
    frame["priority_growth_rate"] = frame["priority_growth_rate"].replace([np.inf, -np.inf], np.nan).fillna(0)
    frame["intensity_delta"] = frame["theme_intensity"] - frame["prior_intensity"].fillna(0)
    frame["prior_delta"] = frame.groupby(group_cols)["intensity_delta"].shift(1).fillna(0)
    frame["theme_acceleration"] = frame["intensity_delta"] - frame["prior_delta"]
    return frame


def calculate_momentum(company_theme_scores: pd.DataFrame) -> pd.DataFrame:
    """Estimate strategic momentum using slope, growth, and recency."""

    if company_theme_scores.empty:
        return pd.DataFrame(columns=["ticker", "company", "industry", "theme", "theme_momentum", "trend_slope"])

    frame = calculate_growth_rates(company_theme_scores)
    rows: list[dict[str, object]] = []
    max_year = pd.to_numeric(frame["year"], errors="coerce").max()
    for (ticker, theme), group in frame.groupby(["ticker", "theme"], dropna=False):
        group = group.sort_values("year")
        years = pd.to_numeric(group["year"], errors="coerce").fillna(max_year).to_numpy().reshape(-1, 1)
        intensity = group["theme_intensity"].fillna(0).to_numpy()
        if len(group) >= 2 and np.nanstd(years) > 0:
            slope = float(LinearRegression().fit(years, intensity).coef_[0])
        else:
            slope = float(group["intensity_delta"].iloc[-1]) if "intensity_delta" in group else 0.0
        latest = group.iloc[-1]
        recency_weight = 1.0 + max(float(latest["year"] - max_year), -3.0) * 0.08 if pd.notna(max_year) else 1.0
        raw_momentum = (
            0.50 * slope
            + 0.30 * float(latest["intensity_delta"])
            + 0.20 * (float(latest["priority_growth_rate"]) / 100)
        ) * recency_weight
        rows.append(
            {
                "ticker": ticker,
                "company": latest["company"],
                "industry": latest["industry"],
                "theme": theme,
                "year": latest["year"],
                "trend_slope": slope,
                "latest_intensity": float(latest["theme_intensity"]),
                "priority_growth_rate": float(latest["priority_growth_rate"]),
                "theme_acceleration": float(latest["theme_acceleration"]),
                "raw_momentum": raw_momentum,
            }
        )
    momentum = pd.DataFrame(rows)
    momentum["theme_momentum"] = min_max(momentum["raw_momentum"])
    return momentum


def industry_theme_trends(company_theme_scores: pd.DataFrame) -> pd.DataFrame:
    """Aggregate theme adoption and momentum by industry."""

    if company_theme_scores.empty:
        return pd.DataFrame(columns=["industry", "year", "theme", "theme_intensity", "company_count"])
    frame = company_theme_scores.copy()
    return (
        frame.groupby(["industry", "year", "theme"], dropna=False)
        .agg(
            theme_intensity=("theme_intensity", "mean"),
            company_count=("ticker", "nunique"),
            forward_looking_rate=("forward_looking_rate", "mean"),
            investment_rate=("investment_rate", "mean"),
            change_rate=("change_rate", "mean"),
        )
        .reset_index()
    )


def detect_emerging_themes(company_theme_scores: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Rank company-theme combinations with high recent acceleration."""

    momentum = calculate_momentum(company_theme_scores)
    if momentum.empty:
        return momentum
    momentum["emergence_score"] = min_max(
        0.45 * momentum["theme_momentum"]
        + 0.35 * min_max(momentum["priority_growth_rate"])
        + 0.20 * min_max(momentum["theme_acceleration"])
    )
    return momentum.sort_values("emergence_score", ascending=False).head(top_n)
