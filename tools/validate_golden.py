"""Validate progress and integrity of the human golden annotation file."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = {
    "conversation_id",
    "customer_message",
    "conversation_context",
    "historical_brand_response",
    "proposed_intent",
    "human_intent",
    "human_escalation",
    "human_notes",
}


def validate(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        rows = list(reader)

    missing_fields = sorted(REQUIRED_FIELDS - fieldnames)
    ids = [row.get("conversation_id", "").strip() for row in rows]
    duplicate_ids = sorted(
        conversation_id
        for conversation_id, count in Counter(ids).items()
        if conversation_id and count > 1
    )
    completed_intents = sum(bool(row.get("human_intent", "").strip()) for row in rows)
    completed_escalations = sum(bool(row.get("human_escalation", "").strip()) for row in rows)
    pending_intents = len(rows) - completed_intents
    pending_escalations = len(rows) - completed_escalations
    skipped = sum(row.get("annotation_status", "").strip().lower() == "skipped" for row in rows)

    failures: list[str] = []
    if missing_fields:
        failures.append("missing required fields")
    if len(rows) != 200:
        failures.append("expected exactly 200 examples")
    if duplicate_ids:
        failures.append("duplicate conversation IDs")
    if any(not conversation_id for conversation_id in ids):
        failures.append("blank conversation IDs")

    print(f"Total examples: {len(rows)}")
    print(f"Human intent labels completed: {completed_intents}")
    print(f"Human escalation decisions completed: {completed_escalations}")
    print(f"Pending intent labels: {pending_intents}")
    print(f"Pending escalation decisions: {pending_escalations}")
    print(f"Skipped examples: {skipped}")
    print(f"Duplicate conversation IDs: {len(duplicate_ids)}")
    print(f"Missing required fields: {', '.join(missing_fields) if missing_fields else 'none'}")
    print(f"Status: {'FAIL' if failures else 'PASS'}")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=Path("data/golden/golden_set.csv"))
    args = parser.parse_args()
    raise SystemExit(validate(args.path))


if __name__ == "__main__":
    main()
