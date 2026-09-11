"""Simple intent baselines with explicit label-file contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

FINAL_INTENTS = [
    "delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits",
    "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion",
    "website_app_or_technical_issue", "other_or_unclear",
]


class IntentModel(Protocol):
    def fit(self, texts: list[str], labels: list[str]) -> "IntentModel": ...
    def predict(self, texts: list[str]) -> list[str]: ...


@dataclass
class MajorityClassBaseline:
    label: str | None = None

    def fit(self, texts: list[str], labels: list[str]) -> "MajorityClassBaseline":
        if not labels:
            raise ValueError("Knowledge labels are empty")
        self.label = pd.Series(labels).value_counts().idxmax()
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if self.label is None:
            raise RuntimeError("Fit the baseline before prediction")
        return [self.label] * len(texts)


@dataclass
class TfidfLogisticBaseline:
    vectorizer: TfidfVectorizer | None = None
    classifier: LogisticRegression | None = None

    def fit(self, texts: list[str], labels: list[str]) -> "TfidfLogisticBaseline":
        if len(set(labels)) < 2:
            raise ValueError("TF-IDF logistic regression requires at least two Knowledge intent labels")
        self.vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=2, max_features=50_000)
        matrix = self.vectorizer.fit_transform(texts)
        self.classifier = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")
        self.classifier.fit(matrix, labels)
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if self.vectorizer is None or self.classifier is None:
            raise RuntimeError("Fit the baseline before prediction")
        return self.classifier.predict(self.vectorizer.transform(texts)).tolist()


def load_labeled_split(path: Path, label_column: str) -> tuple[list[str], list[str]]:
    """Load explicit human labels; never infer labels from golden or message keywords."""
    frame = pd.read_csv(path, dtype=str).fillna("")
    required = {"customer_message", label_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required label columns: {sorted(missing)}")
    labeled = frame[frame[label_column].isin(FINAL_INTENTS)]
    return labeled["customer_message"].tolist(), labeled[label_column].tolist()


def knowledge_label_path(root: Path) -> Path:
    return root / "data" / "processed" / "knowledge_labels.csv"


def build_baselines(root: Path) -> dict[str, IntentModel]:
    """Build baselines from an explicit, human-labelled Knowledge file."""
    path = knowledge_label_path(root)
    if not path.exists():
        raise FileNotFoundError(
            f"Knowledge labels are required at {path}. Create them independently from the golden set before evaluation."
        )
    texts, labels = load_labeled_split(path, "human_intent")
    return {
        "majority_class": MajorityClassBaseline().fit(texts, labels),
        "tfidf_logistic_regression": TfidfLogisticBaseline().fit(texts, labels),
    }
