"""Export processed SignalFire outputs for the static Next.js frontend.

The exporter reads existing real analytics outputs from data/processed and
writes frontend-ready JSON files to frontend/public/data. It does not run or
modify the analytics pipeline.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FRONTEND_DATA_DIR = PROJECT_ROOT / "frontend" / "public" / "data"

THEME_ORDER = [
    "Artificial Intelligence",
    "Generative AI",
    "Cloud Transformation",
    "Cybersecurity",
    "Supply Chain Resilience",
    "Cost Optimization",
    "Digital Transformation",
    "Automation",
    "Workforce Transformation",
    "Sustainability / ESG",
]


def _read_table(name: str, processed_dir: Path) -> pd.DataFrame:
    path = processed_dir / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing processed table: {path}. Run python3 -m signalfire.src.sec_pipeline --max-filings 2 first."
        )
    return pd.read_parquet(path)


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 4)
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{key: _clean_value(value) for key, value in row.items()} for row in frame.to_dict("records")]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _latest_processed_timestamp(processed_dir: Path) -> str:
    files = [path for path in processed_dir.glob("*.parquet") if path.is_file()]
    if not files:
        return datetime.now(timezone.utc).isoformat()
    timestamp = max(path.stat().st_mtime for path in files)
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def build_executive_summary(tables: dict[str, pd.DataFrame], processed_dir: Path) -> dict[str, Any]:
    documents = tables["documents"]
    scorecard = tables["scorecard"]
    signal_scores = tables["signal_scores"]
    company_theme_scores = tables["company_theme_scores"]

    theme_summary = (
        scorecard.groupby("theme", as_index=False)
        .agg(
            avg_momentum=("strategic_momentum_score", "mean"),
            avg_opportunity=("consulting_opportunity_score", "mean"),
            top_company=("company", "first"),
        )
        .sort_values(["avg_momentum", "avg_opportunity"], ascending=False)
    )
    top_theme = theme_summary.iloc[0]
    opportunity_leader = scorecard.sort_values("consulting_opportunity_score", ascending=False).iloc[0]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "lastPipelineRun": _latest_processed_timestamp(processed_dir),
        "scope": "2-filing SEC smoke test",
        "dataSource": "SEC EDGAR 10-K filings",
        "kpis": {
            "companiesAnalyzed": int(signal_scores["ticker"].nunique()),
            "secDocumentsProcessed": int(documents["document_id"].nunique()),
            "topEmergingTheme": str(top_theme["theme"]),
            "highestConsultingOpportunityScore": round(float(opportunity_leader["consulting_opportunity_score"]), 1),
            "themeScoresGenerated": int(len(company_theme_scores)),
            "lastPipelineRun": _latest_processed_timestamp(processed_dir),
        },
        "topTheme": {
            "theme": str(top_theme["theme"]),
            "averageMomentum": round(float(top_theme["avg_momentum"]), 1),
            "averageOpportunity": round(float(top_theme["avg_opportunity"]), 1),
        },
        "opportunityLeader": {
            "company": str(opportunity_leader["company"]),
            "industry": str(opportunity_leader["industry"]),
            "theme": str(opportunity_leader["theme"]),
            "consultingOpportunityScore": round(float(opportunity_leader["consulting_opportunity_score"]), 1),
            "signalFireScore": round(
                float(
                    signal_scores.loc[
                        signal_scores["ticker"].eq(opportunity_leader["ticker"]),
                        "signal_fire_score",
                    ].max()
                ),
                1,
            ),
            "strategicRiskScore": round(float(opportunity_leader["strategic_risk_score"]), 1),
        },
        "brief": {
            "situation": "Public companies disclose strategic priorities before those shifts are fully visible in financial performance.",
            "signal": (
                f"The current SEC smoke test identifies {top_theme['theme']} as the strongest emerging theme "
                f"by average momentum across the processed company-theme scorecard."
            ),
            "implication": "The output is useful for validating the product workflow and interaction model, not for broad market conclusions yet.",
            "recommendedNextRead": "Review the Opportunity Radar and company briefing sheets, then expand coverage before using results for portfolio-level analysis.",
        },
        "coverage": _records(
            documents.groupby(["ticker", "company"], as_index=False)
            .agg(documents=("document_id", "nunique"), minDate=("date", "min"), maxDate=("date", "max"))
            .sort_values("ticker")
        ),
    }


def build_company_profiles(tables: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    profiles = tables["company_profiles"].rename(
        columns={
            "Company": "company",
            "Industry": "industry",
            "Dominant Strategic Theme": "dominantTheme",
            "Theme Momentum": "themeMomentum",
            "Consulting Opportunity Score": "consultingOpportunityScore",
            "Strategic Risk Score": "strategicRiskScore",
            "Emerging Theme": "emergingTheme",
            "Emerging Theme Growth Rate": "emergingThemeGrowthRate",
        }
    )
    scorecard = tables["scorecard"]
    signal_scores = tables["signal_scores"]
    keywords = tables["keywords"]
    company_theme_scores = tables["company_theme_scores"]

    rows: list[dict[str, Any]] = []
    for profile in profiles.to_dict("records"):
        company = profile["company"]
        company_scorecard = scorecard.loc[scorecard["company"].eq(company)].copy()
        company_signal = signal_scores.loc[signal_scores["company"].eq(company)].head(1)
        top_keywords = (
            keywords.loc[keywords["company"].eq(company)]
            .sort_values(["rank", "tfidf_weight"], ascending=[True, False])
            .drop_duplicates("term")
            .head(10)["term"]
            .tolist()
        )
        evolution = (
            company_theme_scores.loc[company_theme_scores["company"].eq(company)]
            .sort_values(["year", "theme"])
            [["year", "theme", "theme_intensity"]]
        )
        rows.append(
            {
                **{key: _clean_value(value) for key, value in profile.items()},
                "ticker": str(company_scorecard["ticker"].iloc[0]) if not company_scorecard.empty else None,
                "signalFireScore": round(float(company_signal["signal_fire_score"].iloc[0]), 1)
                if not company_signal.empty
                else None,
                "readinessScore": round(float(company_scorecard["transformation_readiness_score"].max()), 1)
                if not company_scorecard.empty
                else None,
                "topKeywords": top_keywords,
                "themeEvolution": _records(evolution),
            }
        )
    return rows


def build_scorecard(tables: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    return _records(tables["scorecard"].sort_values("consulting_opportunity_score", ascending=False))


def build_theme_trends(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    company_theme_scores = tables["company_theme_scores"]
    scorecard = tables["scorecard"]
    theme_rows = []
    for theme in THEME_ORDER:
        theme_scorecard = scorecard.loc[scorecard["theme"].eq(theme)]
        theme_history = company_theme_scores.loc[company_theme_scores["theme"].eq(theme)]
        if theme_scorecard.empty:
            continue
        top_row = theme_scorecard.sort_values("strategic_momentum_score", ascending=False).iloc[0]
        trend = (
            theme_history.groupby("year", as_index=False)
            .agg(themeIntensity=("theme_intensity", "mean"))
            .sort_values("year")
        )
        theme_rows.append(
            {
                "theme": theme,
                "score": round(float(theme_scorecard["strategic_momentum_score"].mean()), 1),
                "topCompany": str(top_row["company"]),
                "topCompanyScore": round(float(top_row["strategic_momentum_score"]), 1),
                "averageOpportunity": round(float(theme_scorecard["consulting_opportunity_score"].mean()), 1),
                "signal": (
                    f"{top_row['company']} is the highest-momentum company for {theme} in the current SEC smoke test."
                ),
                "trend": _records(trend),
            }
        )
    return {
        "themes": theme_rows,
        "companyThemeScores": _records(company_theme_scores.sort_values(["theme", "company", "year"])),
    }


def build_industry_trends(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    industry_trends = tables["industry_trends"]
    fastest = (
        industry_trends.groupby("industry", as_index=False)
        .agg(avgIntensity=("theme_intensity", "mean"), companyCount=("company_count", "max"))
        .sort_values("avgIntensity", ascending=False)
    )
    return {"rows": _records(industry_trends), "fastestIndustries": _records(fastest)}


def build_opportunity_radar(tables: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    scorecard = tables["scorecard"]
    signal_scores = tables["signal_scores"][["ticker", "signal_fire_score"]]
    profiles = tables["company_profiles"].rename(
        columns={"Company": "company", "Dominant Strategic Theme": "dominantTheme"}
    )[["company", "dominantTheme"]]
    radar = (
        scorecard.merge(signal_scores, on="ticker", how="left")
        .merge(profiles, on="company", how="left")
        .sort_values("consulting_opportunity_score", ascending=False)
        .reset_index(drop=True)
    )
    radar["rank"] = radar.index + 1
    radar["explanation"] = radar.apply(
        lambda row: (
            f"{row['company']} ranks highly because its {row['theme']} signal combines "
            f"momentum ({row['strategic_momentum_score']:.1f}), priority growth "
            f"({row['priority_growth_rate']:.1f}%), and industry pressure "
            f"({row['industry_transformation_pressure']:.1f})."
        ),
        axis=1,
    )
    return _records(
        radar[
            [
                "rank",
                "ticker",
                "company",
                "industry",
                "theme",
                "dominantTheme",
                "consulting_opportunity_score",
                "signal_fire_score",
                "strategic_risk_score",
                "strategic_momentum_score",
                "transformation_readiness_score",
                "priority_growth_rate",
                "explanation",
            ]
        ]
    )


def build_keywords(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    keywords = tables["keywords"]
    by_company = {}
    for company, group in keywords.groupby("company"):
        by_company[company] = group.sort_values(["rank", "tfidf_weight"], ascending=[True, False]).head(12)[
            ["term", "rank", "tfidf_weight"]
        ].pipe(_records)
    global_terms = (
        keywords.groupby("term", as_index=False)
        .agg(weight=("tfidf_weight", "mean"), companies=("company", "nunique"))
        .sort_values(["companies", "weight"], ascending=False)
        .head(40)
    )
    return {"byCompany": by_company, "globalTerms": _records(global_terms)}


def build_methodology(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    return {
        "flow": [
            {"step": 1, "title": "SEC 10-K ingestion", "description": "Download recent real SEC EDGAR 10-K filings for the watchlist."},
            {"step": 2, "title": "Text cleaning", "description": "Normalize filing text and remove noisy HTML artifacts."},
            {"step": 3, "title": "NLP theme classification", "description": "Score documents against auditable strategic theme definitions."},
            {"step": 4, "title": "TF-IDF / keyword extraction", "description": "Extract high-weighted terms that help explain each company profile."},
            {"step": 5, "title": "Strategic scoring", "description": "Calculate momentum, opportunity, readiness, and risk scores."},
            {"step": 6, "title": "Company intelligence profiles", "description": "Summarize dominant and emerging themes by company."},
            {"step": 7, "title": "Opportunity radar", "description": "Rank company-theme pairs for consulting opportunity review."},
        ],
        "formulas": [
            {
                "name": "SignalFire Score",
                "formula": "30% Theme Intensity + 25% Theme Growth + 10% Hiring Alignment + 15% Organizational Signals + 20% Strategic Consistency",
            },
            {
                "name": "Consulting Opportunity Score",
                "formula": "35% Strategic Change Velocity + 25% Priority Growth + 20% Industry Transformation Pressure + 20% Organizational Disruption Signals",
            },
            {
                "name": "Strategic Risk Score",
                "formula": "45% Organizational Disruption + 30% Readiness Gap + 25% Theme Volatility",
            },
        ],
        "themeTerms": _records(tables["theme_terms"]),
        "limitations": [
            "Current version uses real SEC EDGAR filings from a 2-filing smoke test.",
            "This is not a finished market-wide study.",
            "Scores are derived analytical constructs, not company-reported metrics.",
            "No synthetic analytics data is used.",
        ],
    }


def export_frontend_data(processed_dir: Path = PROCESSED_DIR, output_dir: Path = FRONTEND_DATA_DIR) -> dict[str, int]:
    tables = {
        "documents": _read_table("documents", processed_dir),
        "company_profiles": _read_table("company_profiles", processed_dir),
        "scorecard": _read_table("scorecard", processed_dir),
        "company_theme_scores": _read_table("company_theme_scores", processed_dir),
        "industry_trends": _read_table("industry_trends", processed_dir),
        "keywords": _read_table("keywords", processed_dir),
        "theme_terms": _read_table("theme_terms", processed_dir),
        "signal_scores": _read_table("signal_scores", processed_dir),
    }
    payloads = {
        "executive_summary.json": build_executive_summary(tables, processed_dir),
        "company_profiles.json": build_company_profiles(tables),
        "scorecard.json": build_scorecard(tables),
        "theme_trends.json": build_theme_trends(tables),
        "industry_trends.json": build_industry_trends(tables),
        "opportunity_radar.json": build_opportunity_radar(tables),
        "keywords.json": build_keywords(tables),
        "methodology.json": build_methodology(tables),
    }
    counts: dict[str, int] = {}
    for filename, payload in payloads.items():
        _write_json(output_dir / filename, payload)
        if isinstance(payload, list):
            counts[filename] = len(payload)
        elif isinstance(payload, dict):
            counts[filename] = len(payload)
        else:
            counts[filename] = 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Export processed SignalFire data to frontend JSON.")
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=FRONTEND_DATA_DIR)
    args = parser.parse_args()

    counts = export_frontend_data(args.processed_dir, args.output_dir)
    print(f"Exported frontend JSON to {args.output_dir}")
    for filename, count in counts.items():
        print(f"- {filename}: {count}")


if __name__ == "__main__":
    main()
