# SignalFire Methodology

## Objective

SignalFire estimates emerging strategic priorities at the company and industry
level using real public data. The goal is to identify directional strategic
momentum, not to predict stock returns or replace human diligence.

## Data Inputs

### SEC 10-K Filings

The ingestion layer downloads recent 10-K filings through SEC EDGAR APIs using
company CIKs. Filings provide structured annual disclosure language around risk,
strategy, operations, investments, and transformation priorities.

### Earnings Call Transcripts

The pipeline accepts locally downloaded Motley Fool/Kaggle transcript CSVs.
Transcripts complement filings by capturing management commentary and evolving
priorities between annual reports.

### Layoffs.fyi

Layoffs.fyi data is used as an organizational disruption signal. Layoffs are not
interpreted as negative sentiment; they are treated as evidence of operating
model change, cost pressure, or restructuring activity.

## Strategic Theme Taxonomy

Default themes:

- Artificial Intelligence
- Generative AI
- Cloud Transformation
- Cybersecurity
- Supply Chain Resilience
- Cost Optimization
- Digital Transformation
- Automation
- Workforce Transformation
- Sustainability / ESG

New themes can be added by defining a `StrategicTheme` with a name, description,
and seed terms in `theme_classifier.py`.

## NLP Pipeline

### Theme Classification

SignalFire builds TF-IDF n-gram vectors across company documents and strategic
theme seed descriptions. Each document receives a cosine-similarity score
against every theme vector.

This approach is more explainable than black-box classification and more robust
than raw keyword counting because it uses weighted phrases and full theme
definitions.

### TF-IDF Analysis

The platform extracts document-level and company-year TF-IDF terms to show the
language driving each company's strategic profile.

### Keyword Extraction

For each document, the highest-weighted TF-IDF terms are retained for audit and
inspection.

### Named Entity Recognition

spaCy extracts organizations, products, geographies, people, laws, and monetary
references when an English model is installed. A phrase fallback is included for
lightweight local runs.

### Topic Modeling

BERTopic is used when available. If transformer topic modeling cannot run in a
local environment, the pipeline uses NMF over TF-IDF features so topic discovery
remains reproducible.

### Strategic Language Scoring

Documents are scored for forward-looking, investment, and change language using
auditable lexicons normalized by document length.

## Core Metrics

### Strategic Priority Score

Measures how important a theme appears for a company.

Formula:

`45% Theme Intensity + 20% Strategic Consistency + 15% Source Breadth + 20% Growth`

### Strategic Momentum Score

Measures whether a theme is accelerating.

Components:

- Trend slope across available years
- Latest intensity delta
- Priority growth rate
- Recency adjustment

### Priority Growth Rate

Year-over-year percentage change in company-theme intensity.

Formula:

`(Current Intensity - Prior Intensity) / Prior Intensity`

### Priority Concentration

Measures whether a company is focused around a few priorities or spread across
many themes.

Formula:

`sum(theme_share^2)` for each company-year.

### SignalFire Score

Composite company-level strategic signal.

Formula:

`30% Theme Intensity + 25% Theme Growth + 10% Hiring Alignment + 15% Organizational Signals + 20% Strategic Consistency`

Hiring alignment is reserved for O*NET/job-posting enrichment and defaults to
zero unless a real hiring dataset is integrated.

### Consulting Opportunity Score

Ranks where advisory and transformation demand is likely emerging.

Formula:

`35% Strategic Change Velocity + 25% Priority Growth + 20% Industry Transformation Pressure + 20% Organizational Disruption Signals`

### Transformation Readiness Score

Estimates whether a company appears prepared to execute on a theme.

Formula:

`40% Strategic Consistency + 25% Source Breadth + 20% Theme Intensity + 15% Low Volatility`

### Strategic Risk Score

Highlights potential transformation risk.

Formula:

`45% Organizational Disruption + 30% Readiness Gap + 25% Theme Volatility`

## Assumptions

- Public disclosures contain meaningful signals about management priorities.
- Language intensity and growth are directional proxies for strategic focus.
- Industry-level averages provide useful transformation-pressure benchmarks.
- Layoffs and restructuring signals can indicate opportunity as well as risk.

## Limitations

- SEC filings are lagging and legally constrained.
- Earnings-call availability depends on external data access.
- Layoffs.fyi coverage varies by company and reporting date.
- The model is explainable but not causal.
- Scores should guide diligence, not replace expert judgment.
