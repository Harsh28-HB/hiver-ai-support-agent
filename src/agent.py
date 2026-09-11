"""Local AmazonHelp support agent using Knowledge-only classification and retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .baselines import FINAL_INTENTS, TfidfLogisticBaseline, knowledge_label_path


@dataclass
class RetrievedEvidence:
    conversation_id: str
    similarity: float
    customer_message: str
    historical_response: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "similarity": round(self.similarity, 4),
            "customer_message": self.customer_message,
            "historical_response": self.historical_response,
        }


class AmazonHelpAgent:
    """A reproducible local agent. It never reads golden data."""

    def __init__(self, root: Path):
        self.root = root
        self.classifier = TfidfLogisticBaseline()
        self.retrieval_vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=2,
            max_features=100_000,
        )
        self._fit_classifier()
        self._fit_retrieval()

    def _fit_classifier(self) -> None:
        labels_path = knowledge_label_path(self.root)
        if not labels_path.exists():
            raise FileNotFoundError(f"Knowledge labels not found: {labels_path}")
        labels = pd.read_csv(labels_path, dtype=str).fillna("")
        labels = labels[labels["human_intent"].isin(FINAL_INTENTS)]
        self.classifier.fit(labels["customer_message"].tolist(), labels["human_intent"].tolist())

    def _fit_retrieval(self) -> None:
        conversations_path = self.root / "data" / "processed" / "conversations.csv"
        frame = pd.read_csv(conversations_path, usecols=["conversation_id", "messages", "split"], dtype=str)
        frame = frame[frame["split"].eq("knowledge")].copy()
        documents: list[str] = []
        records: list[dict[str, str]] = []
        for _, row in frame.iterrows():
            messages = json.loads(row["messages"])
            customers = [item["text"].strip() for item in messages if item.get("speaker") == "customer" and item.get("text", "").strip()]
            responses = [item["text"].strip() for item in messages if item.get("speaker") == "brand" and item.get("text", "").strip()]
            if not customers or not responses:
                continue
            documents.append(" ".join(customers))
            records.append({
                "conversation_id": str(row["conversation_id"]),
                "customer_message": customers[-1],
                "historical_response": responses[-1],
            })
        if not records:
            raise ValueError("No usable Knowledge conversations available for retrieval")
        self.retrieval_matrix = self.retrieval_vectorizer.fit_transform(documents)
        self.retrieval_records = records

    def _predict_intent(self, message: str) -> tuple[str, float]:
        if self.classifier.classifier is None or self.classifier.vectorizer is None:
            raise RuntimeError("Intent classifier is not fitted")
        matrix = self.classifier.vectorizer.transform([message])
        probabilities = self.classifier.classifier.predict_proba(matrix)[0]
        index = int(probabilities.argmax())
        return str(self.classifier.classifier.classes_[index]), float(probabilities[index])

    def _retrieve(self, message: str, limit: int = 3) -> list[RetrievedEvidence]:
        query = self.retrieval_vectorizer.transform([message])
        similarities = cosine_similarity(query, self.retrieval_matrix).ravel()
        indices = similarities.argsort()[::-1][:limit]
        return [
            RetrievedEvidence(
                conversation_id=self.retrieval_records[index]["conversation_id"],
                similarity=float(similarities[index]),
                customer_message=self.retrieval_records[index]["customer_message"],
                historical_response=self.retrieval_records[index]["historical_response"],
            )
            for index in indices
        ]

    @staticmethod
    def _clean_response(response: str) -> str:
        response = re.sub(r"https?://\S+", "", response).strip()
        response = re.sub(r"^@\w+\s*", "", response).strip()
        return response

    def respond(self, message: str) -> dict[str, Any]:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be empty")
        intent, confidence = self._predict_intent(message)
        evidence = self._retrieve(message)
        best_similarity = evidence[0].similarity if evidence else 0.0
        enough_evidence = best_similarity >= 0.20 and len(evidence) > 0
        high_confidence = confidence >= 0.60
        decision = "AUTO-HANDLE" if high_confidence and enough_evidence and intent != "other_or_unclear" else "ESCALATE"
        if decision == "AUTO-HANDLE":
            reason = f"Intent confidence {confidence:.2f} and best Knowledge similarity {best_similarity:.2f} meet the auto-handle thresholds."
            reply = self._clean_response(evidence[0].historical_response)
        else:
            reasons = []
            if intent == "other_or_unclear":
                reasons.append("intent is other_or_unclear")
            if not high_confidence:
                reasons.append(f"intent confidence {confidence:.2f} is below 0.60")
            if not enough_evidence:
                reasons.append(f"best Knowledge similarity {best_similarity:.2f} is below 0.20")
            reason = "Escalated because " + "; ".join(reasons) + "."
            reply = "I’m sorry, but I need a support specialist to review this request."
        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "retrieved_evidence": [item.as_dict() for item in evidence],
            "reply": reply,
            "decision": decision,
            "reason": reason,
        }
