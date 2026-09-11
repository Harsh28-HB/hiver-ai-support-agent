"""Create explicit weak Knowledge labels from the approved AmazonHelp taxonomy.

These are training labels, not human ground truth. The output marks their source
so downstream reports cannot mistake them for manually annotated data.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from .baselines import FINAL_INTENTS
from .config import get_config

RULES = {
    "delivery_delay": r"delivery|delivered|arriv|late|delay|package|shipment|shipping|waiting|haven.t received",
    "delivery_tracking": r"track|tracking|order status|shipping status|shipped|dispatch|where.*order|status of",
    "refund_return_or_cancellation": r"refund|return|cancel|money back|reimburse|damaged|defective|broken|wrong item|missing item",
    "prime_membership_or_benefits": r"prime|membership|trial|renewal",
    "account_email_or_login": r"account|login|log in|password|email address|verification|sign in|signin",
    "payment_or_card_charge": r"payment|charged|charge|credit card|debit card|billing|transaction|bank",
    "gift_card_or_promotion": r"gift card|giftcard|promo|promotion|voucher|coupon|redemption|claim code",
    "website_app_or_technical_issue": r"\bwebsite\b|\bweb site\b|\bapp\b|\bapplication\b|\berror\b|not working|checkout|\bpage\b|technical",
}


def assign_intent(text: str) -> str:
    normalized = text.lower()
    scores = {intent: len(re.findall(pattern, normalized)) for intent, pattern in RULES.items()}
    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    return best_intent if best_score else "other_or_unclear"


def create_labels(root: Path) -> Path:
    source = root / "data" / "processed" / "conversations.csv"
    output = root / "data" / "processed" / "knowledge_labels.csv"
    rows: list[dict[str, str]] = []
    frame = pd.read_csv(source, usecols=["conversation_id", "messages", "split"], dtype=str)
    for _, row in frame[frame["split"].eq("knowledge")].iterrows():
        messages = json.loads(row["messages"])
        for message in messages:
            if message.get("speaker") != "customer" or not str(message.get("text", "")).strip():
                continue
            rows.append({
                "conversation_id": str(row["conversation_id"]),
                "customer_message": str(message["text"]).strip(),
                "human_intent": assign_intent(str(message["text"])),
                "label_source": "weak_rule",
            })
    result = pd.DataFrame(rows, columns=["conversation_id", "customer_message", "human_intent", "label_source"])
    if not set(result["human_intent"].unique()).issubset(set(FINAL_INTENTS)):
        raise ValueError("Generated label outside approved taxonomy")
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    output = create_labels((args.root or get_config().root).resolve())
    print(f"Wrote weak Knowledge labels to {output}")


if __name__ == "__main__":
    main()
