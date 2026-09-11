# Improved AmazonHelp Evaluation

- Golden labelled examples evaluated: 196
- Clean Knowledge training examples: 5,274
- Excluded ambiguous/low-confidence Knowledge examples: 80,041
- Golden training leakage: 0
- Original baseline artifacts were preserved.

## Original TF-IDF baseline
- Accuracy: 0.081633
- Macro F1: 0.105836
- Full per-intent F1 and confusion matrix: `results/baseline_results.csv`

## Improved classifier/agent intent component
- Accuracy: 0.076531
- Macro F1: 0.068655
- Escalation accuracy using unchanged retrieval and thresholds: 0.331633
- Per-intent F1: `{"account_email_or_login": 0.0, "delivery_delay": 0.066225, "delivery_tracking": 0.066667, "gift_card_or_promotion": 0.142857, "other_or_unclear": 0.0, "payment_or_card_charge": 0.08, "prime_membership_or_benefits": 0.173913, "refund_return_or_cancellation": 0.088235, "website_app_or_technical_issue": 0.0}`
- Confusion matrix: `{"labels": ["delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits", "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion", "website_app_or_technical_issue", "other_or_unclear"], "matrix": [[5, 0, 0, 0, 1, 0, 0, 0, 0], [18, 1, 2, 4, 1, 1, 0, 1, 0], [43, 0, 3, 5, 2, 1, 1, 3, 0], [23, 0, 0, 4, 1, 0, 1, 2, 0], [26, 1, 4, 1, 0, 0, 0, 0, 0], [13, 0, 1, 1, 3, 1, 0, 3, 0], [9, 0, 0, 0, 0, 0, 1, 1, 0], [5, 0, 0, 0, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0, 0, 0, 0]]}`

## Label policy
Only Knowledge customer messages with exactly one matched taxonomy intent and at least two high-confidence rule signals were used. Ambiguous and low-confidence examples were excluded; no examples were forced into `other_or_unclear`. The `other_or_unclear` class therefore has no automatically generated training examples.

These are deterministic weak-label results, not human-supervised Knowledge results. No Golden messages were used for label creation or training.