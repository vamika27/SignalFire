"""Explainable strategic scoring models for SignalFire."""

from __future__ import annotations

import numpy as np
import pandas as pd

from signalfire.src.trend_analysis import calculate_momentum, industry_theme_trends, min_max


def _safe_latest(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.sort_values("year").groupby(group_cols, as_index=False, dropna=False).tail(1)


def calculate_priority_concentration(company_theme_scores: pd.DataFrame) -> pd.DataFrame:
    """Calculate how concentrated each company's theme portfolio is."""

    if company_theme_scores.empty:
        return pd.DataFrame(columns=["ticker", "year", "priority_concentration"])
    frame = company_theme_scores.copy()
    totals = frame.groupby(["ticker", "year"], dropna=False)["theme_intensity"].transform("sum").replace(0, np.nan)
    frame["theme_share"] = frame["theme_intensity"] / totals
    concentration = (
        frame.groupby(["ticker", "company", "industry", "year"], dropna=False)["theme_share"]
        .apply(lambda values: float(np.square(values.fillna(0)).sum()))
        .reset_index(name="priority_concentration")
    )
    concentration["priority_concentration_score"] = min_max(concentration["priority_concentration"])
    return concentration


def calculate_disruption_signals(layoffs: pd.DataFrame | None) -> pd.DataFrame:
    """Summarize organizational disruption from Layoffs.fyi data."""

    if layoffs is None or layoffs.empty or "company" not in layoffs.columns:
        return pd.DataFrame(columns=["company", "organizational_disruption_score", "layoff_events"])

    frame = layoffs.copy()
    number_cols = [column for column in frame.columns if "laid" in column or "number" in column or "total" in column]
    if number_cols:
        frame["layoff_volume"] = pd.to_numeric(
            frame[number_cols[0]].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0)
    else:
        frame["layoff_volume"] = 1
    disruption = (
        frame.groupby("company", as_index=False)
        .agg(layoff_events=("company", "size"), layoff_volume=("layoff_volume", "sum"))
    )
    disruption["organizational_disruption_score"] = min_max(
        0.6 * disruption["layoff_events"] + 0.4 * min_max(disruption["layoff_volume"])
    )
    return disruption[["company", "organizational_disruption_score", "layoff_events"]]


def build_company_theme_scorecard(
    company_theme_scores: pd.DataFrame,
    layoffs: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create theme-level strategic, momentum, and opportunity scores."""

    if company_theme_scores.empty:
        return pd.DataFrame()

    frame = company_theme_scores.copy()
    momentum = calculate_momentum(frame)
    latest = _safe_latest(frame, ["ticker", "theme"])
    scorecard = latest.merge(
        momentum[
            [
                "ticker",
                "theme",
                "theme_momentum",
                "trend_slope",
                "priority_growth_rate",
                "theme_acceleration",
            ]
        ],
        on=["ticker", "theme"],
        how="left",
    )

    industry = industry_theme_trends(frame)
    industry_latest = _safe_latest(industry, ["industry", "theme"])
    industry_latest["industry_transformation_pressure"] = min_max(industry_latest["theme_intensity"])
    scorecard = scorecard.merge(
        industry_latest[["industry", "theme", "industry_transformation_pressure"]],
        on=["industry", "theme"],
        how="left",
    )

    disruption = calculate_disruption_signals(layoffs)
    scorecard = scorecard.merge(disruption, on="company", how="left")
    scorecard["organizational_disruption_score"] = scorecard["organizational_disruption_score"].fillna(0)
    scorecard["layoff_events"] = scorecard["layoff_events"].fillna(0)

    scorecard["theme_intensity_score"] = min_max(scorecard["theme_intensity"])
    scorecard["growth_score"] = min_max(scorecard["priority_growth_rate"])
    scorecard["hiring_alignment_score"] = 0.0
    scorecard["strategic_consistency_score"] = min_max(
        scorecard["forward_looking_rate"].fillna(0)
        + scorecard["investment_rate"].fillna(0)
        + scorecard["change_rate"].fillna(0)
    )
    scorecard["source_breadth_score"] = min_max(scorecard["source_count"].fillna(0))

    scorecard["strategic_priority_score"] = (
        0.45 * scorecard["theme_intensity_score"]
        + 0.20 * scorecard["strategic_consistency_score"]
        + 0.15 * scorecard["source_breadth_score"]
        + 0.20 * scorecard["growth_score"]
    ).round(1)

    scorecard["strategic_momentum_score"] = (
        0.55 * scorecard["theme_momentum"].fillna(0)
        + 0.30 * scorecard["growth_score"].fillna(0)
        + 0.15 * min_max(scorecard["theme_acceleration"].fillna(0))
    ).round(1)

    scorecard["consulting_opportunity_score"] = (
        0.35 * scorecard["strategic_momentum_score"].fillna(0)
        + 0.25 * scorecard["growth_score"].fillna(0)
        + 0.20 * scorecard["industry_transformation_pressure"].fillna(0)
        + 0.20 * scorecard["organizational_disruption_score"].fillna(0)
    ).round(1)

    volatility = (
        frame.groupby(["ticker", "theme"], dropna=False)["theme_intensity"]
        .std()
        .reset_index(name="theme_volatility")
    )
    scorecard = scorecard.merge(volatility, on=["ticker", "theme"], how="left")
    scorecard["transformation_readiness_score"] = (
        0.40 * scorecard["strategic_consistency_score"].fillna(0)
        + 0.25 * scorecard["source_breadth_score"].fillna(0)
        + 0.20 * scorecard["theme_intensity_score"].fillna(0)
        + 0.15 * (100 - min_max(scorecard["theme_volatility"].fillna(0)))
    ).round(1)

    scorecard["strategic_risk_score"] = (
        0.45 * scorecard["organizational_disruption_score"].fillna(0)
        + 0.30 * (100 - scorecard["transformation_readiness_score"].fillna(0))
        + 0.25 * min_max(scorecard["theme_volatility"].fillna(0))
    ).round(1)
    return scorecard.sort_values("consulting_opportunity_score", ascending=False)


def build_company_profiles(scorecard: pd.DataFrame) -> pd.DataFrame:
    """Create the Company Intelligence Profile table."""

    if scorecard.empty:
        return pd.DataFrame(
            columns=[
                "Company",
                "Industry",
                "Dominant Strategic Theme",
                "Theme Momentum",
                "Emerging Theme",
                "Emerging Theme Growth Rate",
                "Consulting Opportunity Score",
                "Strategic Risk Score",
            ]
        )

    dominant = scorecard.sort_values("strategic_priority_score", ascending=False).groupby("ticker").head(1)
    emerging = scorecard.sort_values("strategic_momentum_score", ascending=False).groupby("ticker").head(1)
    profiles = dominant[
        [
            "ticker",
            "company",
            "industry",
            "theme",
            "strategic_momentum_score",
            "consulting_opportunity_score",
            "strategic_risk_score",
        ]
    ].rename(
        columns={
            "company": "Company",
            "industry": "Industry",
            "theme": "Dominant Strategic Theme",
            "strategic_momentum_score": "Theme Momentum",
            "consulting_opportunity_score": "Consulting Opportunity Score",
            "strategic_risk_score": "Strategic Risk Score",
        }
    )
    emerging = emerging[["ticker", "theme", "priority_growth_rate"]].rename(
        columns={"theme": "Emerging Theme", "priority_growth_rate": "Emerging Theme Growth Rate"}
    )
    profiles = profiles.merge(emerging, on="ticker", how="left").drop(columns=["ticker"])
    return profiles.sort_values("Consulting Opportunity Score", ascending=False)


def build_signal_fire_scores(scorecard: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SignalFire Score at company level."""

    if scorecard.empty:
        return pd.DataFrame()
    ranked = scorecard.copy()
    ranked["signal_fire_score"] = (
        0.30 * ranked["theme_intensity_score"].fillna(0)
        + 0.25 * ranked["growth_score"].fillna(0)
        + 0.10 * ranked["hiring_alignment_score"].fillna(0)
        + 0.15 * ranked["organizational_disruption_score"].fillna(0)
        + 0.20 * ranked["strategic_consistency_score"].fillna(0)
    ).round(1)
    return (
        ranked.groupby(["ticker", "company", "industry"], as_index=False)
        .agg(
            signal_fire_score=("signal_fire_score", "max"),
            consulting_opportunity_score=("consulting_opportunity_score", "max"),
            strategic_momentum_score=("strategic_momentum_score", "max"),
            strategic_priority_score=("strategic_priority_score", "max"),
            transformation_readiness_score=("transformation_readiness_score", "max"),
            strategic_risk_score=("strategic_risk_score", "max"),
        )
        .sort_values("signal_fire_score", ascending=False)
    )
