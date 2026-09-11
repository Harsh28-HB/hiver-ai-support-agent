"""Discover an exploratory AmazonHelp intent taxonomy from the knowledge split only."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .config import get_config

STOPWORDS = {
    "the", "and", "for", "you", "that", "this", "with", "have", "are", "was", "but", "not", "can",
    "just", "from", "your", "they", "what", "when", "has", "been", "all", "will", "get", "out", "there",
    "one", "how", "why", "our", "its", "amazonhelp", "https", "http", "www", "com", "please", "help",
    "thanks", "thank", "would", "could", "like", "about", "more", "some", "into", "than", "then", "still",
}

INTENT_RULES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("delivery_late_or_missing", "The order or package is late, missing, not received, or has an unresolved delivery date.", "delivery|delivered|arriv|late|delay|package|shipment|shipping|waiting|haven.t received|where is", ("deliv", "late", "delay", "package", "shipment", "wait")),
    ("order_tracking_or_status", "The customer asks where an order is, whether it shipped, or how to track its current status.", "track|tracking|order status|shipping status|shipped|dispatch|where.*order|status of", ("track", "status", "shipped", "dispatch", "order")),
    ("refund_return_or_cancellation", "The customer requests a refund, return, cancellation, reimbursement, or money-back action.", "refund|return|cancel|money back|reimburse|reimbursement|exchange", ("refund", "return", "cancel", "money", "reimburse")),
    ("prime_membership_or_benefits", "The message concerns Prime membership, Prime delivery benefits, trials, renewal, or membership charges.", "prime|membership|member|trial|renewal", ("prime", "membership", "trial", "renewal")),
    ("account_email_or_login", "The customer cannot access, update, verify, or receive messages for an Amazon account or email.", "account|login|log in|password|email address|verification|sign in|signin", ("account", "login", "password", "email", "verification")),
    ("payment_or_card_charge", "The message concerns a payment, charge, credit/debit card, billing, or an unexpected transaction.", "payment|charged|charge|credit card|debit card|billing|transaction|bank", ("payment", "charg", "credit", "debit", "billing", "card")),
    ("gift_card_or_promotion", "The customer reports a gift card, promotional code, voucher, balance, or redemption problem.", "gift card|giftcard|promo|promotion|voucher|coupon|redemption|claim code|balance", ("gift", "promo", "promotion", "voucher", "coupon", "redemption")),
    ("item_wrong_damaged_or_missing", "The delivered item is wrong, damaged, defective, incomplete, or materially different from the order.", "wrong item|damaged|damage|defective|broken|missing item|incomplete|not what|different item", ("wrong", "damag", "defect", "broken", "missing", "incomplete")),
    ("customer_service_contact_or_escalation", "The customer reports poor support, requests a human/contact route, or asks why support has not resolved the issue.", "customer service|customer support|call|contact|agent|representative|no one|nobody|complaint|escalat|response", ("customer", "service", "support", "call", "contact", "agent", "complaint")),
    ("website_app_or_technical_issue", "The customer reports an Amazon site, app, link, checkout, or other technical failure.", "website|web site|app|application|link|error|not working|checkout|page|technical", ("website", "app", "error", "checkout", "page", "technical")),
]


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9']{2,}", text) if token.lower() not in STOPWORDS]


def _intent_matches(text: str) -> list[str]:
    normalized = text.lower()
    return [name for name, _, pattern, _ in INTENT_RULES if re.search(pattern, normalized)]


def _intent_score(text: str, rule: tuple[str, str, str, tuple[str, ...]]) -> int:
    normalized = text.lower()
    _, _, pattern, anchors = rule
    score = 2 if re.search(pattern, normalized) else 0
    score += sum(len(re.findall(re.escape(anchor), normalized)) for anchor in anchors)
    return score


def _primary_intent(text: str) -> str:
    scored = [( _intent_score(text, rule), rule[0]) for rule in INTENT_RULES]
    score, intent = max(scored, default=(0, "other_or_unclear"))
    return intent if score > 0 else "other_or_unclear"


def _load_knowledge(path: Path) -> tuple[list[dict[str, Any]], int]:
    frame = pd.read_csv(path, usecols=["conversation_id", "messages", "split"])
    knowledge = frame[frame["split"].eq("knowledge")]
    records: list[dict[str, Any]] = []
    for _, row in knowledge.iterrows():
        messages = json.loads(row["messages"])
        customers = [message for message in messages if message.get("speaker") == "customer"]
        if customers:
            records.append({"conversation_id": str(row["conversation_id"]), "messages": messages, "customer_messages": customers})
    return records, int(frame["split"].eq("golden").sum())


def _tfidf_terms(records: list[dict[str, Any]]) -> list[tuple[str, float]]:
    document_frequency = Counter()
    term_frequency = Counter()
    for record in records:
        terms = _tokens(" ".join(message["text"] for message in record["customer_messages"]))
        term_frequency.update(terms)
        document_frequency.update(set(terms))
    documents = max(len(records), 1)
    scores = {
        term: count * math.log((1 + documents) / (1 + document_frequency[term]))
        for term, count in term_frequency.items()
    }
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:80]


def _response_signals(records: list[dict[str, Any]]) -> dict[str, Counter]:
    signals: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        for index, message in enumerate(record["messages"]):
            if message.get("speaker") != "customer":
                continue
            intent = _primary_intent(message["text"])
            following = record["messages"][index + 1:]
            brand_text = " ".join(item["text"] for item in following if item.get("speaker") == "brand")
            lower = brand_text.lower()
            signals[intent]["brand_response_observed"] += int(bool(brand_text))
            signals[intent]["apology_or_empathy"] += int(bool(re.search(r"sorry|understand|frustrat|apolog", lower)))
            signals[intent]["private_or_direct_message"] += int(bool(re.search(r"dm|direct message|private message", lower)))
            signals[intent]["order_or_tracking_guidance"] += int(bool(re.search(r"order|tracking|delivery|shipment|arriv", lower)))
            signals[intent]["wait_or_deadline"] += int(bool(re.search(r"wait|arrive|by \d|within|day", lower)))
            signals[intent]["contact_or_support_route"] += int(bool(re.search(r"contact|call|chat|support|help", lower)))
    return signals


def _examples(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    candidates: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for record in records:
        for message in record["customer_messages"]:
            intent = _primary_intent(message["text"])
            rule = next((rule for rule in INTENT_RULES if rule[0] == intent), None)
            score = _intent_score(message["text"], rule) if rule else 0
            candidates[intent].append((score, message["text"].replace("\n", " ").strip()))
    return {intent: [text for _, text in sorted(values, key=lambda item: item[0], reverse=True)[:3]] for intent, values in candidates.items()}


def write_outputs(config_root: Path) -> None:
    processed = config_root / "data" / "processed" / "conversations.csv"
    results = config_root / "results"
    records, golden_count = _load_knowledge(processed)
    examples = _examples(records)
    signals = _response_signals(records)
    counts = Counter(_primary_intent(message["text"]) for record in records for message in record["customer_messages"])
    ambiguous = Counter(len(_intent_matches(message["text"])) for record in records for message in record["customer_messages"])
    tfidf = _tfidf_terms(records)

    distribution = []
    for name, definition, _, _ in INTENT_RULES:
        anchors = next(rule[3] for rule in INTENT_RULES if rule[0] == name)
        distribution.append({"intent": name, "knowledge_customer_messages": counts[name], "knowledge_customer_message_pct": round(100 * counts[name] / max(sum(counts.values()), 1), 2), "tfidf_anchor_terms": ", ".join(term for term, _ in tfidf if any(anchor in term for anchor in anchors))})
    distribution.append({"intent": "other_or_unclear", "knowledge_customer_messages": counts["other_or_unclear"], "knowledge_customer_message_pct": round(100 * counts["other_or_unclear"] / max(sum(counts.values()), 1), 2), "tfidf_anchor_terms": ""})
    pd.DataFrame(distribution).to_csv(results / "intent_distribution.csv", index=False)

    taxonomy_lines = ["# Draft AmazonHelp Intent Taxonomy", "", "This exploratory taxonomy was derived only from conversations in the `knowledge` split. The golden split was counted for planning but never read for terms, examples, or taxonomy decisions.", "", f"Knowledge conversations analyzed: {len(records):,}", f"Knowledge customer messages analyzed: {sum(counts.values()):,}", "", "## Intents"]
    closest = {
        "delivery_late_or_missing": "order_tracking_or_status",
        "order_tracking_or_status": "delivery_late_or_missing",
        "refund_return_or_cancellation": "item_wrong_damaged_or_missing",
        "prime_membership_or_benefits": "payment_or_card_charge",
        "account_email_or_login": "website_app_or_technical_issue",
        "payment_or_card_charge": "prime_membership_or_benefits",
        "gift_card_or_promotion": "payment_or_card_charge",
        "item_wrong_damaged_or_missing": "delivery_late_or_missing",
        "customer_service_contact_or_escalation": "all operational intents",
        "website_app_or_technical_issue": "account_email_or_login",
    }
    for name, definition, _, _ in INTENT_RULES:
        taxonomy_lines.extend([f"### {name}", f"- Definition: {definition}", f"- Approximate frequency: {counts[name]:,} customer messages ({100 * counts[name] / max(sum(counts.values()), 1):.2f}% of knowledge customer messages)", f"- Closest/confusing intent: `{closest[name]}`", "- Representative examples:"])
        taxonomy_lines.extend(f"  - {example}" for example in examples[name])
        taxonomy_lines.append("")
    taxonomy_lines.extend(["## Ambiguity", f"Messages matching two or more exploratory themes: {sum(value for key, value in ambiguous.items() if key >= 2):,}", f"Messages matching no exploratory theme: {counts['other_or_unclear']:,}", "These are review queues, not automatically assigned labels.", "", "## TF-IDF signals", ", ".join(f"{term} ({score:.1f})" for term, score in tfidf[:40]), "", "The themes are lightweight, evidence-based grouping anchors for manual review, not a classifier or final label set."])
    (results / "intent_taxonomy_draft.md").write_text("\n".join(taxonomy_lines), encoding="utf-8")

    resolution_lines = ["# AmazonHelp Resolution Patterns", "", "Computed from brand messages following knowledge-split customer messages. Golden conversations were not inspected.", ""]
    for name, _, _, _ in INTENT_RULES:
        signal = signals[name]
        total = counts[name]
        resolution_lines.append(f"## {name}")
        resolution_lines.append(f"- Customer messages: {total:,}; messages with a later brand response: {signal['brand_response_observed']:,} ({100 * signal['brand_response_observed'] / max(total, 1):.1f}%).")
        for key in ["apology_or_empathy", "private_or_direct_message", "order_or_tracking_guidance", "wait_or_deadline", "contact_or_support_route"]:
            resolution_lines.append(f"- {key.replace('_', ' ').capitalize()}: {signal[key]:,} ({100 * signal[key] / max(total, 1):.1f}%).")
        resolution_lines.append("")
    (results / "resolution_patterns.md").write_text("\n".join(resolution_lines), encoding="utf-8")

    sampling = f"""# Golden Evaluation Sampling Plan

The golden split contains {golden_count:,} conversations in the current processed artifact. It was not used to discover, tune, or name intents.

Sample approximately 200 complete conversations for human annotation:

- Draw 160 conversations with a deterministic seed from the golden split, stratified only by observable structure: conversation length (2, 3, 4, and 5+ messages), whether the first customer message has a linked brand reply, and customer-message length bands.
- Reserve 40 additional conversations for coverage of rare/ambiguous cases identified by annotators during the first pass. Selection must be blind to any automatically inferred intent.
- Keep every message in a selected conversation together. Annotators should label the first customer request using the approved taxonomy, mark multi-intent and ambiguous cases, and record the first historically appropriate brand response separately.
- Deduplicate near-identical customer text within the golden sample using normalized exact text before annotation; replace excluded rows with another deterministic draw.
- Store labels and annotator notes under `data/golden/`; do not feed those labels back into taxonomy discovery.

This plan creates a human-reviewed evaluation set without allowing golden examples to shape the taxonomy.
"""
    (results / "golden_sampling_plan.md").write_text(sampling, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    write_outputs((args.root or get_config().root).resolve())
    print("Intent discovery complete using only the knowledge split.")


if __name__ == "__main__":
    main()
