# Hiver AmazonHelp Final Report

## Evaluation scope

The final evaluation used the existing AmazonHelp Golden file. It contained 200 rows, of which 196 had usable human intent and escalation labels; four skipped rows were excluded. No Golden data was used for training or retrieval.

Isolation checks passed:

- Duplicate conversation IDs: `0`
- Split leakage: `0`
- Training/retrieval source: Knowledge only
- LLM judge: unavailable because `OPENAI_API_KEY` was not configured

## Final metrics

| System | Accuracy | Macro F1 | Escalation accuracy |
|---|---:|---:|---:|
| Majority baseline | 0.015306 | 0.003350 | N/A |
| Original TF-IDF baseline | 0.081633 | 0.105836 | N/A |
| Balanced AmazonHelp agent | 0.096939 | 0.121689 | 0.392857 |

Balanced-agent per-intent F1:

| Intent | F1 |
|---|---:|
| delivery_delay | 0.095238 |
| delivery_tracking | 0.235294 |
| refund_return_or_cancellation | 0.089552 |
| prime_membership_or_benefits | 0.195122 |
| account_email_or_login | 0.000000 |
| payment_or_card_charge | 0.153846 |
| gift_card_or_promotion | 0.125000 |
| website_app_or_technical_issue | 0.166667 |
| other_or_unclear | 0.034483 |

The full confusion matrices are in `results/final_evaluation.csv` and `results/final_evaluation.md`.

## Interpretation

The balanced classifier is measurably better than the original TF-IDF baseline, but the headline accuracy must not be treated as agent quality. Macro F1 remains low, account/email/login has zero F1, and several intents still map heavily to `other_or_unclear` or delivery delay. Escalation accuracy is only `0.392857`, so intent improvement does not imply safe handling behavior. Response quality is unmeasured because the LLM judge was unavailable.

The detailed diagnosis, including five real Golden examples for each major failure pattern, is in [final_failure_analysis.md](final_failure_analysis.md).

## Current conclusion

The project has a reproducible Knowledge-only baseline comparison and a modest balanced-classifier improvement. It does not yet support a claim of reliable autonomous customer support. The next review should focus on intent coverage, semantic retrieval relevance, and escalation calibration before any production-style agent claim.