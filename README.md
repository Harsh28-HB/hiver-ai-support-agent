# Hiver AmazonHelp Support Intelligence Agent

Reproducible support-intelligence pipeline for the Hiver SDE Intern take-home assignment. It uses Customer Support on Twitter to select AmazonHelp, reconstruct conversations, derive an exploratory taxonomy, annotate a Golden set, compare intent baselines, and evaluate a local retrieval-grounded support agent.

This is an evaluated research prototype, not a production support system. Final metrics show modest intent performance and weak escalation performance; response quality was not LLM-judged because no API key was configured.

## Problem Statement

The system should classify AmazonHelp customer messages, retrieve similar historical conversations, ground replies in historical support behavior, and decide whether to auto-handle or escalate with an explicit reason. Banking77 is out of scope. The primary dataset is Kaggle's [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).

## AmazonHelp Selection

The export contained `2,811,774` rows and seven columns: `tweet_id`, `author_id`, `inbound`, `created_at`, `text`, `response_tweet_id`, and `in_response_to_tweet_id`. Brands are outbound `author_id` accounts because the dataset has no brand column.

AmazonHelp was selected using support volume, linked customer-response evidence, and text coverage. Strong alternatives included AppleSupport, Uber_Support, AmericanAir, and SpotifyCares. Reconstruction produced `47,204` usable AmazonHelp conversations, including `38,374` multi-turn conversations.

## Architecture

```text
raw CSV -> schema inspection -> brand ranking -> reply-graph reconstruction
	-> Knowledge / Validation / Golden conversation splits
	-> taxonomy discovery and human Golden annotation
	-> baselines and Knowledge-only TF-IDF classifier
	-> Knowledge-only TF-IDF retrieval -> grounded reply and escalation
```

- `src/data_inspection.py`: schema, missingness, duplicates, and relationship inspection.
- `src/brand_analysis.py`: outbound support-account ranking.
- `src/conversations.py`: chronological explicit-link reconstruction.
- `src/intent_discovery.py`: Knowledge-only taxonomy discovery.
- `src/golden_sampling.py`: deterministic Golden sampling and validation.
- `src/baselines.py`: majority and TF-IDF + Logistic Regression baselines.
- `src/balanced_training.py`: deterministic capped Knowledge training artifact.
- `src/agent.py`: Knowledge-only intent, retrieval, reply, and escalation logic.
- `run_agent.py`: local command-line agent.

## Data Pipeline

The pipeline inspects the actual CSV, identifies outbound support accounts, reconstructs connected reply components from tweet IDs, removes unusable records, and assigns complete conversations to Knowledge, Validation, or Golden. Raw data remains untouched. Evaluation must truncate conversations before target brand responses to prevent future-response leakage.

## Final Intent Taxonomy

`delivery_delay`, `delivery_tracking`, `refund_return_or_cancellation` (including wrong/damaged/defective/missing items), `prime_membership_or_benefits`, `account_email_or_login`, `payment_or_card_charge`, `gift_card_or_promotion`, `website_app_or_technical_issue`, and `other_or_unclear`.

Customer-service contact/escalation is a separate escalation attribute, not a primary intent.

## Golden-Set Methodology

Exactly 200 unique complete conversations were sampled from the existing Golden split with deterministic near-duplicate filtering. The final file has 196 usable human-labelled examples and four skipped examples. Golden messages were never used for training or retrieval; duplicate IDs and split leakage were zero.

Validate annotations with:

```powershell
python tools/validate_golden.py
```

## Baselines and Final Metrics

All final metrics use 196 labelled Golden examples.

| System | Accuracy | Macro F1 | Escalation accuracy |
|---|---:|---:|---:|
| Majority baseline | 0.015306 | 0.003350 | N/A |
| Original TF-IDF + Logistic Regression | 0.081633 | 0.105836 | N/A |
| Balanced AmazonHelp agent | 0.096939 | 0.121689 | 0.392857 |

Balanced-agent per-intent F1: delivery delay `0.095238`, delivery tracking `0.235294`, refund/return/cancellation `0.089552`, Prime `0.195122`, account/email/login `0.000000`, payment/card `0.153846`, gift card/promotion `0.125000`, website/app/technical `0.166667`, and other/unclear `0.034483`.

The headline accuracy is not sufficient: macro F1 remains low, account/email/login has zero F1, and escalation accuracy is only `0.392857`. The LLM judge was unavailable because `OPENAI_API_KEY` was not configured.

Important artifacts:

- [results/final_report.md](results/final_report.md)
- [results/final_failure_analysis.md](results/final_failure_analysis.md)
- [results/decision_log.md](results/decision_log.md)
- [results/final_evaluation.csv](results/final_evaluation.csv)
- [results/final_evaluation.md](results/final_evaluation.md)

## Failure Analysis

The five main patterns are residual collapse into `other_or_unclear`, delivery vocabulary dominating unrelated issues, unrecognized account/email/login messages, generic TF-IDF retrieval neighbors, and poorly calibrated escalation/direct response copying. Real Golden examples and evidence are documented in [results/final_failure_analysis.md](results/final_failure_analysis.md).

## Quickstart

Run from the repository root in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_agent.py --message "My order is late"
python tools/validate_golden.py
python -m compileall -q src evaluation tools run_agent.py run_pipeline.py
```

For a fresh raw-data reproduction, place the Kaggle export at `data/raw/twcs.csv` and run:

```powershell
python run_pipeline.py
```

The local agent returns JSON containing `intent`, `confidence`, top-three `retrieved_evidence`, `reply`, `decision`, and `reason`. It uses Knowledge-only local TF-IDF components and does not require an LLM API key.

## Project Structure

```text
hiver-ai-support-agent/
|-- data/raw/                 # local raw export; ignored by Git
|-- data/processed/           # generated working data; ignored by Git
|-- data/golden/              # human annotation files
|-- src/                      # inspection, reconstruction, models, agent
|-- evaluation/               # baseline and final evaluation scripts
|-- tools/                    # annotation and validation tools
|-- results/                  # reports and final evaluation artifacts
|-- run_agent.py
|-- run_pipeline.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

## Remaining Issues

The workspace is not initialized as a Git repository, so tracked-file status could not be verified. The raw 516 MB dataset is intentionally excluded. The LLM judge remains unavailable, and retrieval relevance, escalation calibration, and minority-intent coverage remain weak.
