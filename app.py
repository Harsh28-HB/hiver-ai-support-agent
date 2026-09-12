"""Streamlit interface for the existing AmazonHelp support agent."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from src.agent import AmazonHelpAgent

ROOT = Path(__file__).resolve().parent
REQUIRED_AGENT_ARTIFACTS = (
    ROOT / "data" / "processed" / "conversations.csv",
    ROOT / "data" / "processed" / "knowledge_labels.csv",
)
EXAMPLES = {
    "Delivery delay": "My Amazon order was supposed to arrive yesterday and it still hasn't arrived.",
    "Track an order": "Where can I track my order?",
    "Refund or cancellation": "I want to cancel my order and get a refund.",
    "Payment issue": "I was charged the wrong amount on my card.",
    "Account access": "I cannot log in to my Amazon account.",
}

st.set_page_config(
    page_title="AmazonHelp AI Support Intelligence",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#17212b; --muted:#667482; --line:#dce4e8; --blue:#146ef5; --blue-soft:#eaf2ff; --green:#11845b; --green-soft:#e9f8f1; --amber:#9a6500; --amber-soft:#fff5dd; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
    .block-container { max-width: 1220px; padding-top: 2rem; padding-bottom: 4rem; }
    .hero { border-bottom: 1px solid var(--line); padding: 0 0 1.4rem; margin-bottom: 1.5rem; }
    .eyebrow { color: var(--blue); font-size: .76rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1.02; margin: .4rem 0 .65rem; }
    .hero p { color: var(--muted); font-size: 1rem; max-width: 720px; margin: 0; }
    .panel { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 1.25rem; box-shadow: 0 8px 25px rgba(30, 51, 65, .05); }
    .metric { background: #f7fafb; border: 1px solid var(--line); border-radius: 12px; padding: 1rem; min-height: 100px; }
    .metric-label { color: var(--muted); font-size: .76rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    .metric-value { color: #17212b !important; font-family: 'Space Grotesk', sans-serif; font-size: 1.45rem; font-weight: 700; line-height: 1.2; margin-top: .45rem; overflow-wrap: anywhere; }
    .metric-sub { color: var(--muted); font-size: .8rem; margin-top: .25rem; }
    .response { background: #17212b; border-radius: 14px; color: #f7fbfd; padding: 1.5rem; margin: .6rem 0 1rem; }
    .response-label { color: #a9c9ff; font-size: .75rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
    .response-text { font-size: 1.12rem; line-height: 1.55; margin-top: .7rem; }
    .evidence-card { border-left: 3px solid var(--blue); background: #f7fafb; border-radius: 0 10px 10px 0; padding: .9rem 1rem; margin: .7rem 0; }
    .evidence-meta { color: var(--blue); font-size: .78rem; font-weight: 700; }
    .evidence-text { font-size: .92rem; line-height: 1.45; margin-top: .35rem; }
    .evidence-response { color: var(--muted); font-size: .86rem; line-height: 1.45; margin-top: .4rem; }
    .section-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 600; margin: 1.2rem 0 .7rem; }
    [data-testid="stSidebar"] { background: #f5f8fa; border-right: 1px solid var(--line); }
    [data-testid="stFormSubmitButton"] button, .stButton button { border-radius: 9px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading Knowledge-only support intelligence...")
def load_agent() -> AmazonHelpAgent:
    _ensure_agent_artifacts()
    return AmazonHelpAgent(ROOT)


def _ensure_agent_artifacts() -> None:
    """Build missing runtime artifacts using the existing repository pipeline."""
    missing = [path for path in REQUIRED_AGENT_ARTIFACTS if not path.exists()]
    if not missing:
        return
    raw_files = sorted((ROOT / "data" / "raw").glob("*.csv"))
    if not raw_files:
        names = ", ".join(path.relative_to(ROOT).as_posix() for path in missing)
        raise RuntimeError(
            f"Required agent artifacts are missing ({names}), and no CSV exists in data/raw/ "
            "to rebuild them. Add the dataset to the deployment or include the processed artifacts."
        )
    try:
        if not (ROOT / "data" / "processed" / "conversations.csv").exists():
            subprocess.run(
                [sys.executable, "run_pipeline.py"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        if not (ROOT / "data" / "processed" / "knowledge_labels.csv").exists():
            subprocess.run(
                [sys.executable, "-m", "src.create_knowledge_labels"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "pipeline failed").strip()[-1000:]
        raise RuntimeError(f"Could not rebuild agent artifacts: {detail}") from error


@st.cache_data
def load_metrics() -> pd.DataFrame:
    return pd.read_csv(ROOT / "results" / "final_evaluation.csv", dtype=str).fillna("")


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Amazon customer support intelligence</div>
      <h1>AmazonHelp AI Support Intelligence</h1>
      <p>Analyze a customer request, find the closest historical support cases, and inspect the evidence behind the recommended handling decision.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Evaluation snapshot")
    try:
        metrics = load_metrics()
        row = metrics[metrics["system"].eq("balanced_amazonhelp_agent")].iloc[0]
        st.metric("Accuracy", f"{float(row['accuracy']):.1%}")
        st.metric("Macro F1", f"{float(row['macro_f1']):.3f}")
        st.metric("Escalation accuracy", f"{float(row['escalation_accuracy']):.1%}")
        st.caption("196 labelled Golden examples. Knowledge-only training and retrieval. LLM judge unavailable.")
    except Exception as error:
        st.warning(f"Evaluation metrics unavailable: {error}")
    st.markdown("### Example requests")
    for label, prompt in EXAMPLES.items():
        if st.button(label, use_container_width=True):
            st.session_state["message"] = prompt

message = st.text_area(
    "Customer message",
    value=st.session_state.get("message", ""),
    height=130,
    placeholder="Describe the customer's issue...",
    label_visibility="visible",
)

if st.button("Analyze request", type="primary", use_container_width=False):
    if not message.strip():
        st.warning("Enter a customer message to analyze.")
    else:
        try:
            with st.spinner("Analyzing Knowledge evidence..."):
                result = load_agent().respond(message)
            st.markdown('<div class="section-title">Decision summary</div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric"><div class="metric-label">Intent</div><div class="metric-value">{}</div><div class="metric-sub">Predicted support category</div></div>'.format(result["intent"]), unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric"><div class="metric-label">Confidence</div><div class="metric-value">{:.1%}</div><div class="metric-sub">Classifier confidence</div></div>'.format(result["confidence"]), unsafe_allow_html=True)
            with col3:
                decision_class = "green" if result["decision"] == "AUTO-HANDLE" else "amber"
                st.markdown('<div class="metric"><div class="metric-label">Decision</div><div class="metric-value">{}</div><div class="metric-sub">{}</div></div>'.format(result["decision"], decision_class), unsafe_allow_html=True)

            st.markdown('<div class="section-title">Recommended response</div>', unsafe_allow_html=True)
            st.markdown('<div class="response"><div class="response-label">Grounded AmazonHelp response</div><div class="response-text">{}</div></div>'.format(result["reply"]), unsafe_allow_html=True)
            st.caption(result["reason"])

            with st.expander("Historical evidence", expanded=True):
                for index, evidence in enumerate(result["retrieved_evidence"], 1):
                    st.markdown(
                        '<div class="evidence-card"><div class="evidence-meta">Case {} · similarity {:.1%} · {}</div><div class="evidence-text">{}</div><div class="evidence-response"><strong>Historical response:</strong> {}</div></div>'.format(
                            index, evidence["similarity"], evidence["conversation_id"], evidence["customer_message"], evidence["historical_response"]
                        ),
                        unsafe_allow_html=True,
                    )
        except Exception as error:
            st.error(f"The request could not be analyzed: {error}")
            st.caption("Check that the Knowledge training and processed conversation artifacts are present.")
else:
    st.markdown('<div class="panel"><div class="section-title">Ready for analysis</div><p style="color:#667482;margin:0">Choose an example from the sidebar or enter a customer message above.</p></div>', unsafe_allow_html=True)

st.markdown("<div style='color:#87949d;font-size:.8rem;margin-top:2rem'>AmazonHelp prototype · responses grounded in historical Knowledge conversations</div>", unsafe_allow_html=True)
