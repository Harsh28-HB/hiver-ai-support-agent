"""Evaluate the AmazonHelp agent on human-labelled golden examples only."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from src.agent import AmazonHelpAgent
from src.baselines import FINAL_INTENTS, build_baselines
from src.config import get_config


def _golden_validation(root: Path, golden: pd.DataFrame) -> tuple[int, int]:
    duplicate_ids = int(golden["conversation_id"].duplicated().sum())
    processed = pd.read_csv(root / "data" / "processed" / "conversations.csv", usecols=["conversation_id", "split"], dtype=str)
    split_map = processed.drop_duplicates("conversation_id").set_index("conversation_id")["split"]
    leakage = int(sum(split_map.get(conversation_id, "") != "golden" for conversation_id in golden["conversation_id"]))
    return duplicate_ids, leakage


def _metrics(truth: list[str], predictions: list[str]) -> dict[str, Any]:
    scores = f1_score(truth, predictions, labels=FINAL_INTENTS, average=None, zero_division=0)
    matrix = confusion_matrix(truth, predictions, labels=FINAL_INTENTS)
    return {
        "accuracy": round(float(accuracy_score(truth, predictions)), 6),
        "macro_f1": round(float(f1_score(truth, predictions, labels=FINAL_INTENTS, average="macro", zero_division=0)), 6),
        "per_intent_f1": dict(zip(FINAL_INTENTS, scores.round(6).tolist())),
        "confusion_matrix": {"labels": FINAL_INTENTS, "matrix": matrix.tolist()},
    }


def _optional_llm_judge(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reserve optional judge integration without making API calls when unconfigured."""
    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "unavailable: OPENAI_API_KEY is not configured", "n_examples": 0}
    return {"status": "not_run: API integration requires an explicitly selected provider/model", "n_examples": 0}


def evaluate(root: Path) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    golden = pd.read_csv(root / "data" / "golden" / "golden_set.csv", dtype=str).fillna("")
    duplicate_ids, leakage = _golden_validation(root, golden)
    labelled = golden[golden["human_intent"].isin(FINAL_INTENTS) & golden["human_escalation"].isin(["AUTO-HANDLE", "ESCALATE"])]
    if duplicate_ids or leakage:
        raise ValueError(f"Golden validation failed: duplicate_ids={duplicate_ids}, split_leakage={leakage}")
    agent = AmazonHelpAgent(root)
    baseline_models = build_baselines(root)
    texts = labelled["customer_message"].tolist()
    truth_intent = labelled["human_intent"].tolist()
    truth_escalation = labelled["human_escalation"].tolist()
    agent_rows: list[dict[str, Any]] = []
    intent_predictions: list[str] = []
    escalation_predictions: list[str] = []
    for _, row in labelled.iterrows():
        result = agent.respond(row["customer_message"])
        intent_predictions.append(result["intent"])
        escalation_predictions.append(result["decision"])
        agent_rows.append({
            "conversation_id": row["conversation_id"],
            "customer_message": row["customer_message"],
            "gold_intent": row["human_intent"],
            "predicted_intent": result["intent"],
            "confidence": result["confidence"],
            "gold_escalation": row["human_escalation"],
            "predicted_decision": result["decision"],
            "decision_reason": result["reason"],
            "reply": result["reply"],
            "retrieved_evidence": json.dumps(result["retrieved_evidence"], ensure_ascii=True),
        })
    rows: list[dict[str, Any]] = []
    for name, model in baseline_models.items():
        rows.append({"system": name, "n_examples": len(labelled), **_metrics(truth_intent, model.predict(texts)), "escalation_accuracy": ""})
    agent_metrics = _metrics(truth_intent, intent_predictions)
    rows.append({
        "system": "amazonhelp_agent",
        "n_examples": len(labelled),
        **agent_metrics,
        "escalation_accuracy": round(float(accuracy_score(truth_escalation, escalation_predictions)), 6),
    })
    metadata = {
        "golden_rows": len(golden),
        "labelled_rows": len(labelled),
        "duplicate_ids": duplicate_ids,
        "split_leakage": leakage,
        "llm_judge": _optional_llm_judge(agent_rows),
    }
    return pd.DataFrame(rows), metadata, agent_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = (args.root or get_config().root).resolve()
    results, metadata, agent_rows = evaluate(root)
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(results_dir / "agent_evaluation.csv", index=False)
    report_lines = [
        "# AmazonHelp Agent Evaluation",
        "",
        "Evaluation uses only human-labelled golden rows. The agent trains and retrieves only from Knowledge data.",
        "",
        f"- Golden rows: {metadata['golden_rows']}",
        f"- Human-labelled rows evaluated: {metadata['labelled_rows']}",
        f"- Duplicate conversation IDs: {metadata['duplicate_ids']}",
        f"- Split leakage: {metadata['split_leakage']}",
        f"- LLM judge: {metadata['llm_judge']['status']}",
        "",
        "## Metrics",
        "",
    ]
    for _, row in results.iterrows():
        report_lines.extend([
            f"### {row['system']}",
            f"- Accuracy: {row['accuracy']}",
            f"- Macro F1: {row['macro_f1']}",
            f"- Escalation accuracy: {row['escalation_accuracy'] or 'not applicable'}",
            f"- Per-intent F1: `{json.dumps(row['per_intent_f1'], sort_keys=True)}`",
            f"- Confusion matrix: `{json.dumps(row['confusion_matrix'])}`",
            "",
        ])
    (results_dir / "agent_evaluation.md").write_text("\n".join(report_lines), encoding="utf-8")
    pd.DataFrame(agent_rows).to_csv(results_dir / "agent_evaluation_examples.csv", index=False)
    print(results.to_string(index=False))
    print(f"\nLLM judge: {metadata['llm_judge']['status']}")


if __name__ == "__main__":
    main()
