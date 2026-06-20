# SignalFire Product Strategy Brief

## Product Vision

SignalFire helps strategy teams detect corporate priorities before they become
obvious, turning public disclosures into a strategic opportunity radar for
consulting, market intelligence, product strategy, and investment research.

## Target Users

### Strategy Consultant

- Needs to identify accounts with emerging transformation demand.
- Wants evidence-backed themes for client conversations.
- Values concise executive summaries and drill-down support.

### Corporate Strategy Lead

- Tracks competitor moves and sector shifts.
- Needs early warning on technology, cost, supply chain, and workforce themes.
- Values industry benchmarks and trend direction.

### Market Intelligence Analyst

- Monitors public company disclosures at scale.
- Needs repeatable scoring and auditable methodology.
- Values exportable data tables and consistent taxonomy.

### Product Strategy Manager

- Wants to know which enterprise priorities are accelerating.
- Uses industry signals to shape roadmap bets and positioning.
- Values theme trends and account-level prioritization.

### Investor or Private Equity Analyst

- Evaluates transformation pressure and execution readiness.
- Needs company-level and sector-level signal comparison.
- Values risk, momentum, and opportunity scoring.

## User Pain Points

- Strategic shifts are recognized too late.
- Public filings and transcripts are too time-consuming to review manually.
- Existing dashboards show metrics but do not explain emerging priorities.
- Keyword counts are noisy and not credible for executive decision-making.
- Opportunity prioritization is often subjective and difficult to compare.

## Jobs to Be Done

1. When planning account coverage, help me find companies with rising
   transformation demand so I can prioritize outreach.
2. When monitoring a sector, help me see which themes are accelerating so I can
   update my market thesis.
3. When preparing a client briefing, help me explain what has changed with
   evidence from public disclosures.
4. When evaluating a company, help me distinguish strategic momentum from
   one-off language.
5. When sizing consulting opportunity, help me combine company change velocity,
   industry pressure, and organizational disruption.

## Product Requirements

### Data Requirements

- Ingest SEC 10-K filings through EDGAR APIs.
- Support earnings-call transcript CSV uploads.
- Support Layoffs.fyi table or CSV ingestion.
- Preserve source metadata and document IDs.
- Avoid synthetic data in shipped analytics outputs.

### Analytics Requirements

- Classify strategic themes.
- Extract TF-IDF keywords.
- Extract named entities.
- Run topic modeling.
- Detect trend direction and acceleration.
- Produce explainable company, theme, and industry scores.

### Dashboard Requirements

- Executive overview.
- Strategic theme explorer.
- Company intelligence profile.
- Industry intelligence heatmaps.
- Opportunity radar.
- Methodology page.

### Trust Requirements

- Document formulas.
- Show assumptions and limitations.
- Preserve auditable theme definitions.
- Make data-source requirements visible.

## MVP Definition

The MVP is a local Streamlit application that:

- Downloads real SEC 10-K filings for a default real-company universe.
- Accepts optional real earnings-call and layoffs datasets.
- Runs NLP classification, topic modeling, keyword extraction, NER, and trend
  detection.
- Produces company profiles, industry views, and consulting opportunity ranks.
- Stores outputs in parquet and DuckDB.
- Documents formulas and product thinking.

## Success Metrics

### User Value

- Time to identify top opportunity accounts.
- Number of credible company-theme insights generated per analysis session.
- Analyst confidence in score explainability.

### Product Engagement

- Companies monitored per workspace.
- Saved theme views.
- Exported account briefings.
- Repeat usage after new filings or transcripts.

### Model Quality

- Theme classification precision based on analyst review.
- Stability of scores across source updates.
- Evidence coverage per high-scoring theme.

### Business Impact

- Consulting pipeline influenced.
- Account plans created from SignalFire outputs.
- Competitive intelligence briefs produced.

## Roadmap

### MVP Plus

- Evidence snippets behind every score.
- CSV upload UI for transcripts and layoffs exports.
- Account shortlist export.
- Peer-group filters.

### SaaS Version

- Scheduled ingestion.
- Alerts for theme acceleration thresholds.
- Team workspaces and saved watchlists.
- Client-ready PDF briefs.
- API endpoints for BI tools.

### Advanced Intelligence

- O*NET and job-posting hiring alignment.
- Retrieval-augmented source citations.
- Sector-specific theme taxonomies.
- Event detection from investor days and product announcements.
- Scenario modeling for consulting demand.

## Risks

- Public disclosures lag actual internal priorities.
- SEC language can be boilerplate.
- External transcript and layoffs datasets may have licensing or coverage
  constraints.
- Theme scores can be overinterpreted without human review.
- Transformer-based topic modeling can be resource-intensive locally.

## Positioning

SignalFire is not a sentiment dashboard or text-mining toy. It is a strategic
forecasting workflow that converts disclosure language into business priorities,
transformation signals, and opportunity rankings.
