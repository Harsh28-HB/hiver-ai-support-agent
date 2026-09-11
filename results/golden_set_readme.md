# AmazonHelp Golden Annotation Set

## Scope

This phase creates a 200-conversation human annotation set from the existing AmazonHelp `golden` split only. Knowledge and validation conversations were not used to select candidates. Reconstruction was not rerun.

The current processed artifact contains 4,761 golden conversations. The selected candidates are complete conversation IDs and are written to `data/golden/golden_candidates.csv`.

## Final taxonomy for annotation

Primary intent choices:

- `delivery_delay`: late, missing, delayed, or failed delivery.
- `delivery_tracking`: order status, dispatch, shipment, or tracking questions without a clear missed-delivery complaint.
- `refund_return_or_cancellation`: refund, return, cancellation, reimbursement, wrong, damaged, defective, or missing-item requests. The reviewed item-damage category is merged here.
- `prime_membership_or_benefits`: Prime membership, trial, renewal, or Prime benefit questions.
- `account_email_or_login`: account access, email, password, sign-in, or verification issues.
- `payment_or_card_charge`: payment, card, billing, or unexpected charge issues.
- `gift_card_or_promotion`: gift cards, vouchers, promotions, coupons, or redemption issues.
- `website_app_or_technical_issue`: Amazon website, app, checkout, or technical failures.
- `other_or_unclear`: insufficiently specified, multilingual/noisy, or unsupported requests.

`customer_service_contact_or_escalation` is not a primary intent. Annotators should record escalation separately using `human_escalation` as `AUTO-HANDLE` or `ESCALATE`.

## Sampling strategy

Candidates were sampled deterministically with seed `42` from conversations whose stored split is exactly `golden`. A non-binding `proposed_intent` hint was generated only from the candidate's customer message to diversify coverage; it is not a human label and must be accepted, corrected, or ignored by the annotator.

The sampler prioritizes coverage across observed intent-like themes, minority themes, ambiguous messages, and conversations with multiple turns. It removes normalized near-duplicates using normalized text and high-similarity text comparison. Every selected row retains one complete source conversation ID; no conversation is split across partitions.

The final CSV contains exactly 200 unique golden conversation IDs. `human_intent`, `human_escalation`, and `human_notes` are intentionally blank.

## Leakage prevention

- Candidate membership is checked against `split == golden` in `data/processed/conversations.csv`.
- Knowledge and validation rows are not eligible for sampling.
- No golden labels are used to discover or tune the taxonomy.
- The source conversation is kept intact, while annotation focuses on the first customer request and its historical response.
- Near-duplicate customer messages are filtered within the golden candidate pool.

## Annotation workflow

Launch the resumable terminal tool from the repository root:

```powershell
python tools/annotate_golden.py
```

For each example, choose an intent number, choose `a` for `AUTO-HANDLE` or `e` for `ESCALATE`, and optionally add notes. Progress is saved after every annotation to `data/golden/golden_set.csv`. Use `q` to save and quit; rerunning the command resumes pending rows.

The tool displays the non-binding proposed hint, prior context, customer message, and historical AmazonHelp response. Human decisions must be based on the reviewed taxonomy and the conversation evidence, not blindly copied from the hint.
