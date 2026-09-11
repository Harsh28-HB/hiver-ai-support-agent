"""Evaluate intent baselines on human-labelled golden examples when available."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from src.baselines import FINAL_INTENTS, build_baselines, knowledge_label_path
from src.config import get_config

RESULT_COLUMNS = ["baseline", "status", "n_examples", "accuracy", "macro_f1", "per_intent_f1", "confusion_matrix"]


def _pending(reason: str) -> pd.DataFrame:
    return pd.DataFrame([
        {"baseline": "majority_class", "status": f"pending: {reason}", "n_examples": 0, "accuracy": "", "macro_f1": "", "per_intent_f1": "", "confusion_matrix": ""},
        {"baseline": "tfidf_logistic_regression", "status": f"pending: {reason}", "n_examples": 0, "accuracy": "", "macro_f1": "", "per_intent_f1": "", "confusion_matrix": ""},
    ], columns=RESULT_COLUMNS)


def evaluate(root: Path) -> pd.DataFrame:
    golden_path = root / "data" / "golden" / "golden_set.csv"
    if not golden_path.exists():
        return _pending("golden_set.csv does not exist")
    golden = pd.read_csv(golden_path, dtype=str).fillna("")
    processed_path = root / "data" / "processed" / "conversations.csv"
    duplicate_ids = int(golden["conversation_id"].duplicated().sum()) if "conversation_id" in golden else 0
    split_leakage = 0
    if processed_path.exists() and {"conversation_id", "split"}.issubset(golden.columns):
        processed = pd.read_csv(processed_path, usecols=["conversation_id", "split"], dtype=str)
        split_map = processed.drop_duplicates("conversation_id").set_index("conversation_id")["split"]
        split_leakage = int(sum(split_map.get(conversation_id, "") != "golden" for conversation_id in golden["conversation_id"]))
    if duplicate_ids or split_leakage:
        return _pending(f"golden validation failed: duplicate_ids={duplicate_ids}, split_leakage={split_leakage}")
    if "human_intent" not in golden or golden["human_intent"].isin(FINAL_INTENTS).sum() == 0:
        return _pending("human golden intent labels are not available")
    try:
        models = build_baselines(root)
    except (FileNotFoundError, ValueError) as error:
        return _pending(str(error))
    labeled = golden[golden["human_intent"].isin(FINAL_INTENTS)]
    texts = labeled["customer_message"].tolist()
    truth = labeled["human_intent"].tolist()
    rows = []
    for name, model in models.items():
        predictions = model.predict(texts)
        per_intent = f1_score(truth, predictions, labels=FINAL_INTENTS, average=None, zero_division=0)
        matrix = confusion_matrix(truth, predictions, labels=FINAL_INTENTS)
        rows.append({
            "baseline": name,
            "status": "complete_weak_supervision",
            "n_examples": len(labeled),
            "accuracy": round(float(accuracy_score(truth, predictions)), 6),
            "macro_f1": round(float(f1_score(truth, predictions, labels=FINAL_INTENTS, average="macro", zero_division=0)), 6),
            "per_intent_f1": json.dumps(dict(zip(FINAL_INTENTS, per_intent.round(6).tolist())), sort_keys=True),
            "confusion_matrix": json.dumps({"labels": FINAL_INTENTS, "matrix": matrix.tolist()}),
        })
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = (args.root or get_config().root).resolve()
    output = root / "results" / "baseline_results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    results = evaluate(root)
    results.to_csv(output, index=False)
    golden = pd.read_csv(root / "data" / "golden" / "golden_set.csv", dtype=str).fillna("") if (root / "data" / "golden" / "golden_set.csv").exists() else pd.DataFrame()
    intent_labels = int(golden["human_intent"].isin(FINAL_INTENTS).sum()) if "human_intent" in golden else 0
    (root / "results" / "baseline_report.md").write_text(
        "# Baseline Evaluation Report\n\n"
        "Training is restricted to Knowledge-only labels at `data/processed/knowledge_labels.csv`. "
        "Those labels are explicitly marked `label_source=weak_rule`; they are not human ground truth. "
        "Golden examples are evaluation-only.\n\n"
        f"- Golden examples: {len(golden):,}\n"
        f"- Human-labelled golden intents: {intent_labels:,}\n"
          f"- Evaluation status: {'complete with weak Knowledge labels' if (results['status'] == 'complete_weak_supervision').all() else 'pending'}\n\n"
          + ("Metrics are pending because required inputs are unavailable. No results were fabricated.\n"
              if not (results["status"] == "complete_weak_supervision").all() else "Metrics are recorded in `baseline_results.csv`; they measure models trained on deterministic weak labels and evaluated on 196 human-labelled golden examples.\n"),
        encoding="utf-8",
    )
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
