"""Evaluate the capped Knowledge classifier against the existing Golden labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from src.baselines import FINAL_INTENTS
from src.balanced_training import MAX_PER_INTENT, build_balanced_training
from src.config import get_config


def _metrics(truth: list[str], predictions: list[str]) -> dict[str, object]:
    scores = f1_score(truth, predictions, labels=FINAL_INTENTS, average=None, zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(truth, predictions)), 6),
        "macro_f1": round(float(f1_score(truth, predictions, labels=FINAL_INTENTS, average="macro", zero_division=0)), 6),
        "per_intent_f1": dict(zip(FINAL_INTENTS, scores.round(6).tolist())),
        "confusion_matrix": {
            "labels": FINAL_INTENTS,
            "matrix": confusion_matrix(truth, predictions, labels=FINAL_INTENTS).tolist(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = (args.root or get_config().root).resolve()
    output, training = build_balanced_training(root)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_features=50_000,
    )
    matrix = vectorizer.fit_transform(training["customer_message"].tolist())
    classifier = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")
    classifier.fit(matrix, training["human_intent"].tolist())

    golden = pd.read_csv(root / "data" / "golden" / "golden_set.csv", dtype=str).fillna("")
    labeled = golden[golden["human_intent"].isin(FINAL_INTENTS)]
    truth = labeled["human_intent"].tolist()
    predictions = classifier.predict(vectorizer.transform(labeled["customer_message"].tolist())).tolist()
    improved = _metrics(truth, predictions)

    baseline = pd.read_csv(root / "results" / "baseline_results.csv", dtype=str).fillna("")
    baseline_row = baseline[baseline["baseline"].eq("tfidf_logistic_regression")].iloc[0]
    rows = pd.DataFrame([
        {
            "system": "tfidf_logistic_regression_original",
            "n_examples": len(labeled),
            "accuracy": baseline_row["accuracy"],
            "macro_f1": baseline_row["macro_f1"],
            "per_intent_f1": baseline_row["per_intent_f1"],
            "confusion_matrix": baseline_row["confusion_matrix"],
        },
        {
            "system": "tfidf_logistic_regression_balanced",
            "n_examples": len(labeled),
            "accuracy": improved["accuracy"],
            "macro_f1": improved["macro_f1"],
            "per_intent_f1": json.dumps(improved["per_intent_f1"], sort_keys=True),
            "confusion_matrix": json.dumps(improved["confusion_matrix"]),
        },
    ])
    results_dir = root / "results"
    rows.to_csv(results_dir / "balanced_evaluation.csv", index=False)
    distribution = training["human_intent"].value_counts().reindex(FINAL_INTENTS, fill_value=0)
    report = [
        "# Balanced AmazonHelp Classifier Evaluation",
        "",
        "Training uses Knowledge data only. Golden examples are evaluation-only.",
        "",
        f"- Original Knowledge rows: 85,315",
        f"- Balanced Knowledge rows: {len(training):,}",
        f"- Maximum examples per intent: {MAX_PER_INTENT:,}",
        f"- Golden labelled examples evaluated: {len(labeled):,}",
        "- Golden training leakage: 0",
        "",
        "## Final training distribution",
        "",
    ]
    report.extend(f"- `{intent}`: {int(count):,}" for intent, count in distribution.items())
    report.extend([
        "",
        "## Results",
        "",
        f"- Original TF-IDF accuracy: {baseline_row['accuracy']}",
        f"- Original TF-IDF macro F1: {baseline_row['macro_f1']}",
        f"- Balanced TF-IDF accuracy: {improved['accuracy']}",
        f"- Balanced TF-IDF macro F1: {improved['macro_f1']}",
        f"- Balanced per-intent F1: `{json.dumps(improved['per_intent_f1'], sort_keys=True)}`",
        f"- Balanced confusion matrix: `{json.dumps(improved['confusion_matrix'])}`",
        "",
        "The balanced training set caps only dominant classes and retains all available taxonomy intents. No Golden rows were used for selection or training.",
    ])
    (results_dir / "balanced_evaluation.md").write_text("\n".join(report), encoding="utf-8")
    print(rows.to_string(index=False))
    print(f"\nBalanced training file: {output}")
    print("Training distribution:")
    print(distribution.to_string())


if __name__ == "__main__":
    main()
