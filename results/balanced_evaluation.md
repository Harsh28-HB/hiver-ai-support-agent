# Balanced AmazonHelp Classifier Evaluation

Training uses Knowledge data only. Golden examples are evaluation-only.

- Original Knowledge rows: 85,315
- Balanced Knowledge rows: 26,781
- Maximum examples per intent: 6,000
- Golden labelled examples evaluated: 196
- Golden training leakage: 0

## Final training distribution

- `delivery_delay`: 6,000
- `delivery_tracking`: 1,646
- `refund_return_or_cancellation`: 5,059
- `prime_membership_or_benefits`: 2,453
- `account_email_or_login`: 2,152
- `payment_or_card_charge`: 1,040
- `gift_card_or_promotion`: 388
- `website_app_or_technical_issue`: 2,043
- `other_or_unclear`: 6,000

## Results

- Original TF-IDF accuracy: 0.081633
- Original TF-IDF macro F1: 0.105836
- Balanced TF-IDF accuracy: 0.096939
- Balanced TF-IDF macro F1: 0.121689
- Balanced per-intent F1: `{"account_email_or_login": 0.0, "delivery_delay": 0.095238, "delivery_tracking": 0.235294, "gift_card_or_promotion": 0.125, "other_or_unclear": 0.034483, "payment_or_card_charge": 0.153846, "prime_membership_or_benefits": 0.195122, "refund_return_or_cancellation": 0.089552, "website_app_or_technical_issue": 0.166667}`
- Balanced confusion matrix: `{"labels": ["delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits", "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion", "website_app_or_technical_issue", "other_or_unclear"], "matrix": [[2, 0, 0, 0, 1, 0, 0, 0, 3], [4, 4, 2, 3, 1, 1, 0, 1, 12], [9, 0, 3, 2, 1, 1, 3, 1, 38], [5, 0, 0, 4, 1, 0, 1, 1, 19], [7, 2, 3, 1, 0, 0, 0, 0, 19], [5, 0, 1, 0, 2, 2, 0, 2, 10], [3, 0, 0, 0, 0, 0, 1, 1, 6], [0, 0, 0, 0, 0, 0, 0, 1, 4], [1, 0, 0, 0, 0, 0, 0, 0, 2]]}`

The balanced training set caps only dominant classes and retains all available taxonomy intents. No Golden rows were used for selection or training.