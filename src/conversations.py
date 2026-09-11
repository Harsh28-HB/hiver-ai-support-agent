"""Reconstruct reliable support conversations from discovered relationships."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, get_config
from .data_inspection import discover_files

LOGGER = logging.getLogger(__name__)


def _find_column(columns: list[str], patterns: tuple[str, ...]) -> str | None:
    for column in columns:
        if any(re.search(pattern, column.lower()) for pattern in patterns):
            return column
    return None


def _direction(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {"outbound", "out", "brand", "agent", "response", "true", "1", "yes"}:
        return "brand"
    if text in {"inbound", "in", "customer", "user", "false", "0", "no"}:
        return "customer"
    return None


def reconstruct_conversations(path: Path, config: PipelineConfig, brand: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build connected reply components for one outbound support account.

    The first pass identifies the selected account's tweet IDs and their explicit
    response targets. The second pass retains those tweets plus directly linked
    customer tweets. Components are then built from parent-child edges, so a
    multi-turn chain remains one conversation instead of one row per parent.
    """
    columns = ["tweet_id", "author_id", "inbound", "created_at", "text", "response_tweet_id", "in_response_to_tweet_id"]
    empty = pd.DataFrame(columns=["conversation_id", "brand", "messages", "message_count", "customer_messages", "brand_messages"])
    if not brand:
        return empty, {"reason": "no selected brand", "raw_records": 0, "usable_conversation_threads": 0}

    brand_ids: set[str] = set()
    response_ids: set[str] = set()
    raw_records = 0
    empty_records = 0
    duplicate_records = 0
    for chunk in pd.read_csv(path, usecols=columns, chunksize=config.chunk_size, on_bad_lines="skip"):
        raw_records += len(chunk)
        empty_records += int(chunk["text"].fillna("").astype(str).str.strip().eq("").sum())
        duplicate_records += int(chunk.duplicated().sum())
        support = chunk[(chunk["author_id"].astype(str) == brand) & chunk["inbound"].eq(False)]
        brand_ids.update(support["tweet_id"].astype(str))
        for value in support["response_tweet_id"]:
            if not pd.isna(value):
                response_ids.update(item.strip() for item in str(value).split(",") if item.strip())

    retained: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=columns, chunksize=config.chunk_size, on_bad_lines="skip"):
        ids = chunk["tweet_id"].astype(str)
        parents = chunk["in_response_to_tweet_id"].astype("Int64").astype(str)
        keep = ids.isin(brand_ids | response_ids) | parents.isin(brand_ids | response_ids)
        retained.append(chunk[keep].copy())
    frame = pd.concat(retained, ignore_index=True) if retained else pd.DataFrame(columns=columns)
    frame = frame.drop_duplicates(subset=["tweet_id"])
    valid_text = frame["text"].fillna("").astype(str).str.strip().ne("")
    frame = frame[valid_text].copy()
    frame["_id"] = frame["tweet_id"].astype(str)
    frame["_parent"] = frame["in_response_to_tweet_id"].astype("Int64").astype(str)
    frame["_time"] = pd.to_datetime(frame["created_at"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce", utc=True)

    parent_map = {tweet_id: tweet_id for tweet_id in frame["_id"]}

    def find(tweet_id: str) -> str:
        root = tweet_id
        while parent_map[root] != root:
            root = parent_map[root]
        while parent_map[tweet_id] != tweet_id:
            next_id = parent_map[tweet_id]
            parent_map[tweet_id] = root
            tweet_id = next_id
        return root

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent_map[right_root] = left_root

    for _, row in frame.iterrows():
        parent = row["_parent"]
        if parent in parent_map:
            union(row["_id"], parent)

    frame["_component"] = frame["_id"].map(find)

    records: list[dict[str, Any]] = []
    for conversation_id, group in frame.groupby("_component", sort=True):
        group = group.sort_values("_time", na_position="last")
        has_brand = bool((group["author_id"].astype(str).eq(brand) & ~group["inbound"]).any())
        has_customer = bool(group["inbound"].any())
        if len(group) < 2 or not (has_brand and has_customer):
            continue
        messages = []
        for _, row in group.iterrows():
            messages.append({
                "tweet_id": str(row["tweet_id"]),
                "speaker": "customer" if bool(row["inbound"]) else "brand",
                "author_id": str(row["author_id"]),
                "text": str(row["text"]).strip(),
                "timestamp": None if pd.isna(row["_time"]) else row["_time"].isoformat(),
                "in_response_to_tweet_id": None if pd.isna(row["in_response_to_tweet_id"]) else str(int(row["in_response_to_tweet_id"])),
                "response_tweet_id": None if pd.isna(row["response_tweet_id"]) else str(row["response_tweet_id"]),
            })
        records.append({
            "conversation_id": str(conversation_id),
            "brand": brand,
            "messages": json.dumps(messages, ensure_ascii=True),
            "message_count": len(messages),
            "customer_messages": sum(message["speaker"] == "customer" for message in messages),
            "brand_messages": sum(message["speaker"] == "brand" for message in messages),
            "split": _split_for_conversation(str(conversation_id), config.random_seed),
        })
    output = pd.DataFrame(records, columns=[*empty.columns, "split"])
    return output, {
        "reason": "explicit tweet IDs and parent/response relationships; components require both speakers",
        "raw_records": raw_records,
        "duplicates_removed": duplicate_records,
        "empty_records_removed": empty_records,
        "selected_brand_records": len(frame),
        "usable_conversation_threads": len(output),
        "multi_turn_conversations": int((output["message_count"] > 2).sum()) if not output.empty else 0,
        "retained_linked_records": len(frame),
    }


def _split_for_conversation(conversation_id: str, seed: int) -> str:
    """Assign whole conversations deterministically; no message-level splitting."""
    bucket = int(hashlib.sha256(f"{seed}:{conversation_id}".encode("utf-8")).hexdigest()[:8], 16) % 100
    return "golden" if bucket < 10 else "validation" if bucket < 20 else "knowledge"


def write_conversations(config: PipelineConfig, conversations: pd.DataFrame) -> None:
    """Persist reconstructed conversations in the processed-data boundary."""
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    conversations.to_csv(config.processed_dir / "conversations.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--brand", default=None)
    args = parser.parse_args()
    config = get_config(args.root)
    files = discover_files(config.raw_dir)
    if not files:
        print("No raw dataset found; nothing to reconstruct.")
        return
    output, counters = reconstruct_conversations(files[0], config, args.brand)
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    output.to_csv(config.processed_dir / "conversations.csv", index=False)
    print(json.dumps(counters, indent=2))


if __name__ == "__main__":
    main()
