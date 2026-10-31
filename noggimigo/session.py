"""Integrated Noggimigo session runtime with authoritative verification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .answer_verifier import verify_answer
from .curriculum import CURRICULUM
from .mastery import MasteryTracker
from .pedagogy import PedagogicalValidationError, validate_suggestion


@dataclass
class TeachingPreferences:
    short_messages: bool = False
    one_step_at_a_time: bool = True
    hint_intensity: int = 1
    show_progress: bool = True


class NoggimigoSession:
    """Authoritative lesson state with optional, untrusted model suggestions."""

    def __init__(self, lesson_id: str = "fractions_intro", *, model=None, preferences=None, history_limit: int = 30):
        self.model = model
        self.preferences = preferences or TeachingPreferences()
        self.history_limit = history_limit
        self.reset(lesson_id)

    def reset(self, lesson_id: str | None = None) -> dict[str, Any]:
        if lesson_id is not None:
            if lesson_id not in CURRICULUM:
                raise ValueError(f"Unsupported lesson: {lesson_id}")
            self.lesson_id = lesson_id
        self.lesson = CURRICULUM[self.lesson_id]
        self.index = 0
        self.history: list[dict[str, Any]] = []
        components = [component for node in self.lesson["nodes"] for component in node.get("knowledge_components", [])]
        self.mastery = MasteryTracker(components)
        return self.current_prompt()

    @property
    def complete(self) -> bool:
        return self.index >= len(self.lesson["nodes"])

    def current_prompt(self) -> dict[str, Any]:
        if self.complete:
            return {"completed": True, "message": "Lesson complete. Nice work!", "mastery": self.mastery.snapshot()}
        node = self.lesson["nodes"][self.index]
        result = {"completed": False, "lesson_id": self.lesson_id, "title": self.lesson["title"], "question": node["question"], "progress": f"{self.index + 1}/{len(self.lesson['nodes'])}", "mastery": self.mastery.snapshot()}
        if self.preferences.short_messages:
            result["question"] = result["question"].replace("What fraction is unshaded?", "What fraction is left?")
        return result

    def mastery_snapshot(self) -> dict[str, Any]:
        return {"bkt": self.mastery.snapshot(), "mirt_ability": self.mastery.mirt_snapshot()}

    def _record(self, event: dict[str, Any]) -> None:
        self.history.append(event)
        del self.history[:-self.history_limit]

    def request_hint(self) -> dict[str, Any]:
        if self.complete:
            return {"status": "COMPLETE", "feedback": "This lesson is already complete."}
        node = self.lesson["nodes"][self.index]
        result = {"status": "HINT_REQUESTED", "feedback": node["hint"], "advanced": False, "progress": self.current_prompt()["progress"]}
        self._record({"type": "hint", **result})
        return result

    def submit(self, answer: str) -> dict[str, Any]:
        if self.complete:
            return {"status": "COMPLETE", "feedback": "This lesson is already complete.", "advanced": False}
        node = self.lesson["nodes"][self.index]
        check = verify_answer(answer, node["answer"])
        is_correct = check.status == "CORRECT"
        mastery_event = self.mastery.observe(node["knowledge_components"], correct=is_correct)
        if is_correct:
            self.index += 1
            result = {"status": "CORRECT", "feedback": "Correct. Now let’s take the next step." if not self.complete else "Correct. You completed the lesson!", "advanced": True, "completed": self.complete, "next_prompt": self.current_prompt()}
        else:
            feedback = node["misconceptions"].get(" ".join(answer.strip().lower().split()), "Not quite. Try one small step and check the quantities again.")
            if check.status == "AMBIGUOUS":
                feedback = check.reason
            result = {"status": check.status, "feedback": feedback, "advanced": False, "completed": False, "next_prompt": self.current_prompt()}
        result["mastery"] = self.mastery_snapshot()
        self._record({"type": "answer", "answer": answer, "knowledge_components": node["knowledge_components"], "correct": is_correct, "mastery_event": mastery_event, **result})

        if self.model is not None:
            try:
                suggestion = self.model.generate(
                    node["question"],
                    answer,
                    subject=self.lesson["subject"],
                    lesson_context={"title": self.lesson["title"], "objective": self.lesson["objective"]},
                    deterministic_feedback=result["feedback"],
                )
            except Exception:
                # Provider failures are expected to be recoverable; deterministic
                # verification and progression have already completed.
                result["model_fallback"] = True
            else:
                try:
                    validated = validate_suggestion(
                        suggestion,
                        answer_status=check.status,
                        expected_answer=node["answer"],
                        progression_verified=is_correct,
                        lesson_complete_verified=self.complete,
                    )
                except PedagogicalValidationError:
                    result["model_fallback"] = True
                else:
                    result["model_message"] = validated["student_facing_message"]
                    result["pedagogical_action"] = validated["pedagogical_action"]
        return result
