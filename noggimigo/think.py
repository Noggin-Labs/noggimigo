"""Deterministic pedagogical planning for Noggimigo.

The Think engine converts verified lesson events into a small, inspectable
teaching plan. It does not generate private chain-of-thought or decide whether
an answer is correct; the answer verifier and curriculum remain authoritative.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SUPPORTED_STATUSES = frozenset({
    "CORRECT",
    "INCORRECT",
    "INVALID",
    "AMBIGUOUS",
    "HINT_REQUESTED",
})

_ACTIONS = {
    "CORRECT": "ACKNOWLEDGE_AND_CONTINUE",
    "INCORRECT": "GIVE_SMALL_HINT",
    "INVALID": "ASK_GUIDING_QUESTION",
    "AMBIGUOUS": "ASK_WHAT_IS_CONFUSING",
    "HINT_REQUESTED": "GIVE_SMALL_HINT",
}


@dataclass(frozen=True)
class TeachingPlan:
    """A concise decision record for the next tutoring move."""

    learner_state: str
    teaching_goal: str
    strategy: str
    pedagogical_action: str
    focus: str
    decision_basis: tuple[str, ...]
    must_avoid: tuple[str, ...]
    requires_verification: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        result = asdict(self)
        result["decision_basis"] = list(self.decision_basis)
        result["must_avoid"] = list(self.must_avoid)
        return result


def build_teaching_plan(
    answer_status: str,
    *,
    question: str,
    deterministic_feedback: str,
    hint: str | None = None,
    preferences: Mapping[str, Any] | None = None,
) -> TeachingPlan:
    """Choose a teaching strategy from authoritative lesson state.

    This function intentionally does not infer ability, emotion, disability,
    attention, or mastery from a learner's wording or response time.
    """
    if answer_status not in SUPPORTED_STATUSES:
        raise ValueError(f"Unsupported answer status: {answer_status!r}")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if not isinstance(deterministic_feedback, str) or not deterministic_feedback.strip():
        raise ValueError("deterministic_feedback must be a non-empty string")

    preferences = preferences or {}
    one_step_at_a_time = preferences.get("one_step_at_a_time", True)
    if not isinstance(one_step_at_a_time, bool):
        raise ValueError("one_step_at_a_time preference must be a boolean")

    if answer_status == "CORRECT":
        return TeachingPlan(
            learner_state="verified_correct",
            teaching_goal="Reinforce the verified step and present the next curriculum prompt.",
            strategy="brief_acknowledgement_then_continue",
            pedagogical_action=_ACTIONS[answer_status],
            focus="Connect the verified response to the next step without making a mastery claim.",
            decision_basis=("The deterministic answer verifier marked the response CORRECT.",),
            must_avoid=("Independent mastery claims", "Unverified claims about lesson completion"),
        )

    if answer_status == "AMBIGUOUS":
        return TeachingPlan(
            learner_state="response_ambiguous",
            teaching_goal="Resolve the ambiguity before teaching or evaluating the response.",
            strategy="clarify_learner_intent",
            pedagogical_action=_ACTIONS[answer_status],
            focus="Ask one concise question about what the learner meant.",
            decision_basis=("The deterministic answer verifier marked the response AMBIGUOUS.",),
            must_avoid=("Treating the response as correct or incorrect", "Guessing the learner's intended answer"),
        )

    if answer_status == "INVALID":
        return TeachingPlan(
            learner_state="response_uninterpretable",
            teaching_goal="Help the learner express an answer in an interpretable form.",
            strategy="request_rephrase",
            pedagogical_action=_ACTIONS[answer_status],
            focus="Ask for a clearer response without implying a mathematical error.",
            decision_basis=("The deterministic answer verifier marked the response INVALID.",),
            must_avoid=("Calling the answer mathematically wrong", "Guessing the intended answer"),
        )

    if answer_status == "HINT_REQUESTED":
        selected_hint = hint.strip() if isinstance(hint, str) and hint.strip() else None
        return TeachingPlan(
            learner_state="requested_support",
            teaching_goal="Offer a scaffold that helps the learner take the next step.",
            strategy="give_curriculum_hint" if selected_hint else "ask_guiding_question",
            pedagogical_action=_ACTIONS[answer_status],
            focus=selected_hint or "Ask what part of the question the learner would like to unpack.",
            decision_basis=("The learner explicitly requested a hint.",),
            must_avoid=("Revealing the expected answer", "Claiming the learner is stuck or incapable"),
        )

    # INCORRECT
    selected_hint = hint.strip() if isinstance(hint, str) and hint.strip() else None
    if one_step_at_a_time and selected_hint:
        strategy = "one_step_scaffold"
        focus = selected_hint
    else:
        strategy = "guided_reconsideration"
        focus = "Invite the learner to check one part of their approach."
    return TeachingPlan(
        learner_state="verified_incorrect",
        teaching_goal="Support another attempt while preserving the learner's opportunity to reason.",
        strategy=strategy,
        pedagogical_action=_ACTIONS[answer_status],
        focus=focus,
        decision_basis=("The deterministic answer verifier marked the response INCORRECT.",),
        must_avoid=("Revealing the expected answer", "Claiming the learner lacks ability or understanding"),
    )
