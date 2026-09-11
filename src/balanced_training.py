"""Build a deterministic, capped Knowledge training set for the existing classifier."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .baselines import FINAL_INTENTS, knowledge_label_path

MAX_PER_INTENT = 6_000
SEED = 42
OUTPUT_NAME = "balanced_knowledge_labels.csv"


def _stable_key(row: pd.Series) -> str:
    value = f"{SEED}:{row.get('conversation_id', '')}:{row.get('customer_message', '')}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_balanced_training(root: Path, max_per_intent: int = MAX_PER_INTENT) -> tuple[Path, pd.DataFrame]:
    """Cap only dominant classes while retaining all available taxonomy intents."""
    source = knowledge_label_path(root)
    frame = pd.read_csv(source, dtype=str).fillna("")
    frame = frame[
        frame["human_intent"].isin(FINAL_INTENTS)
        & frame["customer_message"].str.strip().ne("")
    ].copy()
    frame["_stable_key"] = frame.apply(_stable_key, axis=1)
    selected: list[pd.DataFrame] = []
    for intent in FINAL_INTENTS:
        group = frame[frame["human_intent"].eq(intent)].sort_values("_stable_key")
        if group.empty:
            continue
        selected.append(group.head(max_per_intent))
    balanced = pd.concat(selected, ignore_index=True).drop(columns=["_stable_key"])
    output = root / "data" / "processed" / OUTPUT_NAME
    balanced.to_csv(output, index=False)
    return output, balanced


if __name__ == "__main__":
    import argparse
    from .config import get_config

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    output, balanced = build_balanced_training((args.root or get_config().root).resolve())
    print(f"Wrote {output}")
    print(balanced["human_intent"].value_counts().sort_index().to_string())
