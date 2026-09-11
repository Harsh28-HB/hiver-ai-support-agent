"""Fast, resumable terminal annotation tool for the AmazonHelp golden set."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

INTENTS = [
    "delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits",
    "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion",
    "website_app_or_technical_issue", "other_or_unclear",
]
ESCALATION = {"a": "AUTO-HANDLE", "e": "ESCALATE"}
FIELDS = [
    "conversation_id", "customer_message", "conversation_context", "historical_brand_response",
    "proposed_intent", "human_intent", "human_escalation", "human_notes", "annotation_status",
]


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row.setdefault("annotation_status", "labelled" if row.get("human_intent", "").strip() else "")
        for field in FIELDS:
            row.setdefault(field, "")
    return rows


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _show(index: int, total: int, row: dict[str, str]) -> None:
    print("\n" + "=" * 80)
    print(f"Example {index + 1}/{total} | conversation_id={row['conversation_id']}")
    print(f"Sampling hint only: {row['proposed_intent']}")
    print(f"\nRelevant context:\n{row['conversation_context']}")
    print(f"\nCustomer message:\n{row['customer_message']}")
    print("\nIntents:")
    for number, intent in enumerate(INTENTS, 1):
        print(f"  {number}. {intent}")
    print("  ENTER = accept hint | 1-9 = override | a = AUTO-HANDLE | e = ESCALATE")
    print("  s = skip | q = save and quit")


def _progress(rows: list[dict[str, str]]) -> None:
    reviewed = sum(bool(row.get("human_intent", "").strip()) and row.get("annotation_status", "").lower() in {"human-reviewed", "labelled"} for row in rows)
    print(f"Human-reviewed: {reviewed}/{len(rows)}")
    print(f"Remaining: {len(rows) - reviewed}")


def validate(path: Path) -> int:
    rows = _read(path)
    ids = [row.get("conversation_id", "") for row in rows]
    labelled = [row for row in rows if row.get("human_intent", "").strip()]
    skipped = [row for row in rows if row.get("annotation_status", "").strip().lower() == "skipped"]
    duplicate_ids = sorted({conversation_id for conversation_id in ids if ids.count(conversation_id) > 1 and conversation_id})
    missing = [row["conversation_id"] for row in rows if not row.get("human_intent", "").strip() and row.get("annotation_status", "").lower() != "skipped"]
    print(f"Rows: {len(rows)}")
    print(f"Labelled: {len(labelled)}")
    print(f"Remaining: {len(missing)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Duplicate IDs: {len(duplicate_ids)}" + (f" ({', '.join(duplicate_ids[:10])})" if duplicate_ids else ""))
    print(f"Missing labels: {len(missing)}")
    return 1 if len(rows) != 200 or duplicate_ids else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=Path("data/golden/golden_candidates.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/golden/golden_set.csv"))
    parser.add_argument("--validate", action="store_true", help="Report annotation progress and integrity checks.")
    args = parser.parse_args()
    if args.validate:
        raise SystemExit(validate(args.output))
    rows = _read(args.candidates)
    if args.output.exists():
        saved = {row["conversation_id"]: row for row in _read(args.output)}
        for row in rows:
            if row["conversation_id"] in saved:
                row.update(saved[row["conversation_id"]])
    if len(rows) != 200:
        raise SystemExit(f"Expected exactly 200 candidates, found {len(rows)}")
    pending = [index for index, row in enumerate(rows) if not row["human_intent"].strip() and row.get("annotation_status", "") != "skipped"]
    _progress(rows)
    for index in pending:
        row = rows[index]
        _show(index, len(rows), row)
        choice = input("Intent [ENTER=accept, 1-9=override, s=skip, q=quit]: ").strip().lower()
        if choice == "q":
            _write(args.output, rows)
            print(f"Progress saved to {args.output}")
            return
        if choice == "s":
            row["annotation_status"] = "skipped"
            _write(args.output, rows)
            print("Skipped and saved.")
            _progress(rows)
            continue
        if choice == "":
            intent = row.get("proposed_intent", "").strip()
            if intent not in INTENTS:
                print("The proposed hint is not in the finalized taxonomy; choose 1-9 instead.")
                continue
        else:
            try:
                intent = INTENTS[int(choice) - 1]
            except (ValueError, IndexError):
                print("Invalid intent; this example remains pending.")
                continue
        escalation = input("Decision [a= AUTO-HANDLE, e= ESCALATE]: ").strip().lower()
        if escalation not in ESCALATION:
            print("Invalid decision; this example remains pending.")
            continue
        notes = input("Optional notes (Enter for none): ").strip()
        row["human_intent"] = intent
        row["human_escalation"] = ESCALATION[escalation]
        row["human_notes"] = notes
        row["annotation_status"] = "human-reviewed"
        _write(args.output, rows)
        print("Saved as human-reviewed.")
        _progress(rows)
    _write(args.output, rows)
    print(f"Annotation complete. Saved to {args.output}")


if __name__ == "__main__":
    main()
