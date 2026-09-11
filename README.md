Hiver AI Support Agent

An end-to-end AI-assisted customer support agent built for the Hiver SDE Intern assignment, focused on the AmazonHelp brand from the Customer Support on Twitter (TWCS) dataset.

The system reconstructs customer-support conversations, classifies incoming issues, retrieves relevant historical support evidence, recommends a grounded response, and decides whether the request should be AUTO-HANDLED or ESCALATED.

🚀 Live Demo

🌐 Try the Streamlit App

Open the Live Hiver AI Support Agent Demo

The live demo is hosted on Streamlit Community Cloud. It provides an interactive interface for entering AmazonHelp customer messages and viewing the agent's intent, confidence, decision, response, and historical evidence.

🔗 Project Links

Resource

Link

💻 GitHub Repository

Harsh28-HB/hiver-ai-support-agent

🌐 Live Streamlit Demo

Open Demo

📄 Final Report

Hiver AI Support Agent Final Report

📌 Project Overview

Customer-support data is noisy, conversational, and often contains overlapping issues. A useful support agent should therefore do more than assign a label.

This project implements a complete support workflow:

Customer Message
       ↓
Intent Classification
       ↓
Historical Knowledge Retrieval
       ↓
Evidence / Response Selection
       ↓
AUTO-HANDLE or ESCALATE
       ↓
Agent Response + Evidence

The system is designed around AmazonHelp and evaluates its decisions using a human-labelled Golden set.

Key capabilities

Conversation reconstruction from support tweets

AmazonHelp-specific intent classification

TF-IDF + Logistic Regression classification

Historical support-case retrieval using TF-IDF similarity

Evidence-based response recommendation

AUTO-HANDLE vs ESCALATE decisioning

Human-labelled Golden-set evaluation

Failure analysis and decision logging

Interactive Streamlit dashboard

CLI interface for direct agent testing

🎯 AmazonHelp Intent Taxonomy

The final taxonomy contains nine primary support intents:

delivery_delay

delivery_tracking

refund_return_or_cancellation

prime_membership_or_benefits

account_email_or_login

payment_or_card_charge

gift_card_or_promotion

website_app_or_technical_issue

other_or_unclear

Additional taxonomy decisions are documented in the project decision log.

🧠 Architecture

                         ┌─────────────────────────┐
                         │     Customer Message     │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │    Intent Classifier    │
                         │ TF-IDF + Logistic Reg.  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Historical Retrieval    │
                         │    TF-IDF Similarity    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Evidence + Response     │
                         │       Grounding         │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │    Decision Layer       │
                         │ AUTO-HANDLE / ESCALATE  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │    Streamlit / CLI      │
                         └─────────────────────────┘

1. Conversation reconstruction

The raw TWCS data is reconstructed into conversation-level examples so that customer messages and support responses can be evaluated in context.

2. Intent classification

The agent uses TF-IDF text features with Logistic Regression.

Failure analysis showed that the weakly labelled Knowledge data was heavily imbalanced. The later balanced approach was used to improve minority-intent learning without discarding most of the Knowledge data.

3. Historical retrieval

Historical Knowledge conversations are indexed using TF-IDF similarity. The agent retrieves relevant historical cases and exposes similarity information as supporting evidence.

4. Response grounding

The current response layer uses a retrieved historical support response as the basis for the recommended answer. It does not claim to be a fully autonomous production LLM response generator.

5. Escalation decision

The agent combines intent confidence and retrieval quality to decide whether a request can be automatically handled or should be escalated.

📊 Dataset

The project uses the Customer Support on Twitter (TWCS) dataset and focuses specifically on AmazonHelp.

The working pipeline produced:

Dataset Stage

Count

Reconstructed conversations

47,204

Multi-turn conversations

38,374

Knowledge examples

37,762

Validation examples

4,720

Golden split before annotation

4,722

Usable human-labelled Golden examples evaluated

196

Four Golden examples were skipped during annotation and were excluded from the final recorded evaluation.

The raw dataset is not committed to the public repository.

📈 Evaluation

The project compares a trivial majority-class baseline, a simple TF-IDF + Logistic Regression baseline, and the final balanced TF-IDF + Logistic Regression approach.

System

Accuracy

Macro F1

Majority baseline

1.53%

0.34%

TF-IDF + Logistic Regression

8.16%

10.58%

Balanced TF-IDF + Logistic Regression

9.69%

12.17%

The final balanced approach improved the recorded headline classification result over the simple TF-IDF baseline.

However, the absolute performance remains low, so these numbers are presented as prototype evaluation results, not production-readiness claims.

Additional recorded evaluation

Human-labelled Golden examples evaluated: 196

Duplicate Golden conversation IDs: 0

Conversation split leakage: 0

Recorded escalation accuracy: 0.408163

LLM judge: unavailable during the recorded evaluation because OPENAI_API_KEY was not configured

🔎 Failure Analysis

The project includes a detailed failure analysis based on real Golden-set examples.

Failure mode 1: Weak labels caused class collapse

The weakly labelled Knowledge data contained 55,700 of 85,315 rows (65.30%) labelled other_or_unclear.

The agent predicted other_or_unclear for 122 of 196 evaluated Golden examples, while only 3 Golden examples had that intent.

Hypothesis: the noisy class distribution created a strong class prior that overwhelmed minority intents.

Failure mode 2: Overlapping operational intents

Example:

Conversation 111811

Gold: refund_return_or_cancellation

Predicted: payment_or_card_charge

The customer described an order placed on the wrong card, an attempted cancellation, and a forced payment.

Hypothesis: several operational intents share words such as order, payment, cancellation, and delivery. A single-label TF-IDF classifier does not explicitly model multi-intent requests.

Failure mode 3: Unrelated retrieval evidence

Example:

Conversation 718348

The customer reported a $20 price discrepancy after one-click ordering.

Predicted intent: website_app_or_technical_issue

Similarity: 0.1675

Retrieved customer message: “Not really, lost my voice otherwise that would be an option.”

Hypothesis: lexical TF-IDF retrieval can produce weak semantic matches. Intent-conditioned reranking and evidence rejection should be added.

Failure mode 4: Excessive false escalations

Recorded escalation confusion:

Gold AUTO-HANDLE → predicted ESCALATE: 108

Gold AUTO-HANDLE → predicted AUTO-HANDLE: 34

Gold ESCALATE → predicted ESCALATE: 46

Gold ESCALATE → predicted AUTO-HANDLE: 8

Recorded escalation accuracy: 0.408163

Example:

Conversation 1016385

Gold decision: AUTO-HANDLE

Predicted: ESCALATE

Intent: correctly predicted delivery_delay

Confidence: 0.6156

Best similarity: 0.1522

Hypothesis: fixed confidence/retrieval gates reject some cases that human annotators consider handleable. Thresholds should be calibrated on a separately labelled validation set.

Failure mode 5: Incompatible historical response

Example:

Conversation 111811

The customer had a payment/cancellation problem, but the returned historical response discussed expedited shipping and email.

Hypothesis: retrieved responses require an answer-compatibility check before being reused. If the evidence does not address the customer's issue, the agent should not auto-handle the request.

⚠️ What Is Misleading About the Headline Number?

The final 9.69% intent accuracy is a useful recorded metric, but it should not be interpreted as the overall quality of the support agent.

It is limited because:

It is measured on only 196 usable human-labelled Golden examples.

Intent accuracy does not measure retrieval relevance.

Intent accuracy does not measure response compatibility.

Intent accuracy does not measure escalation quality.

The Knowledge training labels were noisy and heavily imbalanced.

The LLM judge was unavailable during the recorded evaluation.

The more accurate conclusion is:

The balanced classifier improved over the simple TF-IDF baseline in the recorded experiment, but the complete support agent remains a prototype with significant classification, retrieval, escalation, and response-grounding failure modes.

🧪 Demo Instructions

Live Demo

Open:

https://hiver-ai-support-agent-dzdycqjbhnahuo4ca837lh.streamlit.app/

Try messages such as:

My Amazon order was supposed to arrive yesterday and it still hasn't arrived.

Where can I track my Amazon package?

I want to cancel my order and get a refund.

The dashboard displays:

Predicted intent

Classifier confidence

AUTO-HANDLE / ESCALATE decision

Recommended response

Historical evidence

Similarity information

Decision rationale

Local Streamlit Demo

python -m streamlit run app.py

Open:

http://localhost:8501

CLI Demo

python run_agent.py --message "Where is my Amazon package?"

🛠️ Local Setup

Clone

git clone https://github.com/Harsh28-HB/hiver-ai-support-agent.git
cd hiver-ai-support-agent

Create virtual environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

macOS/Linux:

python -m venv .venv
source .venv/bin/activate

Install dependencies

python -m pip install -r requirements.txt

Run the agent

python run_agent.py --message "My Amazon order is late."

Run the UI

python -m streamlit run app.py

📁 Repository Structure

hiver-ai-support-agent/
│
├── app.py
├── run_agent.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│   └── core agent / classification / retrieval logic
│
├── tools/
│   ├── annotate_golden.py
│   ├── validate_golden.py
│   └── supporting tools
│
├── results/
│   ├── final_report.md
│   ├── final_failure_analysis.md
│   └── decision_log.md
│
└── data/
    ├── raw/
    └── processed/

Raw dataset files and generated processing artifacts are excluded from the public repository.

📝 Decision Log Summary

Important project decisions included:

Selected AmazonHelp as the target brand.

Defined a nine-intent taxonomy.

Merged wrong/damaged/missing item issues into refund_return_or_cancellation.

Kept delivery_tracking separate from delivery_delay.

Treated customer-service escalation/contact as an escalation attribute rather than a primary intent.

Created a human-labelled Golden evaluation set.

Compared against a majority baseline and TF-IDF + Logistic Regression baseline.

Rejected an earlier filtering strategy after it discarded most Knowledge data and reduced performance.

Used a balanced classifier approach.

Used historical conversations for retrieval-based evidence.

Added explicit AUTO-HANDLE / ESCALATE decisioning.

Added a Streamlit interface without changing the underlying agent logic.

Kept the raw dataset out of the public GitHub repository.

More detailed decisions are documented in results/decision_log.md.

🔮 What I Would Do With One More Week

Build a larger, stratified human-reviewed training subset.

Improve handling of other_or_unclear and minority intents.

Add intent-conditioned retrieval reranking.

Calibrate escalation thresholds using a separately labelled validation set.

Add response compatibility / entailment checks.

Enable and evaluate the LLM-as-judge component.

Measure agreement between automated judging and human ratings.

Expand per-intent and multi-intent Golden-set analysis.

Re-evaluate the full pipeline after each change while keeping the Golden set held out.

⚠️ Current Limitations

This is an assignment/research prototype, not a production customer-support system.

Current limitations include:

Low intent-classification performance on the human-labelled evaluation set.

Dependence on noisy weak labels for training.

TF-IDF retrieval can return semantically unrelated conversations.

Single-label classification does not explicitly handle multi-intent requests.

Threshold-based escalation can produce false positives and false negatives.

Response quality depends on the relevance of retrieved historical evidence.

The current response layer is retrieval-based rather than a fully autonomous production LLM workflow.

The LLM judge was unavailable during the recorded evaluation.

The raw TWCS dataset is not included in the repository.

🎯 Project Takeaway

This project demonstrates the complete support-agent workflow:

Data
  ↓
Conversation Reconstruction
  ↓
Human Golden Set
  ↓
Baselines
  ↓
Intent Classification
  ↓
Historical Retrieval
  ↓
Decisioning
  ↓
Response Grounding
  ↓
Evaluation
  ↓
Failure Analysis
  ↓
Interactive Demo

The goal was not to hide weak results behind a polished interface. The project makes the measured performance, concrete failure modes, design decisions, and next engineering steps explicit.

👤 Author

Harsh Biradar

GitHub: Harsh28-HB

Final Links

Repository: https://github.com/Harsh28-HB/hiver-ai-support-agent

Live Demo: https://hiver-ai-support-agent-dzdycqjbhnahuo4ca837lh.streamlit.app/