# SignalFire

**SignalFire** is a Strategic Intelligence Platform that identifies emerging
corporate priorities before they become obvious to investors, competitors, or
consulting firms.

The platform turns real public disclosures into company- and industry-level
signals about where transformation demand is likely building: AI, cloud,
cybersecurity, supply chain resilience, cost optimization, automation,
workforce transformation, digital transformation, and sustainability.

SignalFire is designed to feel like a product a strategy consulting firm,
corporate strategy team, competitive intelligence team, private equity team, or
market intelligence group could use to prioritize accounts and market theses.

## Business Problem

Organizations often react after a strategic shift is already priced into the
market. By the time a company announces an AI transformation, cloud migration,
cybersecurity investment, restructuring program, or automation initiative, the
best consulting and competitive-intelligence opportunities may already be
obvious.

Companies reveal direction earlier through subtle changes in:

- SEC 10-K risk, operations, and strategy language
- Earnings-call management narratives
- Restructuring and workforce disruption signals
- Industry-wide disclosure patterns

SignalFire detects these shifts and translates them into explainable business
scores.

## Strategic Importance

For consulting and strategy teams, early strategic momentum matters because it
helps answer:

- Which companies are likely to prioritize transformation next?
- Which themes are accelerating before they become consensus?
- Which industries are shifting fastest toward AI, automation, cost reduction,
  cloud modernization, or cyber resilience?
- Where are the highest-value consulting, implementation, and advisory
  opportunities emerging?

## Real Data Sources

SignalFire is built for real datasets only. It does not bundle synthetic
portfolio data.

Primary sources:

1. **SEC 10-K filings** through EDGAR APIs  
   <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>
2. **Motley Fool earnings-call transcripts** from Kaggle  
   <https://www.kaggle.com/datasets/tpotterer/motley-fool-scraped-earnings-call-transcripts>
3. **Layoffs.fyi** restructuring signals  
   <https://layoffs.fyi>

Optional enrichment:

- O*NET skills database for hiring/skills alignment  
  <https://www.onetcenter.org/database.html>

## Methodology

SignalFire uses a transparent NLP and scoring workflow:

1. **Ingest real company documents**
   - Download recent SEC 10-K filing text by ticker/CIK.
   - Load locally downloaded Kaggle earnings-call transcript CSVs.
   - Load Layoffs.fyi tables or CSV exports.

2. **Classify strategic themes**
   - Strategic themes are defined through auditable seed descriptions and terms.
   - TF-IDF n-gram vectors compare documents to theme definitions.
   - Scores are cosine similarities, not raw keyword counts.

3. **Extract strategic signals**
   - TF-IDF keyword extraction
   - Named entity recognition with spaCy
   - BERTopic topic modeling when available, with an NMF fallback
   - Forward-looking, investment, and transformation language scoring
   - Company-year and industry-year trend detection

4. **Score strategic opportunity**
   - Company-level profile
   - Theme momentum
   - Priority growth rate
   - Priority concentration
   - Consulting opportunity score
   - Transformation readiness score
   - Strategic risk score

## Key Metrics

### SignalFire Score

`30% Theme Intensity + 25% Theme Growth + 10% Hiring Alignment + 15% Organizational Signals + 20% Strategic Consistency`

### Consulting Opportunity Score

`35% Strategic Change Velocity + 25% Priority Growth + 20% Industry Transformation Pressure + 20% Organizational Disruption Signals`

### Transformation Readiness Score

`40% Strategic Consistency + 25% Source Breadth + 20% Theme Intensity + 15% Low Volatility`

### Company Intelligence Profile

Each company receives:

- Company
- Industry
- Dominant Strategic Theme
- Theme Momentum
- Emerging Theme
- Emerging Theme Growth Rate
- Consulting Opportunity Score
- Strategic Risk Score

## Dashboard Features

The Streamlit application includes six executive-grade pages:

1. **Executive Overview**
   - Top emerging themes
   - Fastest growing industries
   - Companies with highest momentum
   - Consulting opportunity leaders

2. **Strategic Theme Explorer**
   - Theme trends over time
   - Company comparisons
   - Current theme leaders

3. **Company Intelligence**
   - Interactive company profile
   - Historical theme evolution
   - Opportunity, momentum, and readiness gauges
   - Strategic risk scorecard

4. **Industry Intelligence**
   - Industry heatmaps
   - Theme penetration
   - Transformation trends

5. **Opportunity Radar**
   - Ranked opportunity views for AI, cloud, cybersecurity, supply chain, and
     cost optimization

6. **Methodology**
   - Formulas
   - Assumptions
   - Limitations
   - Auditable theme terms

## Running Locally

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

Set an SEC-compliant user agent:

```bash
export SIGNALFIRE_SEC_USER_AGENT="Your Name your.email@example.com"
```

Run the real-data pipeline:

```bash
python3 -m signalfire.src.sec_pipeline --max-filings 2
```

Optional transcript and layoffs inputs:

```bash
python3 -m signalfire.src.sec_pipeline \
  --max-filings 2 \
  --transcripts data/raw/motley_fool_transcripts.csv \
  --layoffs-source data/raw/layoffs.csv
```

Launch the dashboard:

```bash
streamlit run signalfire/dashboard/app.py
```

## Vercel Frontend Dashboard

SignalFire also includes a polished Next.js dashboard in `frontend/`. It reads
static JSON from `frontend/public/data`, generated from the existing real
processed outputs in `data/processed`.

Export frontend JSON:

```bash
python3 -m signalfire.src.export_frontend_data
```

Run the Next.js dashboard locally:

```bash
cd frontend
npm install
npm run dev
```

Build for production:

```bash
cd frontend
npm run build
```

Deploy to Vercel:

1. Push the repository to GitHub.
2. Create a new Vercel project.
3. Set the Vercel root directory to `frontend`.
4. Use the default commands:
   - Install command: `npm install`
   - Build command: `npm run build`
   - Output directory: Next.js default

Current frontend data is a smoke-test export, not a finished market-wide
analysis. No synthetic analytics data is used.

## Example Insights

When run on recent filings and transcripts, SignalFire is designed to surface
insights such as:

- Technology companies with accelerating generative AI language but rising
  cybersecurity risk exposure.
- Retailers increasing supply-chain resilience and cost-optimization language
  during margin pressure cycles.
- Financial services firms showing sustained cloud and cyber transformation
  language across filings and management commentary.
- Industries where restructuring signals and strategic language indicate rising
  demand for transformation advisory support.

## Project Structure

```text
signalfire/
  src/
    data_ingestion.py
    nlp_pipeline.py
    theme_classifier.py
    scoring.py
    trend_analysis.py
    visualizations.py
    pipeline.py
    sec_pipeline.py
    export_frontend_data.py
  dashboard/
    app.py
frontend/
  public/data/
  src/app/
notebooks/
  01_data_exploration.ipynb
  02_nlp_analysis.ipynb
  03_scoring_models.ipynb
docs/
  executive_summary.md
  product_brief.md
  methodology.md
  resume_bullets.md
data/
  raw/
  processed/
```

## Future Improvements

- Add O*NET and job-posting data to activate hiring alignment scores.
- Add company peer-group benchmarking and account planning exports.
- Incorporate conference presentations, investor-day transcripts, and product
  announcements.
- Add alerting for theme acceleration thresholds.
- Add retrieval-augmented evidence packs that cite document passages behind
  each score.
- Extend topic modeling with sector-specific taxonomies.
