"""Memory-conscious inspection of the Customer Support on Twitter export."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, get_config

LOGGER = logging.getLogger(__name__)
SUPPORTED_SUFFIXES = {".csv", ".tsv", ".txt"}

FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "text": ("text", "tweet", "message", "body", "content", "full_text"),
    "tweet_id": ("tweet_id", "status_id", "id"),
    "author": ("author", "user", "screen_name", "username", "sender", "from"),
    "direction": ("inbound", "outbound", "direction", "in_reply", "incoming", "response"),
    "reply_relationship": ("in_reply_to", "reply", "response_to", "parent", "referenced"),
    "conversation": ("conversation", "thread", "conversation_id", "thread_id"),
    "timestamp": ("created_at", "timestamp", "time", "date"),
    "brand": ("brand", "company", "account", "business", "organization"),
}


def discover_files(raw_dir: Path) -> list[Path]:
    """Return likely tabular files, excluding hidden marker files."""
    return sorted(
        path for path in raw_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES and not path.name.startswith(".")
    ) if raw_dir.exists() else []


def _read_header(path: Path) -> list[str]:
    try:
        return list(pd.read_csv(path, nrows=0, **_reader_options(path)).columns)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        LOGGER.warning("Could not read header for %s: %s", path.name, exc)
        return []


def _read_sample(path: Path, rows: int) -> pd.DataFrame:
    return pd.read_csv(path, nrows=rows, on_bad_lines="skip", **_reader_options(path))


def _reader_options(path: Path) -> dict[str, Any]:
    """Use the fast parser when the file extension provides an unambiguous delimiter."""
    if path.suffix.lower() == ".csv":
        return {"sep": ",", "engine": "c"}
    if path.suffix.lower() == ".tsv":
        return {"sep": "\t", "engine": "c"}
    return {"sep": None, "engine": "python"}


def _candidate_columns(columns: list[str]) -> dict[str, list[str]]:
    candidates: dict[str, list[str]] = {}
    for role, patterns in FIELD_PATTERNS.items():
        matches = [column for column in columns if any(re.search(pattern, column.lower()) for pattern in patterns)]
        candidates[role] = matches
    return candidates


def inspect_file(path: Path, config: PipelineConfig) -> dict[str, Any]:
    """Inspect one file in chunks and return JSON/Markdown-friendly metadata."""
    header = _read_header(path)
    if not header:
        return {"filename": path.name, "file_size_bytes": path.stat().st_size, "error": "Unreadable header"}

    sample = _read_sample(path, config.sample_rows)
    counts: dict[str, int] = {column: 0 for column in header}
    duplicates = 0
    duplicate_count = 0
    seen_tweet_ids: set[str] = set()
    row_count = 0
    inbound_count = 0
    outbound_count = 0
    unique_authors: set[str] = set()
    for chunk in pd.read_csv(path, chunksize=config.chunk_size, on_bad_lines="skip", **_reader_options(path)):
        row_count += len(chunk)
        duplicates += int(chunk.duplicated().sum())
        if "tweet_id" in chunk:
            tweet_ids = chunk["tweet_id"].dropna().astype(str)
            duplicate_count += int(tweet_ids.isin(seen_tweet_ids).sum())
            seen_tweet_ids.update(tweet_ids)
        if "inbound" in chunk:
            inbound_count += int(chunk["inbound"].eq(True).sum())
            outbound_count += int(chunk["inbound"].eq(False).sum())
        if "author_id" in chunk:
            unique_authors.update(chunk["author_id"].dropna().astype(str))
        for column in header:
            counts[column] += int(chunk[column].isna().sum())

    missingness = {column: round((value / row_count) * 100, 3) if row_count else None for column, value in counts.items()}
    return {
        "filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "row_count": row_count,
        "columns": header,
        "dtypes": {column: str(sample[column].dtype) for column in sample.columns},
        "missing_value_percentages": missingness,
        "duplicate_count": duplicate_count + duplicates,
        "unique_author_count": len(unique_authors),
        "inbound_count": inbound_count,
        "outbound_count": outbound_count,
        "representative_rows": json.loads(sample.head(config.max_representative_rows).to_json(orient="records", date_format="iso")),
        "candidate_columns": _candidate_columns(header),
        "sample_unique_values": {
            column: [value for value in sample[column].dropna().astype(str).drop_duplicates().head(10)]
            for column in header
        },
    }


def inspect_dataset(config: PipelineConfig) -> dict[str, Any]:
    """Inspect all supported raw files without loading any full file at once."""
    files = discover_files(config.raw_dir)
    reports = []
    for path in files:
        LOGGER.info("Inspecting %s (%d bytes)", path.name, path.stat().st_size)
        reports.append(inspect_file(path, config))
    return {"raw_directory": str(config.raw_dir), "files": reports}


def print_report(report: dict[str, Any]) -> None:
    print(json.dumps(report, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = inspect_dataset(get_config(args.root))
    if not report["files"]:
        print("No CSV/TSV/TXT files found in data/raw. Add the Kaggle export and rerun.")
    print_report(report)


if __name__ == "__main__":
    main()
