"""NLP pipeline for SignalFire strategic intelligence."""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

from signalfire.src.theme_classifier import ThemeClassifier


TEXT_COLUMNS = ["document_id", "source", "ticker", "company", "industry", "date", "year", "text"]


@dataclass
class NLPArtifacts:
    document_theme_scores: pd.DataFrame
    company_theme_scores: pd.DataFrame
    tfidf_terms: pd.DataFrame
    keywords: pd.DataFrame
    entities: pd.DataFrame
    topics: pd.DataFrame
    theme_terms: pd.DataFrame


def prepare_documents(documents: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize document inputs."""

    missing = set(TEXT_COLUMNS).difference(documents.columns)
    missing.discard("year")
    if missing:
        raise ValueError(f"Documents missing required columns: {sorted(missing)}")

    docs = documents.copy()
    docs["date"] = pd.to_datetime(docs["date"], errors="coerce")
    docs["year"] = docs.get("year", docs["date"].dt.year)
    docs["text"] = docs["text"].fillna("").astype(str).map(clean_text)
    docs = docs.loc[docs["text"].str.len() > 500].reset_index(drop=True)
    return docs


def clean_text(text: str) -> str:
    """Normalize text while preserving business phrases."""

    text = re.sub(r"\s+", " ", str(text))
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return text.strip()


def extract_keywords(documents: pd.DataFrame, max_features: int = 5000, top_n: int = 15) -> pd.DataFrame:
    """Extract document-level keywords with TF-IDF weights."""

    if documents.empty:
        return pd.DataFrame(columns=["document_id", "ticker", "term", "rank", "tfidf_weight"])
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
        min_df=1,
        max_df=1.0,
        max_features=max_features,
    )
    matrix = vectorizer.fit_transform(documents["text"])
    terms = np.array(vectorizer.get_feature_names_out())
    rows: list[dict[str, object]] = []
    for row_idx, document_id in enumerate(documents["document_id"]):
        weights = matrix[row_idx].toarray().ravel()
        top_indices = np.argsort(weights)[::-1][:top_n]
        for rank, term_idx in enumerate(top_indices, start=1):
            if weights[term_idx] <= 0:
                continue
            rows.append(
                {
                    "document_id": document_id,
                    "ticker": documents.loc[row_idx, "ticker"],
                    "company": documents.loc[row_idx, "company"],
                    "term": terms[term_idx],
                    "rank": rank,
                    "tfidf_weight": float(weights[term_idx]),
                }
            )
    return pd.DataFrame(rows)


def corpus_tfidf_terms(documents: pd.DataFrame, top_n: int = 75) -> pd.DataFrame:
    """Return corpus-level TF-IDF terms by company and year."""

    if documents.empty:
        return pd.DataFrame(columns=["ticker", "company", "year", "term", "tfidf_weight"])

    grouped = (
        documents.groupby(["ticker", "company", "industry", "year"], dropna=False)["text"]
        .apply(" ".join)
        .reset_index()
    )
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 3), max_features=20_000, min_df=1)
    matrix = vectorizer.fit_transform(grouped["text"])
    terms = np.array(vectorizer.get_feature_names_out())
    rows: list[dict[str, object]] = []
    for row_idx, group in grouped.iterrows():
        weights = matrix[row_idx].toarray().ravel()
        top_indices = np.argsort(weights)[::-1][:top_n]
        for term_idx in top_indices:
            if weights[term_idx] <= 0:
                continue
            rows.append(
                {
                    "ticker": group["ticker"],
                    "company": group["company"],
                    "industry": group["industry"],
                    "year": group["year"],
                    "term": terms[term_idx],
                    "tfidf_weight": float(weights[term_idx]),
                }
            )
    return pd.DataFrame(rows)


def extract_named_entities(documents: pd.DataFrame, max_docs: int | None = None) -> pd.DataFrame:
    """Extract named entities with spaCy when a model is installed.

    Falls back to high-confidence organization-like capitalized phrases so the
    pipeline still runs in lightweight local environments.
    """

    docs = documents if max_docs is None else documents.head(max_docs)
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
        rows: list[dict[str, object]] = []
        if "ner" in nlp.pipe_names:
            for meta, parsed in zip(docs.to_dict("records"), nlp.pipe(docs["text"].str[:200_000]), strict=False):
                for entity in parsed.ents:
                    if entity.label_ in {"ORG", "PRODUCT", "GPE", "PERSON", "MONEY", "LAW"}:
                        rows.append(
                            {
                                "document_id": meta["document_id"],
                                "ticker": meta["ticker"],
                                "company": meta["company"],
                                "entity": entity.text.strip(),
                                "label": entity.label_,
                            }
                        )
            return _entity_counts(rows)
    except Exception:
        pass

    pattern = re.compile(r"\b(?:[A-Z][A-Za-z&.-]+(?:\s+|$)){2,4}")
    rows = []
    for _, row in docs.iterrows():
        matches = pattern.findall(row["text"][:200_000])
        for match in matches:
            entity = match.strip()
            if len(entity) < 4 or entity.lower().startswith("item "):
                continue
            rows.append(
                {
                    "document_id": row["document_id"],
                    "ticker": row["ticker"],
                    "company": row["company"],
                    "entity": entity,
                    "label": "PHRASE",
                }
            )
    return _entity_counts(rows)


def _entity_counts(rows: Iterable[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["ticker", "company", "entity", "label", "mentions"])
    return (
        frame.groupby(["ticker", "company", "entity", "label"], as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
        .sort_values("mentions", ascending=False)
    )


def topic_model(documents: pd.DataFrame, n_topics: int = 8, top_n: int = 10) -> pd.DataFrame:
    """Create explainable topics using NMF or opt-in BERTopic.

    Set SIGNALFIRE_TOPIC_MODEL=bertopic to use BERTopic. The NMF default keeps
    local runs fast and avoids implicit model downloads in constrained
    environments while still satisfying the same topic-table contract.
    """

    if documents.empty:
        return pd.DataFrame(columns=["topic_id", "term", "weight", "model"])

    texts = documents["text"].tolist()
    if os.getenv("SIGNALFIRE_TOPIC_MODEL", "nmf").lower() == "bertopic":
        try:
            from bertopic import BERTopic

            model = BERTopic(verbose=False, calculate_probabilities=False, min_topic_size=2)
            topics, _ = model.fit_transform(texts)
            rows: list[dict[str, object]] = []
            for topic_id in sorted(set(topics)):
                if topic_id == -1:
                    continue
                for term, weight in model.get_topic(topic_id)[:top_n]:
                    rows.append({"topic_id": topic_id, "term": term, "weight": float(weight), "model": "BERTopic"})
            if rows:
                return pd.DataFrame(rows)
        except Exception:
            pass

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=8000, min_df=1)
    matrix = vectorizer.fit_transform(texts)
    topic_count = max(1, min(n_topics, matrix.shape[0], matrix.shape[1] - 1))
    nmf = NMF(n_components=topic_count, init="nndsvda", random_state=42, max_iter=1000, tol=1e-3)
    nmf.fit(matrix)
    terms = np.array(vectorizer.get_feature_names_out())
    rows = []
    for topic_idx, components in enumerate(nmf.components_):
        for term_idx in np.argsort(components)[::-1][:top_n]:
            rows.append(
                {
                    "topic_id": topic_idx,
                    "term": terms[term_idx],
                    "weight": float(components[term_idx]),
                    "model": "NMF TF-IDF",
                }
            )
    return pd.DataFrame(rows)


def strategic_language_features(documents: pd.DataFrame) -> pd.DataFrame:
    """Score forward-looking, investment, and transformation language."""

    lexicons = {
        "forward_looking": [
            "expect",
            "intend",
            "plan",
            "priority",
            "strategy",
            "roadmap",
            "future",
            "accelerate",
        ],
        "investment": ["invest", "capital", "spend", "build", "launch", "expand", "platform", "capability"],
        "change": ["transform", "restructure", "modernize", "migration", "automation", "efficiency", "redesign"],
    }
    rows = []
    for _, row in documents.iterrows():
        tokens = re.findall(r"[a-zA-Z][a-zA-Z-]+", row["text"].lower())
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        feature_row = {
            "document_id": row["document_id"],
            "ticker": row["ticker"],
            "company": row["company"],
            "date": row["date"],
            "year": row["year"],
        }
        for feature, terms in lexicons.items():
            feature_row[f"{feature}_rate"] = sum(counts[term] for term in terms) / total
        rows.append(feature_row)
    return pd.DataFrame(rows)


def run_nlp_pipeline(documents: pd.DataFrame) -> NLPArtifacts:
    """Run theme classification, keyword extraction, NER, TF-IDF, and topics."""

    docs = prepare_documents(documents)
    classifier = ThemeClassifier().fit(docs["text"])
    document_theme_scores = classifier.score_documents(docs["text"], docs)
    language = strategic_language_features(docs)
    document_theme_scores = document_theme_scores.merge(
        language,
        on=["document_id", "ticker", "company", "date", "year"],
        how="left",
    )
    company_theme_scores = (
        document_theme_scores.groupby(["ticker", "company", "industry", "year", "theme"], dropna=False)
        .agg(
            theme_intensity=("theme_intensity", "mean"),
            source_count=("source", "nunique"),
            document_count=("document_id", "nunique"),
            forward_looking_rate=("forward_looking_rate", "mean"),
            investment_rate=("investment_rate", "mean"),
            change_rate=("change_rate", "mean"),
        )
        .reset_index()
    )

    return NLPArtifacts(
        document_theme_scores=document_theme_scores,
        company_theme_scores=company_theme_scores,
        tfidf_terms=corpus_tfidf_terms(docs),
        keywords=extract_keywords(docs),
        entities=extract_named_entities(docs),
        topics=topic_model(docs),
        theme_terms=classifier.top_terms_by_theme(),
    )
