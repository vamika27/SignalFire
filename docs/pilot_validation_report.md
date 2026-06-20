# SignalFire Pilot Validation Report

## Scope

This report validates the current SignalFire **2-filing smoke test** output. It
is not a finished analysis and should not be interpreted as a complete strategic
market readout.

The goal was to confirm that the SEC pipeline can generate processed outputs,
that the generated files have basic data quality, and that the Streamlit
dashboard reads those processed outputs correctly.

## Commands Used

From the repository root:

```bash
python3 -m compileall signalfire
```

```bash
python3 -m signalfire.src.sec_pipeline --max-filings 2
```

```bash
streamlit run signalfire/dashboard/app.py
```

Additional validation command:

```bash
python3 - <<'PY'
from signalfire.dashboard.app import load_tables

tables = load_tables()
for name, frame in tables.items():
    print(f"{name}: {len(frame)}")
PY
```

## Files Generated

Generated files in `data/processed`:

| File | Rows |
| --- | ---: |
| `company_profiles.parquet` | 10 |
| `company_theme_scores.parquet` | 190 |
| `document_theme_scores.parquet` | 190 |
| `documents.parquet` | 19 |
| `entities.parquet` | 3,112 |
| `industry_trends.parquet` | 150 |
| `keywords.parquet` | 285 |
| `layoffs.parquet` | 0 |
| `priority_concentration.parquet` | 19 |
| `scorecard.parquet` | 100 |
| `sec_documents.parquet` | 19 |
| `signal_scores.parquet` | 10 |
| `signalfire.duckdb` | 14 tables |
| `tfidf_terms.parquet` | 1,425 |
| `theme_terms.parquet` | 172 |
| `topics.parquet` | 80 |

DuckDB tables:

| Table | Rows |
| --- | ---: |
| `company_profiles` | 10 |
| `company_theme_scores` | 190 |
| `document_theme_scores` | 190 |
| `documents` | 19 |
| `entities` | 3,112 |
| `industry_trends` | 150 |
| `keywords` | 285 |
| `layoffs` | 0 |
| `priority_concentration` | 19 |
| `scorecard` | 100 |
| `signal_scores` | 10 |
| `tfidf_terms` | 1,425 |
| `theme_terms` | 172 |
| `topics` | 80 |

## SEC Smoke Test Coverage

The smoke test requested up to two recent 10-K filings per default company.
Current output contains 19 SEC documents:

| Ticker | Company | Documents | Min report date | Max report date |
| --- | --- | ---: | --- | --- |
| AAPL | Apple | 2 | 2024-09-28 | 2025-09-27 |
| AMZN | Amazon | 2 | 2024-12-31 | 2025-12-31 |
| CRM | Salesforce | 2 | 2025-01-31 | 2026-01-31 |
| F | Ford Motor Company | 2 | 2024-12-31 | 2025-12-31 |
| JPM | JPMorgan Chase | 1 | 2025-12-31 | 2025-12-31 |
| MSFT | Microsoft | 2 | 2024-06-30 | 2025-06-30 |
| PFE | Pfizer | 2 | 2024-12-31 | 2025-12-31 |
| TGT | Target | 2 | 2025-02-01 | 2026-01-31 |
| WMT | Walmart | 2 | 2025-01-31 | 2026-01-31 |
| XOM | Exxon Mobil | 2 | 2024-12-31 | 2025-12-31 |

JPMorgan Chase returned one recent 10-K in this smoke run. No synthetic records
were added to force the count to 20.

## Data Quality Checks

### Missing company names

No missing company names were found in generated tables that contain company
fields:

- `company_profiles.parquet`: 0 missing `Company`
- `company_theme_scores.parquet`: 0 missing `company`
- `document_theme_scores.parquet`: 0 missing `company`
- `documents.parquet`: 0 missing `company`
- `entities.parquet`: 0 missing `company`
- `keywords.parquet`: 0 missing `company`
- `priority_concentration.parquet`: 0 missing `company`
- `scorecard.parquet`: 0 missing `company`
- `sec_documents.parquet`: 0 missing `company`
- `signal_scores.parquet`: 0 missing `company`
- `tfidf_terms.parquet`: 0 missing `company`

### Missing filing dates

No missing filing dates were found:

- `documents.parquet`: 0 missing `date`, 0 missing `filing_date`
- `sec_documents.parquet`: 0 missing `date`, 0 missing `filing_date`
- `document_theme_scores.parquet`: 0 missing `date`

### Empty theme scores

No missing or zero theme intensity scores were found in theme-scored tables:

- `company_theme_scores.parquet`: 0 missing, 0 zero
- `document_theme_scores.parquet`: 0 missing, 0 zero
- `industry_trends.parquet`: 0 missing, 0 zero
- `scorecard.parquet`: 0 missing, 0 zero

### Duplicate records

No exact duplicate rows were found in any generated parquet file.

Primary-key style checks:

- `documents.parquet`: 0 duplicate `document_id`
- `sec_documents.parquet`: 0 duplicate `document_id`
- `company_theme_scores.parquet`: 0 duplicate `ticker` + `theme` + `year`
- `scorecard.parquet`: 0 duplicate `ticker` + `theme`
- `scorecard.parquet`: 0 duplicate `ticker` + `theme` + `year`

Long-format tables such as `document_theme_scores.parquet` and
`keywords.parquet` intentionally repeat `document_id` because each document has
multiple themes and keywords. Those repeated document IDs are expected and are
not duplicate records.

### NaN / None values

After fixes, all generated parquet files report 0 total null values.

`layoffs.parquet` contains 0 rows with a stable schema (`company`, `date`). This
is expected for this SEC-only smoke test because no local Layoffs.fyi export was
provided and the public page did not expose a parseable table during validation.

## Dashboard Status

The dashboard reads from `data/processed/signalfire.duckdb` when available. The
current DuckDB file contains all tables required by the dashboard loader:

- `company_theme_scores`: 190 rows
- `scorecard`: 100 rows
- `signal_scores`: 10 rows
- `company_profiles`: 10 rows
- `industry_trends`: 150 rows
- `keywords`: 285 rows
- `entities`: 3,112 rows
- `topics`: 80 rows
- `theme_terms`: 172 rows
- `priority_concentration`: 19 rows

Page-level dependency checks passed:

- Executive Overview: required scorecard, signal score, and industry trend
  columns are present.
- Strategic Theme Explorer: theme trend and company comparison inputs are
  present.
- Company Intelligence: profile, company-theme history, and scorecard columns
  are present.
- Industry Intelligence: year, industry, theme, and intensity fields are
  present.
- Opportunity Radar: required priority themes and opportunity columns are
  present.
- Methodology: theme term table is present.

The command below launched successfully and served the app at
`http://localhost:8501`:

```bash
streamlit run signalfire/dashboard/app.py
```

## Issues Found

Two validation bugs were found and fixed:

1. `scorecard.parquet` contained 10 null `theme_volatility` values for
   company-theme pairs with only one observed filing year. The scorecard now
   fills single-observation volatility with `0`.
2. `signalfire.duckdb` retained a stale `scorecard_validation` table from a
   previous validation run. The DuckDB writer now rebuilds the database file for
   each pipeline run so only current pipeline tables remain.

No missing company names, missing filing dates, empty theme scores, exact
duplicate rows, or remaining NaN/None values were found after these fixes.

## Recommended Next Fixes

These are recommendations for future work, not changes made in this smoke-test
validation pass:

1. Add an automated validation script or test that reproduces these row-count,
   null, duplicate, and dashboard dependency checks.
2. Add a clearer run summary explaining why `--max-filings 2` can produce fewer
   than `2 x company_count` documents when SEC recent filing availability varies.
3. Add optional explicit CLI control for Layoffs.fyi ingestion so SEC-only smoke
   tests can skip the public layoffs lookup intentionally.
4. Add source evidence checks that verify every high-scoring theme can be traced
   back to document-level inputs before using the output for portfolio analysis.
