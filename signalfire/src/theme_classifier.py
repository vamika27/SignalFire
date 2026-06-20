"""Explainable strategic theme classification.

SignalFire classifies strategy language with a hybrid approach:

1. Theme seed descriptions define the business meaning of each priority.
2. TF-IDF n-gram features compare company documents to those seed descriptions.
3. Optional transformer embeddings can be layered in by downstream users without
   changing the theme taxonomy or score schema.

The output is not a raw keyword count. Scores are cosine similarities between
documents and theme definitions, with top contributing terms retained for audit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class StrategicTheme:
    name: str
    description: str
    seed_terms: tuple[str, ...]

    @property
    def seed_document(self) -> str:
        return " ".join((self.description, *self.seed_terms))


DEFAULT_THEMES: tuple[StrategicTheme, ...] = (
    StrategicTheme(
        "Artificial Intelligence",
        "Enterprise adoption of machine learning, predictive models, AI platforms, responsible AI, and AI-enabled products.",
        (
            "artificial intelligence",
            "machine learning",
            "predictive analytics",
            "model governance",
            "ai platform",
            "data science",
            "neural network",
        ),
    ),
    StrategicTheme(
        "Generative AI",
        "Use of foundation models, large language models, copilots, content generation, and generative automation.",
        (
            "generative ai",
            "large language model",
            "foundation model",
            "copilot",
            "prompt engineering",
            "chatgpt",
            "content generation",
        ),
    ),
    StrategicTheme(
        "Cloud Transformation",
        "Migration of infrastructure, applications, data platforms, and operating models to cloud-native environments.",
        (
            "cloud migration",
            "cloud computing",
            "hybrid cloud",
            "cloud native",
            "data platform",
            "software as a service",
            "infrastructure modernization",
        ),
    ),
    StrategicTheme(
        "Cybersecurity",
        "Cyber resilience, identity protection, threat detection, data security, privacy controls, and regulatory security posture.",
        (
            "cybersecurity",
            "cyber security",
            "information security",
            "ransomware",
            "identity access",
            "zero trust",
            "data privacy",
        ),
    ),
    StrategicTheme(
        "Supply Chain Resilience",
        "Resilience, localization, inventory strategy, logistics redesign, supplier risk, and operational continuity.",
        (
            "supply chain",
            "supplier risk",
            "logistics",
            "inventory optimization",
            "resilience",
            "nearshoring",
            "procurement",
        ),
    ),
    StrategicTheme(
        "Cost Optimization",
        "Efficiency programs, margin expansion, restructuring, productivity, operating leverage, and cost takeout.",
        (
            "cost reduction",
            "cost optimization",
            "operating efficiency",
            "margin expansion",
            "restructuring",
            "productivity",
            "expense management",
        ),
    ),
    StrategicTheme(
        "Digital Transformation",
        "Digitization of customer journeys, business models, operating workflows, products, and enterprise platforms.",
        (
            "digital transformation",
            "digital platform",
            "omnichannel",
            "customer experience",
            "digital commerce",
            "technology modernization",
            "digital capabilities",
        ),
    ),
    StrategicTheme(
        "Automation",
        "Workflow automation, robotics, process redesign, intelligent automation, and software-enabled productivity.",
        (
            "automation",
            "robotic process automation",
            "autonomous systems",
            "workflow automation",
            "process automation",
            "robotics",
            "intelligent automation",
        ),
    ),
    StrategicTheme(
        "Workforce Transformation",
        "Workforce redesign, reskilling, talent strategy, organizational change, hybrid work, and capability building.",
        (
            "workforce transformation",
            "reskilling",
            "upskilling",
            "talent strategy",
            "organizational change",
            "hybrid work",
            "employee experience",
        ),
    ),
    StrategicTheme(
        "Sustainability / ESG",
        "Climate transition, carbon reduction, sustainability reporting, ESG governance, and energy efficiency.",
        (
            "sustainability",
            "esg",
            "carbon emissions",
            "net zero",
            "renewable energy",
            "climate risk",
            "energy transition",
        ),
    ),
)


class ThemeClassifier:
    """TF-IDF similarity classifier for strategic priorities."""

    def __init__(self, themes: tuple[StrategicTheme, ...] = DEFAULT_THEMES) -> None:
        self.themes = themes
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 3),
            min_df=1,
            max_features=60_000,
        )
        self._theme_matrix = None
        self._feature_names: np.ndarray | None = None

    @property
    def theme_names(self) -> list[str]:
        return [theme.name for theme in self.themes]

    def fit(self, documents: pd.Series | list[str]) -> "ThemeClassifier":
        corpus = [theme.seed_document for theme in self.themes] + [str(doc) for doc in documents]
        matrix = self.vectorizer.fit_transform(corpus)
        self._theme_matrix = matrix[: len(self.themes)]
        self._feature_names = self.vectorizer.get_feature_names_out()
        return self

    def score_documents(self, documents: pd.Series | list[str], metadata: pd.DataFrame | None = None) -> pd.DataFrame:
        if self._theme_matrix is None:
            self.fit(documents)
        doc_matrix = self.vectorizer.transform([str(doc) for doc in documents])
        similarities = cosine_similarity(doc_matrix, self._theme_matrix)
        scores = pd.DataFrame(similarities, columns=self.theme_names)
        scores = scores.melt(ignore_index=False, var_name="theme", value_name="theme_intensity").reset_index()
        scores = scores.rename(columns={"index": "row_id"})
        if metadata is not None:
            metadata = metadata.reset_index(drop=True).reset_index(names="row_id")
            passthrough = [
                column
                for column in ["document_id", "source", "ticker", "company", "industry", "date", "year"]
                if column in metadata.columns
            ]
            scores = scores.merge(metadata[["row_id", *passthrough]], on="row_id", how="left")
        scores["theme_intensity"] = scores["theme_intensity"].clip(lower=0)
        return scores

    def top_terms_by_theme(self, top_n: int = 20) -> pd.DataFrame:
        if self._theme_matrix is None or self._feature_names is None:
            raise RuntimeError("ThemeClassifier must be fitted before extracting terms.")
        rows: list[dict[str, object]] = []
        for theme_idx, theme in enumerate(self.themes):
            vector = self._theme_matrix[theme_idx].toarray().ravel()
            top_indices = np.argsort(vector)[::-1][:top_n]
            for rank, feature_idx in enumerate(top_indices, start=1):
                if vector[feature_idx] <= 0:
                    continue
                rows.append(
                    {
                        "theme": theme.name,
                        "rank": rank,
                        "term": self._feature_names[feature_idx],
                        "weight": float(vector[feature_idx]),
                    }
                )
        return pd.DataFrame(rows)


def add_theme(theme: StrategicTheme, existing: tuple[StrategicTheme, ...] = DEFAULT_THEMES) -> tuple[StrategicTheme, ...]:
    """Return a taxonomy with an additional theme appended."""

    if any(current.name == theme.name for current in existing):
        raise ValueError(f"Theme already exists: {theme.name}")
    return (*existing, theme)
