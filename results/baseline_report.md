# Baseline Evaluation Report

Training is restricted to Knowledge-only labels at `data/processed/knowledge_labels.csv`. Those labels are explicitly marked `label_source=weak_rule`; they are not human ground truth. Golden examples are evaluation-only.

- Golden examples: 200
- Human-labelled golden intents: 196
- Evaluation status: complete with weak Knowledge labels

Metrics are recorded in `baseline_results.csv`; they measure models trained on deterministic weak labels and evaluated on 196 human-labelled golden examples.
