# Classifier Diagnosis

## Root cause

The improved classifier performed worse because the strict high-confidence filter removed too much useful training data and changed the training distribution away from the Golden distribution.

It reduced Knowledge training examples from **85,315 to 5,274**, removing **80,041 examples (93.82%)**. The filter retained only examples with exactly one matched intent and at least two rule signals. This increased label purity mechanically, but left the model with sparse and incomplete coverage of the actual customer language.

The most important consequence is that the improved training set contains **zero `other_or_unclear` examples**, even though the Golden set contains 3 such examples. More broadly, minority classes became extremely small, especially `gift_card_or_promotion` with only 41 examples and `delivery_tracking` with only 136.

## Training-label distributions

| Intent | Original Knowledge labels | Original % | Improved clean labels | Improved % | Golden labels | Golden % |
|---|---:|---:|---:|---:|---:|---:|
| delivery_delay | 14,834 | 17.39% | 2,916 | 55.28% | 6 | 3.06% |
| delivery_tracking | 1,646 | 1.93% | 136 | 2.58% | 28 | 14.29% |
| refund_return_or_cancellation | 5,059 | 5.93% | 657 | 12.46% | 58 | 29.59% |
| prime_membership_or_benefits | 2,453 | 2.88% | 542 | 10.28% | 31 | 15.82% |
| account_email_or_login | 2,152 | 2.52% | 468 | 8.87% | 32 | 16.33% |
| payment_or_card_charge | 1,040 | 1.22% | 219 | 4.15% | 22 | 11.22% |
| gift_card_or_promotion | 388 | 0.45% | 41 | 0.78% | 11 | 5.61% |
| website_app_or_technical_issue | 2,043 | 2.39% | 295 | 5.60% | 5 | 2.55% |
| other_or_unclear | 55,700 | 65.30% | 0 | 0.00% | 3 | 1.53% |
| **Total** | **85,315** | **100%** | **5,274** | **100%** | **196** | **100%** |

The original set was badly dominated by `other_or_unclear`, but it at least contained broad language coverage. The improved set overcorrected: it removed the dominant noisy class entirely and also removed most examples for every concrete class. Class balancing in Logistic Regression cannot recover lexical coverage that was discarded before training.

## Metrics comparison

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| Original TF-IDF baseline | 0.081633 | 0.105836 |
| Improved strict-label classifier | 0.076531 | 0.068655 |
| Change | -0.005102 | -0.037181 |

Both evaluations used the same 196 human-labelled Golden examples. The Golden set itself was not modified.

## Per-intent F1

| Intent | Original F1 | Improved F1 | Change |
|---|---:|---:|---:|
| delivery_delay | 0.102564 | 0.066225 | -0.036339 |
| delivery_tracking | 0.125000 | 0.066667 | -0.058333 |
| refund_return_or_cancellation | 0.089552 | 0.088235 | -0.001317 |
| prime_membership_or_benefits | 0.157895 | 0.173913 | +0.016018 |
| account_email_or_login | 0.000000 | 0.000000 | +0.000000 |
| payment_or_card_charge | 0.153846 | 0.080000 | -0.073846 |
| gift_card_or_promotion | 0.125000 | 0.142857 | +0.017857 |
| website_app_or_technical_issue | 0.166667 | 0.000000 | -0.166667 |
| other_or_unclear | 0.032000 | 0.000000 | -0.032000 |

The improved model gained slightly on Prime and gift-card examples, but lost on delivery, payment, website/technical, and `other_or_unclear`. The complete loss of website/technical F1 and the disappearance of `other_or_unclear` support the coverage-loss explanation.

## Confusion-matrix evidence

Original TF-IDF baseline rows are ordered by the approved taxonomy. The largest error pattern was collapse into `other_or_unclear`, including:

- Refund/return/cancellation: 38 of 58 predicted as `other_or_unclear`
- Prime membership: 22 of 31 predicted as `other_or_unclear`
- Account/email/login: 19 of 32 predicted as `other_or_unclear`
- Delivery tracking: 16 of 28 predicted as `other_or_unclear`
- Payment/card: 12 of 22 predicted as `other_or_unclear`

The improved confusion matrix removed that destination entirely, but did not become more accurate. Instead, it concentrated predictions into `delivery_delay`:

- 43 refund/return examples predicted as delivery delay
- 26 account/email/login examples predicted as delivery delay
- 23 Prime examples predicted as delivery delay
- 18 delivery-tracking examples predicted as delivery delay
- 13 payment/card examples predicted as delivery delay

This is a different failure mode: the improved model no longer collapses into `other_or_unclear`, but its much smaller and delivery-heavy clean training set makes `delivery_delay` the dominant learned region.

## Single recommended fix

Create a **manually reviewed, stratified Knowledge training subset** rather than training on the strict rule-filtered rows alone. Keep high-confidence weak labels as candidate suggestions, but review enough examples from every approved intent, including a deliberately reviewed `other_or_unclear` sample, before retraining. This directly addresses both coverage loss and distribution mismatch without using Golden examples for training.

No Golden labels, taxonomy, or original baseline artifacts were modified.
