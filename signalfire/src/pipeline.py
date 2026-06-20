"""End-to-end SignalFire analytics pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from signalfire.src.data_ingestion import (
    PROCESSED_DIR,
    combine_documents,
    download_sec_10k_filings,
    get_company_universe,
    load_earnings_transcripts,
    load_layoffs,
)
from signalfire.src.nlp_pipeline import run_nlp_pipeline
from signalfire.src.scoring import (
    build_company_profiles,
    build_company_theme_scorecard,
    build_signal_fire_scores,
    calculate_priority_concentration,
)
from signalfire.src.trend_analysis import industry_theme_trends


def write_table(frame: pd.DataFrame, name: str, processed_dir: Path = PROCESSED_DIR) -> Path:
    """Persist a DataFrame as parquet."""

    processed_dir.mkdir(parents=True, exist_ok=True)
    path = processed_dir / f"{name}.parquet"
    frame.to_parquet(path, index=False)
    return path


def write_duckdb(tables: dict[str, pd.DataFrame], db_path: Path = PROCESSED_DIR / "signalfire.duckdb") -> Path:
    """Write analytics outputs to a DuckDB file."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with duckdb.connect(str(db_path)) as con:
        for name, frame in tables.items():
            con.register(f"{name}_df", frame)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM {name}_df")
            con.unregister(f"{name}_df")
    return db_path


def run_pipeline(
    company_universe: Path | None = None,
    transcripts: list[Path] | None = None,
    layoffs_source: str | Path | None = None,
    max_filings: int = 2,
    skip_sec: bool = False,
) -> dict[str, pd.DataFrame]:
    """Run the full SignalFire workflow on real data sources."""

    companies = get_company_universe(company_universe)
    sec_docs = pd.DataFrame()
    if not skip_sec:
        sec_docs = download_sec_10k_filings(companies=companies, max_filings_per_company=max_filings)
    transcript_docs = load_earnings_transcripts(transcripts or [])
    documents = combine_documents(sec_docs, transcript_docs, companies)
    if documents.empty:
        raise RuntimeError(
            "No real documents available. Download SEC filings or provide Kaggle earnings transcript CSVs."
        )

    layoffs = load_layoffs(layoffs_source)
    artifacts = run_nlp_pipeline(documents)
    scorecard = build_company_theme_scorecard(artifacts.company_theme_scores, layoffs)
    signal_scores = build_signal_fire_scores(scorecard)
    profiles = build_company_profiles(scorecard)
    concentration = calculate_priority_concentration(artifacts.company_theme_scores)
    industry_trends = industry_theme_trends(artifacts.company_theme_scores)

    tables = {
        "documents": documents.drop(columns=["text"]).copy(),
        "document_theme_scores": artifacts.document_theme_scores,
        "company_theme_scores": artifacts.company_theme_scores,
        "tfidf_terms": artifacts.tfidf_terms,
        "keywords": artifacts.keywords,
        "entities": artifacts.entities,
        "topics": artifacts.topics,
        "theme_terms": artifacts.theme_terms,
        "scorecard": scorecard,
        "signal_scores": signal_scores,
        "company_profiles": profiles,
        "priority_concentration": concentration,
        "industry_trends": industry_trends,
        "layoffs": layoffs,
    }
    for name, frame in tables.items():
        write_table(frame, name)
    write_duckdb(tables)
    return tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SignalFire end-to-end.")
    parser.add_argument("--company-universe", type=Path, help="CSV with ticker, company, cik, industry")
    parser.add_argument("--transcripts", type=Path, nargs="*", default=[], help="Local Kaggle transcript CSVs")
    parser.add_argument("--layoffs-source", help="Layoffs.fyi URL or local CSV")
    parser.add_argument("--max-filings", type=int, default=2)
    parser.add_argument("--skip-sec", action="store_true")
    args = parser.parse_args()

    tables = run_pipeline(
        company_universe=args.company_universe,
        transcripts=args.transcripts,
        layoffs_source=args.layoffs_source,
        max_filings=args.max_filings,
        skip_sec=args.skip_sec,
    )
    print("SignalFire pipeline complete.")
    for name, frame in tables.items():
        print(f"- {name}: {len(frame):,} rows")


if __name__ == "__main__":
    main()
