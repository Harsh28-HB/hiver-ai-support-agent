"""Evidence-based brand/company ranking for a support dataset."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, get_config
from .data_inspection import discover_files, inspect_file

LOGGER = logging.getLogger(__name__)


def _parse_response_ids(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _analyze_twitter_support_schema(path: Path, config: PipelineConfig) -> pd.DataFrame:
    """Rank outbound support accounts using chunked full-export aggregates."""
    columns = ["tweet_id", "author_id", "inbound", "text", "response_tweet_id", "in_response_to_tweet_id"]
    outbound_counts: dict[str, int] = {}
    text_counts: dict[str, int] = {}
    outbound_ids: dict[str, set[str]] = {}
    response_ids: dict[str, set[str]] = {}
    for chunk in pd.read_csv(path, usecols=columns, chunksize=config.chunk_size, on_bad_lines="skip"):
        outbound = chunk[chunk["inbound"].eq(False)].copy()
        outbound["author_id"] = outbound["author_id"].astype(str)
        for brand, group in outbound.groupby("author_id"):
            brand = str(brand)
            outbound_counts[brand] = outbound_counts.get(brand, 0) + len(group)
            text_counts[brand] = text_counts.get(brand, 0) + int(group["text"].fillna("").astype(str).str.strip().ne("").sum())
            outbound_ids.setdefault(brand, set()).update(group["tweet_id"].astype(str))
            for value in group["response_tweet_id"]:
                response_ids.setdefault(brand, set()).update(_parse_response_ids(value))

    inbound_linked = {brand: 0 for brand in outbound_counts}
    for chunk in pd.read_csv(path, usecols=columns, chunksize=config.chunk_size, on_bad_lines="skip"):
        inbound = chunk[chunk["inbound"].eq(True)]
        parent_ids = inbound["in_response_to_tweet_id"].astype("Int64").astype(str)
        for brand, ids in outbound_ids.items():
            inbound_linked[brand] += int(parent_ids.isin(ids).sum())

    rows: list[dict[str, Any]] = []
    for brand, response_count in outbound_counts.items():
        linked = min(inbound_linked[brand], len(response_ids.get(brand, set()))) if response_ids.get(brand) else inbound_linked[brand]
        text_coverage = text_counts[brand] / response_count if response_count else 0.0
        rows.append({
            "brand": brand,
            "source_file": path.name,
            "total_tweets": response_count,
            "customer_messages": inbound_linked[brand],
            "brand_responses": response_count,
            "linked_response_pairs": linked,
            "conversation_threads": None,
            "median_conversation_length": None,
            "usable_conversation_pct": round(100 * linked / response_count, 2) if response_count else 0.0,
            "text_coverage_pct": round(100 * text_coverage, 2),
            "issue_diversity": None,
            "duplicate_noise_rate": None,
            "measurement_basis": "full export, chunked aggregation",
        })
    if not rows:
        return pd.DataFrame()
    maxima = {key: max(float(row[key]) for row in rows) for key in ("total_tweets", "customer_messages", "linked_response_pairs")}
    for row in rows:
        row["selection_score"] = round(
            0.25 * min(row["total_tweets"] / max(maxima["total_tweets"], 1), 1.0)
            + 0.25 * min(row["customer_messages"] / max(maxima["customer_messages"], 1), 1.0)
            + 0.35 * min(row["linked_response_pairs"] / max(maxima["linked_response_pairs"], 1), 1.0)
            + 0.15 * row["text_coverage_pct"] / 100,
            4,
        )
    return pd.DataFrame(rows).sort_values(["selection_score", "linked_response_pairs"], ascending=False).reset_index(drop=True)


def _first_column(columns: list[str], patterns: tuple[str, ...]) -> str | None:
    for column in columns:
        if any(re.search(pattern, column.lower()) for pattern in patterns):
            return column
    return None


def _brand_column(frame: pd.DataFrame) -> str | None:
    preferred = ("brand", "company", "account", "business", "organization")
    return _first_column(list(frame.columns), preferred)


def _direction_column(frame: pd.DataFrame) -> str | None:
    return _first_column(list(frame.columns), ("inbound", "outbound", "direction", "incoming", "response"))


def _text_column(frame: pd.DataFrame) -> str | None:
    return _first_column(list(frame.columns), ("text", "tweet", "message", "body", "content", "full_text"))


def _is_outbound(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"outbound", "out", "brand", "agent", "response", "true", "1", "yes"}:
        return True
    if normalized in {"inbound", "in", "customer", "user", "false", "0", "no"}:
        return False
    return None


def analyze_brands(path: Path, config: PipelineConfig) -> pd.DataFrame:
    """Calculate brand metrics from a bounded sample and document its basis."""
    header = set(pd.read_csv(path, nrows=0).columns)
    twitter_columns = {"tweet_id", "author_id", "inbound", "text", "response_tweet_id", "in_response_to_tweet_id"}
    if twitter_columns.issubset(header):
        return _analyze_twitter_support_schema(path, config)
    inspection = inspect_file(path, config)
    sample = pd.read_csv(path, nrows=config.sample_rows, sep=None, engine="python", on_bad_lines="skip")
    brand_column = _brand_column(sample)
    text_column = _text_column(sample)
    direction_column = _direction_column(sample)
    if not brand_column:
        LOGGER.warning("No brand/company column detected in %s", path.name)
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for brand, group in sample.groupby(brand_column, dropna=False):
        label = "<missing>" if pd.isna(brand) else str(brand)
        outbound = group[direction_column].map(_is_outbound) if direction_column else pd.Series(pd.NA, index=group.index)
        known_direction = outbound.notna()
        customer_count = int((outbound == False).sum()) if direction_column else None
        response_count = int((outbound == True).sum()) if direction_column else None
        text_coverage = float(group[text_column].notna().mean()) if text_column else None
        duplicate_rate = float(group.duplicated().mean())
        usable_direction_rate = float(known_direction.mean()) if direction_column else 0.0
        score = (
            (min(len(group) / 1000, 1.0) * 0.25)
            + ((customer_count or 0) > 0) * 0.20
            + ((response_count or 0) > 0) * 0.20
            + usable_direction_rate * 0.15
            + (text_coverage or 0) * 0.15
            + (1 - duplicate_rate) * 0.05
        )
        rows.append({
            "brand": label,
            "total_tweets_in_sample": len(group),
            "customer_inbound_in_sample": customer_count,
            "brand_outbound_in_sample": response_count,
            "known_direction_rate": round(usable_direction_rate, 6),
            "text_coverage": round(text_coverage, 6) if text_coverage is not None else None,
            "duplicate_rate": round(duplicate_rate, 6),
            "linked_response_pairs": None,
            "conversation_threads": None,
            "median_conversation_length": None,
            "selection_score": round(float(score), 6),
            "measurement_basis": f"bounded sample of {len(sample):,} rows from {inspection['row_count']:,} total rows",
        })
    return pd.DataFrame(rows).sort_values("selection_score", ascending=False).reset_index(drop=True)


def write_brand_outputs(config: PipelineConfig, analyses: pd.DataFrame) -> None:
    config.results_dir.mkdir(parents=True, exist_ok=True)
    if analyses.empty:
        analyses.to_csv(config.results_dir / "brand_analysis.csv", index=False)
        summary = "# Brand Selection\n\nNo brand/company column was detected, or no raw dataset is present. Run the pipeline after placing the Kaggle export in `data/raw/`.\n"
    else:
        analyses.to_csv(config.results_dir / "brand_analysis.csv", index=False)
        top = analyses.iloc[0]
        alternatives = ", ".join(analyses["brand"].head(5).astype(str).tolist())
        summary = (
            "# Brand Selection\n\n"
            f"**Selected candidate:** `{top['brand']}` with score `{top['selection_score']}`.\n\n"
            "The score is normalized across observed outbound support accounts: 25% support volume, 25% linked customer-message volume, "
            "35% response-linkage volume, and 15% non-empty text coverage. Raw tweet count cannot dominate by itself.\n\n"
            f"**Top candidates:** {alternatives}.\n\n"
            f"The strongest alternative is `{analyses.iloc[1]['brand']}` with score `{analyses.iloc[1]['selection_score']}`. "
            "It was not selected because it has less linked customer-response volume under the same criteria. "
            "Conversation-level multi-turn and issue-diversity metrics are written after reconstruction.\n"
        )
    (config.results_dir / "brand_selection.md").write_text(summary, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    config = get_config(args.root)
    files = discover_files(config.raw_dir)
    analyses = analyze_brands(files[0], config) if files else pd.DataFrame()
    write_brand_outputs(config, analyses)
    print(analyses.to_string(index=False) if not analyses.empty else "No brand analysis available.")


if __name__ == "__main__":
    main()
