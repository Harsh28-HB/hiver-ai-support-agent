"""Run Phase 1-6 inspection, brand analysis, and conversation preprocessing."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import logging
import re
from pathlib import Path

from src.brand_analysis import analyze_brands, write_brand_outputs
from src.config import PipelineConfig, get_config
from src.conversations import reconstruct_conversations, write_conversations
from src.data_inspection import inspect_dataset, print_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="Repository root (defaults to this file's directory).")
    parser.add_argument("--reuse-processed", action="store_true", help="Reuse existing processed conversations and refresh reports only.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = get_config(args.root)
    for directory in [config.raw_dir, config.processed_dir, config.golden_dir, config.results_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    inspection = inspect_dataset(config)
    if inspection["files"]:
        item = inspection["files"][0]
        print(
            f"Inspected {item['filename']}: {item['row_count']:,} rows, {len(item['columns'])} columns, "
            f"{item.get('unique_author_count', 0):,} unique authors, "
            f"{item.get('inbound_count', 0):,} inbound, {item.get('outbound_count', 0):,} outbound."
        )
    else:
        print_report(inspection)
    files = sorted(config.raw_dir.glob("*.csv")) + sorted(config.raw_dir.glob("*.tsv")) + sorted(config.raw_dir.glob("*.txt"))
    analysis = analyze_brands(files[0], config) if files else __import__("pandas").DataFrame()
    write_brand_outputs(config, analysis)
    selected = str(analysis.iloc[0]["brand"]) if not analysis.empty else None
    processed_path = config.processed_dir / "conversations.csv"
    if args.reuse_processed and processed_path.exists():
        conversations = __import__("pandas").read_csv(processed_path)
        metadata = {"reason": "reused existing processed conversations", "selected_brand_records": int(conversations["message_count"].sum()), "empty_records_removed": 0, "multi_turn_conversations": int((conversations["message_count"] > 2).sum())}
    else:
        conversations, metadata = (reconstruct_conversations(files[0], config, selected) if files else (__import__("pandas").DataFrame(columns=["conversation_id", "brand", "messages", "message_count"]), {"reason": "no raw file"}))
        write_conversations(config, conversations)

    report = config.results_dir / "data_quality_report.md"
    measured_rows = sum(int(item.get("row_count", 0)) for item in inspection["files"])
    measured_duplicates = sum(int(item.get("duplicate_count", 0)) for item in inspection["files"])
    conversation_lengths = conversations["message_count"] if not conversations.empty else __import__("pandas").Series(dtype="int64")
    all_messages = []
    for serialized in conversations["messages"] if not conversations.empty else []:
        all_messages.extend(json.loads(serialized))
    customer_messages = [message for message in all_messages if message["speaker"] == "customer"]
    brand_messages = [message for message in all_messages if message["speaker"] == "brand"]
    customer_tokens = Counter(
        token.lower() for message in customer_messages
        for token in re.findall(r"[A-Za-z][A-Za-z']{2,}", message["text"])
        if token.lower() not in {"the", "and", "for", "you", "with", "this", "that", "have", "are", "not", "but"}
    )
    split_counts = conversations["split"].value_counts().to_dict() if "split" in conversations else {}
    (config.results_dir / "selected_brand_analysis.md").write_text(
        "# Selected Brand Exploratory Analysis\n\n"
        f"- Brand: {selected or 'not available'}\n"
        f"- Conversations: {len(conversations):,}\n"
        f"- Customer messages: {len(customer_messages):,}\n"
        f"- Brand messages: {len(brand_messages):,}\n"
        f"- Average conversation length: {conversation_lengths.mean() if len(conversation_lengths) else 0:.2f}\n"
        f"- Median conversation length: {conversation_lengths.median() if len(conversation_lengths) else 0:.2f}\n"
        f"- One-message-side conversations (exactly 2 messages): {int((conversation_lengths == 2).sum()) if len(conversation_lengths) else 0:,}\n"
        f"- Multi-turn conversations (>2 messages): {int((conversation_lengths > 2).sum()) if len(conversation_lengths) else 0:,}\n"
        f"- Conversation split counts: {split_counts}\n\n"
        "## Frequent customer terms\n\n"
        + ", ".join(f"{word} ({count})" for word, count in customer_tokens.most_common(40))
        + "\n\nThese are exploratory lexical signals only, not the final intent taxonomy.\n",
        encoding="utf-8",
    )
    report.write_text(
        "# Data Quality Report\n\n"
        f"- Raw records observed: {measured_rows:,}\n"
        f"- Duplicate records observed: {measured_duplicates:,}\n"
        f"- Input files inspected: {len(inspection['files'])}\n"
        f"- Selected brand: {selected or 'not available'}\n"
        f"- Selected-brand processed records: {metadata.get('selected_brand_records', 0):,}\n"
        f"- Usable conversation threads reconstructed: {len(conversations):,}\n"
        f"- Multi-turn conversations (>2 messages): {metadata.get('multi_turn_conversations', 0):,}\n"
        f"- Customer messages in usable conversations: {len(customer_messages):,}\n"
        f"- Brand messages in usable conversations: {len(brand_messages):,}\n"
        f"- Average conversation length: {conversation_lengths.mean() if len(conversation_lengths) else 0:.2f}\n"
        f"- Median conversation length: {conversation_lengths.median() if len(conversation_lengths) else 0:.2f}\n"
        f"- Empty text records removed: {metadata.get('empty_records_removed', 0):,}\n"
        f"- Conversation-level split counts: {split_counts}\n"
        f"- Conversation reconstruction note: {metadata.get('reason', 'not available')}\n"
        "\nFiltering decisions: duplicate tweet IDs are collapsed; empty text is excluded; only explicit tweet-ID "
        "parent/response components containing both customer and selected-brand messages are retained. "
        "Future messages remain in their chronological conversation, but later evaluation must truncate inputs before the target brand response. "
        "The deterministic knowledge/validation/golden assignment is at conversation level, so no conversation is split across partitions.\n",
        encoding="utf-8",
    )
    print(f"\nSelected brand: {selected or 'not available'}")
    print(f"Usable conversations: {len(conversations):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
