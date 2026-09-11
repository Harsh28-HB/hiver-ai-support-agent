"""Sample and validate the AmazonHelp golden annotation candidates."""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .config import get_config

CANDIDATE_FIELDS = [
    "conversation_id", "customer_message", "conversation_context", "historical_brand_response",
    "proposed_intent", "human_intent", "human_escalation", "human_notes",
]
FINAL_INTENTS = [
    "delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits",
    "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion",
    "customer_service_contact_or_escalation", "website_app_or_technical_issue", "other_or_unclear",
]

# These hints are applied only to GOLDEN rows to diversify sampling. They are not human labels.
HINT_RULES: list[tuple[str, str]] = [
    ("refund_return_or_cancellation", r"refund|return|cancel|money back|reimburse|damaged|defective|broken|wrong item|missing item"),
    ("prime_membership_or_benefits", r"prime|membership|trial|renewal"),
    ("account_email_or_login", r"account|login|log in|password|email address|verification|sign in|signin"),
    ("payment_or_card_charge", r"payment|charged|charge|credit card|debit card|billing|transaction|bank"),
    ("gift_card_or_promotion", r"gift card|giftcard|promo|promotion|voucher|coupon|redemption|claim code"),
    ("website_app_or_technical_issue", r"\bwebsite\b|\bweb site\b|\bapp\b|\bapplication\b|\berror\b|\bnot working\b|\bcheckout\b|\bpage\b|\btechnical\b"),
    ("delivery_tracking", r"track|tracking|order status|shipping status|shipped|dispatch|where.*order|status of"),
    ("delivery_delay", r"delivery|delivered|arriv|late|delay|package|shipment|shipping|waiting|haven.t received"),
]


def _normalized(text: str) -> str:
    text = re.sub(r"https?://\S+|@\w+", " ", text.lower())
    text = re.sub(r"\d+", "#", text)
    return re.sub(r"\W+", " ", text).strip()


def _proposal(text: str) -> str:
    normalized = text.lower()
    matches = [(name, len(re.findall(pattern, normalized))) for name, pattern in HINT_RULES]
    name, score = max(matches, key=lambda item: item[1], default=("other_or_unclear", 0))
    return name if score else "other_or_unclear"


def _format_message(message: dict[str, Any]) -> str:
    speaker = "Customer" if message.get("speaker") == "customer" else "AmazonHelp"
    return f"{speaker}: {message.get('text', '').strip()}"


def _load_golden(processed_path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(processed_path, usecols=["conversation_id", "messages", "split"])
    golden = frame[frame["split"].eq("golden")]
    records: list[dict[str, Any]] = []
    for _, row in golden.iterrows():
        messages = json.loads(row["messages"])
        first_customer = next((index for index, message in enumerate(messages) if message.get("speaker") == "customer"), None)
        if first_customer is None:
            continue
        first_brand_after = next((index for index in range(first_customer + 1, len(messages)) if messages[index].get("speaker") == "brand"), None)
        if first_brand_after is None:
            continue
        customer_message = messages[first_customer]["text"].strip()
        response = messages[first_brand_after]["text"].strip()
        context = "\n".join(_format_message(message) for message in messages[:first_customer]) or "(No earlier context)"
        records.append({
            "conversation_id": str(row["conversation_id"]),
            "customer_message": customer_message,
            "conversation_context": context,
            "historical_brand_response": response,
            "proposed_intent": _proposal(customer_message),
            "human_intent": "",
            "human_escalation": "",
            "human_notes": "",
            "_length": len(messages),
            "_ambiguous": len([name for name, pattern in HINT_RULES if re.search(pattern, customer_message, re.I)]) > 1,
            "_near_key": _normalized(customer_message),
        })
    return records


def _sample(records: list[dict[str, Any]], target: int = 200, seed: int = 42) -> list[dict[str, Any]]:
    if len(records) < target:
        raise ValueError(f"Only {len(records)} eligible golden conversations are available; {target} required")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record["proposed_intent"]].append(record)
    for values in groups.values():
        values.sort(key=lambda item: hashlib.sha256(f"{seed}:{item['conversation_id']}".encode()).hexdigest())

    quotas = {name: 0 for name in groups}
    ranked_groups = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)
    for name, values in ranked_groups:
        quotas[name] = min(30, max(4, round(target * len(values) / len(records))))
    while sum(quotas.values()) < target:
        name = max(groups, key=lambda key: len(groups[key]) - quotas[key])
        if quotas[name] < len(groups[name]):
            quotas[name] += 1
        else:
            break
    while sum(quotas.values()) > target:
        name = max(quotas, key=lambda key: quotas[key])
        if quotas[name] > 1:
            quotas[name] -= 1
        else:
            break

    selected: list[dict[str, Any]] = []
    for name, values in groups.items():
        selected.extend(values[:quotas[name]])
    # Prefer difficult and multi-turn examples when trimming or filling the final slots.
    selected.sort(key=lambda item: (not item["_ambiguous"], item["_length"] < 3, item["conversation_id"]))
    selected = selected[:target]

    deduped: list[dict[str, Any]] = []
    seen_keys: list[str] = []
    for record in selected:
        key = record["_near_key"]
        if not key or any(key == prior or (len(key) > 40 and difflib.SequenceMatcher(None, key, prior).ratio() >= 0.94) for prior in seen_keys):
            continue
        deduped.append(record)
        seen_keys.append(key)
        if len(deduped) == target:
            break
    if len(deduped) < target:
        pool = sorted(records, key=lambda item: hashlib.sha256(f"{seed}:fill:{item['conversation_id']}".encode()).hexdigest())
        for record in pool:
            if record in deduped:
                continue
            key = record["_near_key"]
            if key and any(key == prior or (len(key) > 40 and difflib.SequenceMatcher(None, key, prior).ratio() >= 0.94) for prior in seen_keys):
                continue
            deduped.append(record)
            seen_keys.append(key)
            if len(deduped) == target:
                break
    if len(deduped) != target:
        raise ValueError(f"Near-duplicate filtering left only {len(deduped)} candidates")
    return deduped


def write_candidates(config_root: Path) -> Path:
    processed = config_root / "data" / "processed" / "conversations.csv"
    output = config_root / "data" / "golden" / "golden_candidates.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    records = _sample(_load_golden(processed))
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows({field: record[field] for field in CANDIDATE_FIELDS} for record in records)
    annotation_path = config_root / "data" / "golden" / "golden_set.csv"
    if not annotation_path.exists():
        with annotation_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
            writer.writeheader()
            writer.writerows({field: record[field] for field in CANDIDATE_FIELDS} for record in records)
    return output


def validate(config_root: Path) -> list[str]:
    path = config_root / "data" / "golden" / "golden_candidates.csv"
    frame = pd.read_csv(path, dtype=str).fillna("")
    errors: list[str] = []
    if len(frame) != 200:
        errors.append(f"expected exactly 200 rows, found {len(frame)}")
    if frame["conversation_id"].duplicated().any():
        errors.append("duplicate conversation IDs found")
    if set(frame.columns) != set(CANDIDATE_FIELDS):
        errors.append("required candidate fields do not match")
    if frame[["human_intent", "human_escalation", "human_notes"]].apply(lambda column: column.str.strip().ne("")).any().any():
        errors.append("human annotation fields are not blank")
    processed = pd.read_csv(config_root / "data" / "processed" / "conversations.csv", usecols=["conversation_id", "split"], dtype=str)
    split_map = processed.set_index("conversation_id")["split"]
    if any(split_map.get(conversation_id) != "golden" for conversation_id in frame["conversation_id"]):
        errors.append("candidate conversation is not in the golden split")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    root = (args.root or get_config().root).resolve()
    if not args.validate:
        print(f"Wrote {write_candidates(root)}")
    errors = validate(root)
    if errors:
        raise SystemExit("Validation failed: " + "; ".join(errors))
    print("Validation passed: 200 unique golden-only candidates with required fields and blank human annotations.")


if __name__ == "__main__":
    main()
