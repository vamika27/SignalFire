"""Real-data ingestion utilities for SignalFire.

The module intentionally does not ship synthetic records. It can download
public SEC filing text, ingest locally downloaded Kaggle earnings transcripts,
and read Layoffs.fyi tables or exports when available.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SEC_RAW_DIR = RAW_DIR / "sec_filings"


@dataclass(frozen=True)
class CompanySeed:
    """A real public company included in the default watchlist."""

    ticker: str
    company: str
    cik: str
    industry: str


DEFAULT_COMPANIES: tuple[CompanySeed, ...] = (
    CompanySeed("MSFT", "Microsoft", "0000789019", "Technology"),
    CompanySeed("AMZN", "Amazon", "0001018724", "Consumer Discretionary"),
    CompanySeed("AAPL", "Apple", "0000320193", "Technology"),
    CompanySeed("WMT", "Walmart", "0000104169", "Consumer Staples"),
    CompanySeed("JPM", "JPMorgan Chase", "0000019617", "Financial Services"),
    CompanySeed("F", "Ford Motor Company", "0000037996", "Industrials"),
    CompanySeed("PFE", "Pfizer", "0000078003", "Healthcare"),
    CompanySeed("XOM", "Exxon Mobil", "0000034088", "Energy"),
    CompanySeed("TGT", "Target", "0000027419", "Consumer Discretionary"),
    CompanySeed("CRM", "Salesforce", "0001108524", "Technology"),
)


SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{document}"


def _sec_headers() -> dict[str, str]:
    """Return SEC-compliant request headers.

    Users should set SIGNALFIRE_SEC_USER_AGENT to a string containing a contact
    email. SEC requests may be throttled or rejected without a descriptive agent.
    """

    user_agent = os.getenv(
        "SIGNALFIRE_SEC_USER_AGENT",
        "SignalFire portfolio research contact@example.com",
    )
    return {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}


def normalize_cik(cik: str | int) -> str:
    """Return a ten-digit CIK string."""

    return str(cik).strip().zfill(10)


def clean_sec_text(raw_html: str) -> str:
    """Convert SEC filing HTML or plain text into normalized readable text."""

    soup = BeautifulSoup(raw_html, "html.parser")
    for element in soup(["script", "style", "table"]):
        element.decompose()
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)table of contents.*?item 1\.", "Item 1.", text)
    return text.strip()


def get_company_universe(path: Path | None = None) -> pd.DataFrame:
    """Load a user company universe or return the curated real-company default."""

    if path and path.exists():
        frame = pd.read_csv(path)
        required = {"ticker", "company", "cik", "industry"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Company universe missing columns: {sorted(missing)}")
        frame["cik"] = frame["cik"].map(normalize_cik)
        return frame

    return pd.DataFrame([seed.__dict__ for seed in DEFAULT_COMPANIES])


def fetch_sec_submission_index(cik: str) -> dict:
    """Fetch the SEC submissions JSON index for a company CIK."""

    cik = normalize_cik(cik)
    response = requests.get(SEC_SUBMISSIONS_URL.format(cik=cik), headers=_sec_headers(), timeout=30)
    response.raise_for_status()
    time.sleep(0.11)
    return response.json()


def _recent_filings(index: dict, form: str = "10-K", limit: int = 3) -> list[dict[str, str]]:
    """Extract recent filings metadata from an SEC submissions index."""

    recent = index.get("filings", {}).get("recent", {})
    rows: list[dict[str, str]] = []
    forms = recent.get("form", [])
    for idx, filing_form in enumerate(forms):
        if filing_form != form:
            continue
        rows.append(
            {
                "accession_number": recent["accessionNumber"][idx],
                "filing_date": recent["filingDate"][idx],
                "report_date": recent["reportDate"][idx],
                "primary_document": recent["primaryDocument"][idx],
                "form": filing_form,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def fetch_sec_filing_text(cik: str, accession_number: str, primary_document: str) -> str:
    """Download a single SEC filing document and return cleaned text."""

    cik_norm = normalize_cik(cik)
    accession = accession_number.replace("-", "")
    url = SEC_ARCHIVE_URL.format(
        cik_int=int(cik_norm),
        accession=accession,
        document=primary_document,
    )
    response = requests.get(url, headers=_sec_headers(), timeout=60)
    response.raise_for_status()
    time.sleep(0.11)
    return clean_sec_text(response.text)


def download_sec_10k_filings(
    companies: pd.DataFrame | None = None,
    max_filings_per_company: int = 3,
    raw_dir: Path = SEC_RAW_DIR,
) -> pd.DataFrame:
    """Download recent 10-K filing text for real companies.

    Returns a document-level DataFrame and writes raw text plus metadata to
    data/raw/sec_filings. Existing raw text files are reused.
    """

    companies = companies if companies is not None else get_company_universe()
    raw_dir.mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, object]] = []

    for _, company in companies.iterrows():
        cik = normalize_cik(company["cik"])
        index = fetch_sec_submission_index(cik)
        filings = _recent_filings(index, limit=max_filings_per_company)
        for filing in filings:
            accession = filing["accession_number"]
            safe_accession = accession.replace("-", "")
            text_path = raw_dir / f"{company['ticker']}_{safe_accession}.txt"
            meta_path = raw_dir / f"{company['ticker']}_{safe_accession}.json"
            if text_path.exists():
                text = text_path.read_text(encoding="utf-8")
            else:
                text = fetch_sec_filing_text(cik, accession, filing["primary_document"])
                text_path.write_text(text, encoding="utf-8")
                meta_path.write_text(
                    json.dumps({**company.to_dict(), **filing}, indent=2),
                    encoding="utf-8",
                )

            documents.append(
                {
                    "document_id": f"sec_{company['ticker']}_{safe_accession}",
                    "source": "SEC 10-K",
                    "ticker": company["ticker"],
                    "company": company["company"],
                    "cik": cik,
                    "industry": company["industry"],
                    "date": filing["report_date"] or filing["filing_date"],
                    "filing_date": filing["filing_date"],
                    "text": text,
                    "url": SEC_ARCHIVE_URL.format(
                        cik_int=int(cik),
                        accession=safe_accession,
                        document=filing["primary_document"],
                    ),
                }
            )

    frame = pd.DataFrame(documents)
    if not frame.empty:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(PROCESSED_DIR / "sec_documents.parquet", index=False)
    return frame


def load_earnings_transcripts(paths: Iterable[Path]) -> pd.DataFrame:
    """Load real Motley Fool/Kaggle earnings-call transcript exports.

    Expected columns are flexible. The loader looks for company/ticker/date/text
    aliases commonly present in Kaggle transcript exports.
    """

    aliases = {
        "ticker": ["ticker", "symbol"],
        "company": ["company", "company_name", "name"],
        "date": ["date", "call_date", "quarter_date"],
        "text": ["transcript", "content", "text"],
    }
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        rename: dict[str, str] = {}
        lowercase_columns = {column.lower(): column for column in frame.columns}
        for canonical, options in aliases.items():
            for option in options:
                if option in lowercase_columns:
                    rename[lowercase_columns[option]] = canonical
                    break
        frame = frame.rename(columns=rename)
        required = {"ticker", "date", "text"}
        if not required.issubset(frame.columns):
            raise ValueError(f"{path} missing transcript columns: {sorted(required - set(frame.columns))}")
        if "company" not in frame.columns:
            frame["company"] = frame["ticker"]
        frame["source"] = "Earnings Call"
        frame["document_id"] = "earnings_" + frame["ticker"].astype(str) + "_" + frame.index.astype(str)
        frames.append(frame[["document_id", "source", "ticker", "company", "date", "text"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_layoffs(path_or_url: str | Path | None = None) -> pd.DataFrame:
    """Load Layoffs.fyi data from a local CSV or public HTML table."""

    empty = pd.DataFrame(columns=["company", "date"])
    if path_or_url is None:
        path_or_url = os.getenv("SIGNALFIRE_LAYOFFS_SOURCE", "https://layoffs.fyi")
    source = str(path_or_url)
    if Path(source).exists():
        frame = pd.read_csv(source)
    else:
        try:
            tables = pd.read_html(source)
        except (ImportError, ValueError):
            return empty
        if not tables:
            return empty
        frame = tables[0]

    normalized = {column: re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_") for column in frame.columns}
    frame = frame.rename(columns=normalized)
    if "company" not in frame.columns:
        return empty
    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame


def combine_documents(sec_documents: pd.DataFrame, transcripts: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    """Combine document sources and enrich with industry metadata."""

    frames = [frame for frame in (sec_documents, transcripts) if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame(
            columns=["document_id", "source", "ticker", "company", "industry", "date", "text"]
        )
    docs = pd.concat(frames, ignore_index=True, sort=False)
    docs["ticker"] = docs["ticker"].astype(str).str.upper()
    docs = docs.merge(companies[["ticker", "industry"]], on="ticker", how="left", suffixes=("", "_seed"))
    if "industry_seed" in docs.columns:
        docs["industry"] = docs["industry"].fillna(docs.pop("industry_seed"))
    elif "industry" not in docs.columns:
        docs["industry"] = "Unknown"
    docs["industry"] = docs["industry"].fillna("Unknown")
    docs["date"] = pd.to_datetime(docs["date"], errors="coerce")
    docs["year"] = docs["date"].dt.year
    docs["text"] = docs["text"].fillna("").astype(str)
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest real SignalFire datasets.")
    parser.add_argument("--company-universe", type=Path, help="CSV with ticker, company, cik, industry")
    parser.add_argument("--max-filings", type=int, default=2, help="Recent 10-K filings per company")
    parser.add_argument("--transcripts", type=Path, nargs="*", default=[], help="Local Kaggle transcript CSVs")
    parser.add_argument("--skip-sec", action="store_true", help="Skip SEC download")
    args = parser.parse_args()

    companies = get_company_universe(args.company_universe)
    sec_docs = pd.DataFrame()
    if not args.skip_sec:
        sec_docs = download_sec_10k_filings(companies, args.max_filings)
    transcripts = load_earnings_transcripts(args.transcripts)
    documents = combine_documents(sec_docs, transcripts, companies)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "documents.parquet"
    documents.to_parquet(output_path, index=False)
    print(f"Wrote {len(documents):,} real documents to {output_path}")
    print(f"Completed at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()
