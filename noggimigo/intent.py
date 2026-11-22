"""Deterministic, conservative recognition of learner interaction intent.

Intent recognition routes a message; it never verifies or grades an answer.
The answer verifier remains the sole authority for mathematical correctness.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum


class Intent(StrEnum):
    """Supported interaction intents."""

    ANSWER_SUBMISSION = "ANSWER_SUBMISSION"
    QUESTION = "QUESTION"
    HINT_REQUEST = "HINT_REQUEST"
    CONFUSION = "CONFUSION"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class IntentResult:
    """Inspectable classification output, not a claim about learner state."""

    intent: Intent
    confidence: float
    evidence: tuple[str, ...]
    normalized_text: str

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["intent"] = self.intent.value
        result["evidence"] = list(self.evidence)
        return result


_RULES: tuple[tuple[Intent, tuple[re.Pattern[str], ...], float, str], ...] = (
    (
        Intent.HINT_REQUEST,
        (
            re.compile(r"\b(?:give|show|provide|offer)\s+(?:me\s+)?(?:a\s+)?hint\b"),
            re.compile(r"\b(?:can|could|may)\s+i\s+(?:have|get)\s+(?:a\s+)?hint\b"),
            re.compile(r"\bneed\s+(?:a\s+)?hint\b"),
            re.compile(r"^hint$"),
            re.compile(r"\bhelp\s+me\s+(?:with|on)\b"),
        ),
        0.98,
        "explicit_hint_request",
    ),
    (
        Intent.EXPLANATION_REQUEST,
        (
            re.compile(r"\b(?:explain|teach|walk\s+me\s+through)\b"),
            re.compile(r"\bhow\s+does\s+(?:this|that|it)\s+work\b"),
            re.compile(r"\b(?:explain|show)\s+(?:it|this|that)\s+another\s+way\b"),
        ),
        0.96,
        "explicit_explanation_request",
    ),
    (
        Intent.CONFUSION,
        (
            re.compile(r"\b(?:i\s+)?(?:do\s+not|don't|dont)\s+understand\b"),
            re.compile(r"\b(?:i'm|i\s+am)\s+(?:confused|lost|stuck)\b"),
            re.compile(r"\bthis\s+(?:makes\s+)?no\s+sense\b"),
            re.compile(r"\bi\s+don't\s+know\s+what\s+to\s+do\b"),
        ),
        0.95,
        "explicit_confusion_statement",
    ),
    (
        Intent.QUESTION,
        (
            re.compile(r"\bwhy\b"),
            re.compile(r"\bwhat\s+does\b"),
            re.compile(r"\bhow\s+(?:do|does|did|can|should|would)\b"),
            re.compile(r"\bwhen\s+(?:do|does|should|would)\b"),
            re.compile(r"\bwhere\s+(?:do|does|should)\b"),
            re.compile(r"\bis\s+(?:this|that|it)\b"),
            re.compile(r"\bcan\s+you\s+tell\s+me\b"),
        ),
        0.88,
        "question_language",
    ),
)


class IntentRecognizer:
    """Small rule-based router with an explicit uncertain fallback."""

    def classify(self, text: str) -> IntentResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        normalized = " ".join(text.casefold().strip().split())
        if not normalized:
            return IntentResult(Intent.UNCERTAIN, 0.0, ("empty_input",), normalized)

        for intent, patterns, confidence, evidence in _RULES:
            if any(pattern.search(normalized) for pattern in patterns):
                return IntentResult(intent, confidence, (evidence,), normalized)

        # Routing only: the authoritative verifier still decides correctness.
        if re.search(r"[\w\d]", normalized, flags=re.UNICODE):
            return IntentResult(
                Intent.ANSWER_SUBMISSION,
                0.60,
                ("default_to_authoritative_answer_verifier",),
                normalized,
            )

        return IntentResult(Intent.UNCERTAIN, 0.0, ("no_classifiable_content",), normalized)


class NoggimigoIntentAI:
    """Compatibility facade for older callers of predict_intent."""

    def __init__(self) -> None:
        self.recognizer = IntentRecognizer()

    def predict_intent(self, user_sentence: str, min_confidence: float = 0.2) -> dict[str, object]:
        if (
            isinstance(min_confidence, bool)
            or not isinstance(min_confidence, (int, float))
            or not 0.0 <= min_confidence <= 1.0
        ):
            raise ValueError("min_confidence must be between 0 and 1")
        result = self.recognizer.classify(user_sentence)
        intent_value = result.intent.value
        if result.intent is Intent.HINT_REQUEST:
            intent_value = "hint"
        if result.confidence < min_confidence:
            intent_value = Intent.UNCERTAIN.value
        return {
            "intent": intent_value,
            "confidence": result.confidence,
            "match_type": result.evidence[0],
            "evidence": list(result.evidence),
            "normalized_text": result.normalized_text,
        }
