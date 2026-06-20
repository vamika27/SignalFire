"""SignalFire Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signalfire.src.visualizations import (  # noqa: E402
    company_theme_area,
    industry_heatmap,
    opportunity_scatter,
    score_gauge,
    theme_trend_line,
    top_bar,
)


PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = PROCESSED_DIR / "signalfire.duckdb"


st.set_page_config(
    page_title="SignalFire | Strategic Intelligence Platform",
    page_icon="🔥",
    layout="wide",
)


CSS = """
<style>
    .main { background: #F8FAFC; }
    h1, h2, h3 { color: #0B1320; }
    .sf-hero {
        padding: 1.5rem 1.75rem;
        border-radius: 1.25rem;
        background: linear-gradient(135deg, #0B1320 0%, #14213D 55%, #FF6B35 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .sf-hero h1 { color: white; margin-bottom: .2rem; }
    .sf-card {
        padding: 1rem 1.1rem;
        border: 1px solid #EAECF0;
        border-radius: 1rem;
        background: white;
        box-shadow: 0 1px 2px rgba(16, 24, 40, .05);
    }
    .sf-muted { color: #667085; font-size: .95rem; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #EAECF0;
        border-radius: 1rem;
        padding: 1rem;
    }
</style>
"""


@st.cache_data(show_spinner=False)
def load_tables() -> dict[str, pd.DataFrame]:
    """Load SignalFire analytics tables from DuckDB or parquet."""

    table_names = [
        "company_theme_scores",
        "scorecard",
        "signal_scores",
        "company_profiles",
        "industry_trends",
        "keywords",
        "entities",
        "topics",
        "theme_terms",
        "priority_concentration",
    ]
    tables: dict[str, pd.DataFrame] = {}
    if DB_PATH.exists():
        with duckdb.connect(str(DB_PATH), read_only=True) as con:
            for table in table_names:
                try:
                    tables[table] = con.execute(f"SELECT * FROM {table}").df()
                except duckdb.CatalogException:
                    tables[table] = pd.DataFrame()
    else:
        for table in table_names:
            path = PROCESSED_DIR / f"{table}.parquet"
            tables[table] = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    return tables


def render_header() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sf-hero">
            <h1>SignalFire</h1>
            <div>Strategic Intelligence Platform for detecting emerging corporate priorities before they become obvious.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.warning("No processed real-data assets were found.")
    st.markdown(
        """
        SignalFire does not ship synthetic portfolio data. Generate local analytics from real sources:

        ```bash
        export SIGNALFIRE_SEC_USER_AGENT="Your Name your.email@example.com"
        python -m signalfire.src.pipeline --max-filings 2
        streamlit run signalfire/dashboard/app.py
        ```

        Optional real datasets:
        - Motley Fool earnings transcripts from Kaggle: pass CSV files with `--transcripts`.
        - Layoffs.fyi export or public table: pass `--layoffs-source`.
        """
    )


def metric_row(scorecard: pd.DataFrame, signal_scores: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies tracked", f"{signal_scores['ticker'].nunique():,}" if not signal_scores.empty else "0")
    col2.metric("Strategic themes", f"{scorecard['theme'].nunique():,}" if not scorecard.empty else "0")
    col3.metric(
        "Avg opportunity score",
        f"{scorecard['consulting_opportunity_score'].mean():.1f}" if not scorecard.empty else "0",
    )
    col4.metric(
        "High-momentum signals",
        f"{(scorecard['strategic_momentum_score'] >= 70).sum():,}" if not scorecard.empty else "0",
    )


def executive_overview(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Executive Overview")
    scorecard = tables["scorecard"]
    signal_scores = tables["signal_scores"]
    industry = tables["industry_trends"]
    metric_row(scorecard, signal_scores)

    left, right = st.columns(2)
    with left:
        themes = (
            scorecard.groupby("theme", as_index=False)
            .agg(
                avg_momentum=("strategic_momentum_score", "mean"),
                avg_opportunity=("consulting_opportunity_score", "mean"),
            )
            .assign(theme_label=lambda frame: frame["theme"])
            .nlargest(8, "avg_momentum")
        )
        st.plotly_chart(top_bar(themes, "avg_momentum", "theme_label", "Top emerging themes"), width="stretch")
    with right:
        leaders = scorecard.nlargest(8, "consulting_opportunity_score")
        st.plotly_chart(
            top_bar(leaders, "consulting_opportunity_score", "company", "Consulting opportunity leaders", "strategic_momentum_score"),
            width="stretch",
        )

    left, right = st.columns(2)
    with left:
        industry_growth = (
            industry.groupby("industry", as_index=False)["theme_intensity"]
            .mean()
            .nlargest(8, "theme_intensity")
        )
        st.plotly_chart(
            top_bar(industry_growth, "theme_intensity", "industry", "Fastest shifting industries"),
            width="stretch",
        )
    with right:
        momentum = signal_scores.nlargest(8, "strategic_momentum_score")
        st.dataframe(
            momentum[
                [
                    "company",
                    "industry",
                    "signal_fire_score",
                    "strategic_momentum_score",
                    "consulting_opportunity_score",
                ]
            ],
            hide_index=True,
            width="stretch",
        )


def theme_explorer(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Strategic Theme Explorer")
    scores = tables["company_theme_scores"]
    scorecard = tables["scorecard"]
    themes = sorted(scores["theme"].dropna().unique())
    companies = sorted(scores["company"].dropna().unique())
    col1, col2 = st.columns([1, 2])
    theme = col1.selectbox("Theme", themes)
    selected_companies = col2.multiselect("Compare companies", companies, default=companies[: min(4, len(companies))])
    st.plotly_chart(theme_trend_line(scores, theme, selected_companies), width="stretch")
    st.markdown("#### Current leaders")
    st.dataframe(
        scorecard.loc[scorecard["theme"].eq(theme)]
        .nlargest(15, "strategic_priority_score")[
            [
                "company",
                "industry",
                "strategic_priority_score",
                "strategic_momentum_score",
                "priority_growth_rate",
                "consulting_opportunity_score",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def company_intelligence(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Company Intelligence")
    profiles = tables["company_profiles"]
    scores = tables["company_theme_scores"]
    scorecard = tables["scorecard"]
    company = st.selectbox("Company", sorted(scorecard["company"].dropna().unique()))
    company_card = scorecard.loc[scorecard["company"].eq(company)].sort_values(
        "consulting_opportunity_score", ascending=False
    )
    profile = profiles.loc[profiles["Company"].eq(company)].head(1)

    if not profile.empty:
        row = profile.iloc[0]
        st.markdown(
            f"""
            <div class="sf-card">
                <h3>{row['Company']}</h3>
                <div class="sf-muted">{row['Industry']}</div>
                <p><b>Dominant Theme:</b> {row['Dominant Strategic Theme']} &nbsp; | &nbsp;
                <b>Emerging Theme:</b> {row['Emerging Theme']} &nbsp; | &nbsp;
                <b>Emerging Growth:</b> {row['Emerging Theme Growth Rate']:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)
    top_row = company_card.iloc[0]
    with col1:
        st.plotly_chart(score_gauge(top_row["consulting_opportunity_score"], "Opportunity"), width="stretch")
    with col2:
        st.plotly_chart(score_gauge(top_row["strategic_momentum_score"], "Momentum"), width="stretch")
    with col3:
        st.plotly_chart(score_gauge(top_row["transformation_readiness_score"], "Readiness"), width="stretch")

    st.plotly_chart(company_theme_area(scores, company), width="stretch")
    st.markdown("#### Theme scorecard")
    st.dataframe(
        company_card[
            [
                "theme",
                "strategic_priority_score",
                "strategic_momentum_score",
                "priority_growth_rate",
                "consulting_opportunity_score",
                "strategic_risk_score",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def industry_intelligence(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Industry Intelligence")
    industry = tables["industry_trends"]
    years = sorted(industry["year"].dropna().unique())
    selected_year = st.selectbox("Year", years, index=len(years) - 1)
    st.plotly_chart(industry_heatmap(industry, selected_year), width="stretch")

    st.markdown("#### Theme penetration by industry")
    st.dataframe(
        industry.loc[industry["year"].eq(selected_year)]
        .sort_values("theme_intensity", ascending=False)
        .head(30),
        hide_index=True,
        width="stretch",
    )


def opportunity_radar(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Opportunity Radar")
    scorecard = tables["scorecard"]
    priority_themes = [
        "Artificial Intelligence",
        "Cloud Transformation",
        "Cybersecurity",
        "Supply Chain Resilience",
        "Cost Optimization",
    ]
    theme = st.selectbox("Rank opportunity by theme", priority_themes)
    st.plotly_chart(opportunity_scatter(scorecard, theme), width="stretch")
    st.dataframe(
        scorecard.loc[scorecard["theme"].eq(theme)]
        .nlargest(25, "consulting_opportunity_score")[
            [
                "company",
                "industry",
                "strategic_priority_score",
                "strategic_momentum_score",
                "priority_growth_rate",
                "industry_transformation_pressure",
                "organizational_disruption_score",
                "consulting_opportunity_score",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def methodology(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Methodology")
    st.markdown(
        """
        ### Data foundation
        SignalFire ingests real SEC 10-K filings through the SEC EDGAR APIs, optional Motley Fool
        earnings-call transcript CSVs from Kaggle, and optional Layoffs.fyi tables or exports.

        ### NLP workflow
        - **Theme classification:** TF-IDF n-gram similarity between source documents and auditable strategic-theme definitions.
        - **Topic modeling:** BERTopic when available, with NMF TF-IDF fallback for lightweight local runs.
        - **Keyword extraction:** document and company-year TF-IDF terms.
        - **Named entity recognition:** spaCy NER when `en_core_web_sm` is installed; phrase fallback otherwise.
        - **Strategic language scoring:** forward-looking, investment, and change lexicons normalized by document length.

        ### SignalFire Score
        `30% Theme Intensity + 25% Theme Growth + 10% Hiring Alignment + 15% Organizational Signals + 20% Strategic Consistency`

        Hiring alignment is reserved for O*NET/job-posting enrichment and defaults to zero unless integrated.

        ### Consulting Opportunity Score
        `35% Strategic Change Velocity + 25% Priority Growth + 20% Industry Transformation Pressure + 20% Organizational Disruption Signals`

        ### Transformation Readiness Score
        `40% Strategic Consistency + 25% Source Breadth + 20% Theme Intensity + 15% Low Volatility`

        ### Limitations
        - Public disclosures lag internal strategy.
        - SEC language is legally constrained and may understate early experimentation.
        - Layoff data coverage varies by company and date.
        - Theme scores are directional indicators, not investment recommendations.
        """
    )

    terms = tables["theme_terms"]
    if not terms.empty:
        st.markdown("#### Auditable theme seed terms")
        st.dataframe(terms.head(100), hide_index=True, width="stretch")


def main() -> None:
    render_header()
    tables = load_tables()
    scorecard = tables.get("scorecard", pd.DataFrame())
    if scorecard.empty:
        render_empty_state()
        methodology(tables)
        return

    page = st.sidebar.radio(
        "Navigate",
        [
            "Executive Overview",
            "Strategic Theme Explorer",
            "Company Intelligence",
            "Industry Intelligence",
            "Opportunity Radar",
            "Methodology",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Built from real public disclosures. No synthetic data is bundled.")

    if page == "Executive Overview":
        executive_overview(tables)
    elif page == "Strategic Theme Explorer":
        theme_explorer(tables)
    elif page == "Company Intelligence":
        company_intelligence(tables)
    elif page == "Industry Intelligence":
        industry_intelligence(tables)
    elif page == "Opportunity Radar":
        opportunity_radar(tables)
    else:
        methodology(tables)


if __name__ == "__main__":
    main()
