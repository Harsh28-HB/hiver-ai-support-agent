# AmazonHelp Agent Evaluation

Evaluation uses only human-labelled golden rows. The agent trains and retrieves only from Knowledge data.

- Golden rows: 200
- Human-labelled rows evaluated: 196
- Duplicate conversation IDs: 0
- Split leakage: 0
- LLM judge: unavailable: OPENAI_API_KEY is not configured

## Metrics

### majority_class
- Accuracy: 0.015306
- Macro F1: 0.00335
- Escalation accuracy: not applicable
- Per-intent F1: `{"account_email_or_login": 0.0, "delivery_delay": 0.0, "delivery_tracking": 0.0, "gift_card_or_promotion": 0.0, "other_or_unclear": 0.030151, "payment_or_card_charge": 0.0, "prime_membership_or_benefits": 0.0, "refund_return_or_cancellation": 0.0, "website_app_or_technical_issue": 0.0}`
- Confusion matrix: `{"labels": ["delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits", "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion", "website_app_or_technical_issue", "other_or_unclear"], "matrix": [[0, 0, 0, 0, 0, 0, 0, 0, 6], [0, 0, 0, 0, 0, 0, 0, 0, 28], [0, 0, 0, 0, 0, 0, 0, 0, 58], [0, 0, 0, 0, 0, 0, 0, 0, 31], [0, 0, 0, 0, 0, 0, 0, 0, 32], [0, 0, 0, 0, 0, 0, 0, 0, 22], [0, 0, 0, 0, 0, 0, 0, 0, 11], [0, 0, 0, 0, 0, 0, 0, 0, 5], [0, 0, 0, 0, 0, 0, 0, 0, 3]]}`

### tfidf_logistic_regression
- Accuracy: 0.081633
- Macro F1: 0.105836
- Escalation accuracy: not applicable
- Per-intent F1: `{"account_email_or_login": 0.0, "delivery_delay": 0.102564, "delivery_tracking": 0.125, "gift_card_or_promotion": 0.125, "other_or_unclear": 0.032, "payment_or_card_charge": 0.153846, "prime_membership_or_benefits": 0.157895, "refund_return_or_cancellation": 0.089552, "website_app_or_technical_issue": 0.166667}`
- Confusion matrix: `{"labels": ["delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits", "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion", "website_app_or_technical_issue", "other_or_unclear"], "matrix": [[2, 0, 1, 0, 0, 0, 0, 0, 3], [4, 2, 1, 2, 1, 1, 0, 1, 16], [10, 0, 3, 1, 1, 1, 3, 1, 38], [3, 0, 0, 3, 1, 0, 1, 1, 22], [7, 2, 3, 1, 0, 0, 0, 0, 19], [3, 0, 1, 0, 2, 2, 0, 2, 12], [3, 0, 0, 0, 0, 0, 1, 1, 6], [0, 0, 0, 0, 0, 0, 0, 1, 4], [1, 0, 0, 0, 0, 0, 0, 0, 2]]}`

### amazonhelp_agent
- Accuracy: 0.081633
- Macro F1: 0.105836
- Escalation accuracy: 0.408163
- Per-intent F1: `{"account_email_or_login": 0.0, "delivery_delay": 0.102564, "delivery_tracking": 0.125, "gift_card_or_promotion": 0.125, "other_or_unclear": 0.032, "payment_or_card_charge": 0.153846, "prime_membership_or_benefits": 0.157895, "refund_return_or_cancellation": 0.089552, "website_app_or_technical_issue": 0.166667}`
- Confusion matrix: `{"labels": ["delivery_delay", "delivery_tracking", "refund_return_or_cancellation", "prime_membership_or_benefits", "account_email_or_login", "payment_or_card_charge", "gift_card_or_promotion", "website_app_or_technical_issue", "other_or_unclear"], "matrix": [[2, 0, 1, 0, 0, 0, 0, 0, 3], [4, 2, 1, 2, 1, 1, 0, 1, 16], [10, 0, 3, 1, 1, 1, 3, 1, 38], [3, 0, 0, 3, 1, 0, 1, 1, 22], [7, 2, 3, 1, 0, 0, 0, 0, 19], [3, 0, 1, 0, 2, 2, 0, 2, 12], [3, 0, 0, 0, 0, 0, 1, 1, 6], [0, 0, 0, 0, 0, 0, 0, 1, 4], [1, 0, 0, 0, 0, 0, 0, 0, 2]]}`
