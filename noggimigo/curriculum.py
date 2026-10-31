"""Supported, explicit curriculum for the deterministic tutor."""
from __future__ import annotations

CURRICULUM = {
    "fractions_intro": {
        "subject": "mathematics", "topic": "fractions", "title": "Introduction to Fractions",
        "objective": "Identify the unshaded portion and express equivalent fractions.",
        "nodes": [
            {"id": "step_1", "question": "A circle is split into 4 equal parts. 3 are shaded. What fraction is unshaded?", "answer": "1/4", "hint": "Subtract shaded parts from total parts: 4 - 3.", "misconceptions": {"3/4": "3/4 is the shaded portion. We need the part left unshaded."}, "next": "step_2"},
            {"id": "step_2", "question": "If the 1/4 slice is cut in half, what fraction of the whole circle is one new piece?", "answer": "1/8", "hint": "Cutting every fourth into 2 pieces makes 4 × 2 equal pieces.", "misconceptions": {"1/4": "The slice became smaller, so the denominator must increase."}, "next": None},
        ],
    },
    "algebra_intro": {
        "subject": "mathematics", "topic": "algebra", "title": "Basic Algebraic Thinking",
        "objective": "Use inverse operations to isolate a variable.",
        "nodes": [
            {"id": "step_1", "question": "Solve 2x + 4 = 10. What operation first isolates 2x?", "answer": "subtract 4", "hint": "Undo +4 with its inverse operation.", "misconceptions": {"add 4": "Adding 4 moves away from isolating 2x. Try the inverse."}, "next": "step_2"},
            {"id": "step_2", "question": "After subtracting 4, 2x = 6. What is x?", "answer": "3", "hint": "Divide both sides by 2.", "misconceptions": {}, "next": None},
        ],
    },
    "patterns_sequences": {
        "subject": "mathematics", "topic": "sequences", "title": "Pattern Recognition",
        "objective": "Identify a constant step in a numerical sequence.",
        "nodes": [{"id": "step_1", "question": "What number comes next: 2, 5, 8, 11, __?", "answer": "14", "hint": "Find what is added each time.", "misconceptions": {}, "next": None}],
    },
}

def lesson_ids() -> list[str]:
    return list(CURRICULUM)
