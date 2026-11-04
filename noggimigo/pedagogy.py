"""Validation for model-proposed tutoring messages.

This module checks structure and consistency with deterministic application state.
It cannot prove that a natural-language explanation is mathematically or factually correct.
"""
from __future__ import annotations

import re
import unicodedata
from fractions import Fraction
from decimal import Decimal, InvalidOperation
from typing import Any


class PedagogicalValidationError(ValueError):
    """Raised when a model suggestion violates the tutoring output contract."""


ALLOWED_ACTIONS = frozenset({
    "ASK_GUIDING_QUESTION",
    "GIVE_SMALL_HINT",
    "ACKNOWLEDGE_AND_CONTINUE",
    "ASK_WHAT_IS_CONFUSING",
    "EXPLAIN_ONE_STEP",
})

_ACTIONS_BY_STATUS = {
    "CORRECT": frozenset({
        "ACKNOWLEDGE_AND_CONTINUE", "ASK_GUIDING_QUESTION", "EXPLAIN_ONE_STEP"
    }),
    "INCORRECT": frozenset({
        "ASK_GUIDING_QUESTION", "GIVE_SMALL_HINT", "ASK_WHAT_IS_CONFUSING", "EXPLAIN_ONE_STEP"
    }),
    "INVALID": frozenset({
        "ASK_GUIDING_QUESTION", "GIVE_SMALL_HINT", "ASK_WHAT_IS_CONFUSING", "EXPLAIN_ONE_STEP"
    }),
    "AMBIGUOUS": frozenset({
        "ASK_GUIDING_QUESTION", "GIVE_SMALL_HINT", "ASK_WHAT_IS_CONFUSING", "EXPLAIN_ONE_STEP"
    }),
}

_REQUIRED_KEYS = {
    "student_facing_message",
    "pedagogical_action",
    "misconception_candidates",
    "requires_verification",
}

# Claim detectors.
#
# These are lexical pattern detectors, not natural-language understanding. They are
# deliberately broad because the costs are asymmetric: a false positive only falls
# back to the deterministic feedback the application already produced, while a false
# negative lets the model contradict authoritative state. Adversarial review found
# that the original patterns missed common phrasings ("That's right!", "You've
# mastered this!", "Let's move on."), so the alternatives below widen coverage while
# preserving boundaries so that math-context tokens such as "right-hand side" and
# "perfect square" are not treated as correctness claims.
_CORRECT_CLAIMS = re.compile(
    r"\b(?:"
    r"correct"
    r"|right answer|right\b(?![-\s]?hand)"
    r"|(?:you are|you[’']re) right"
    r"|(?:that[’']?s|that is|this is|it[’']?s|it is) right"
    r"|(?:you have |you[’']ve )?got it"
    r"|exactly|well done|spot on|bingo|nailed it"
    r")\b",
    re.IGNORECASE,
)
_INCORRECT_CLAIMS = re.compile(
    r"\b(?:incorrect|wrong answer|(?:you are|you[’']re) wrong|not quite|not right)\b",
    re.IGNORECASE,
)
_COMPLETION_CLAIMS = re.compile(
    r"\b(?:"
    r"lesson complete|lesson is (?:complete|finished|over)"
    r"|(?:you have|you[’']ve) (?:completed|finished)"
    r"|(?:you are|you[’']re) (?:done|finished)"
    r"|(?:all done|that was the last)"
    r")\b",
    re.IGNORECASE,
)
_MASTERY_CLAIMS = re.compile(
    r"\b(?:"
    r"(?:you have |you[’']ve )?mastered"
    r"|mastery (?:achieved|attained)"
    r")\b",
    re.IGNORECASE,
)
_PROGRESSION_CLAIMS = re.compile(
    r"\b(?:"
    r"next lesson|next question"
    r"|moving on|move on to"
    r"|(?:you have |you[’']ve )?advanced (?:to|past)"
    r")\b",
    re.IGNORECASE,
)

# Spoken forms of common fractions. Needed because an answer leak check that only
# knows "1/4" and "0.25" does not catch "one quarter".
_FRACTION_WORDS: dict[tuple[int, int], tuple[str, ...]] = {
    (1, 2): ("one half", "a half"),
    (1, 3): ("one third", "a third"),
    (1, 4): ("one quarter", "a quarter", "one fourth", "a fourth"),
    (1, 5): ("one fifth", "a fifth"),
    (3, 4): ("three quarters", "three fourths"),
    (2, 3): ("two thirds",),
    (1, 8): ("one eighth", "an eighth"),
}

_DIGIT_TO_WORD = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def _has_control_characters(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in value)


def _normalise_text(value: str) -> str:
    value = value.casefold().replace("−", "-")
    value = re.sub(r"\s*/\s*", "/", value)
    value = re.sub(r"\s*=\s*", "=", value)
    return " ".join(value.split())


def _numeric_forms(value: str) -> set[str]:
    """Return exact equivalent fraction/decimal forms where safely parseable."""
    forms = {_normalise_text(value)}
    compact = forms.copy()
    for candidate in compact:
        try:
            if "/" in candidate:
                numerator, denominator = candidate.split("/", 1)
                rational = Fraction(int(numerator), int(denominator))
            else:
                rational = Fraction(Decimal(candidate))
        except (ValueError, ZeroDivisionError, InvalidOperation):
            continue
        forms.add(f"{rational.numerator}/{rational.denominator}")
        forms.update(_FRACTION_WORDS.get((rational.numerator, rational.denominator), ()))
        denominator = rational.denominator
        while denominator % 2 == 0:
            denominator //= 2
        while denominator % 5 == 0:
            denominator //= 5
        if denominator == 1:
            decimal = Decimal(rational.numerator) / Decimal(rational.denominator)
            forms.add(format(decimal.normalize(), "f"))
    return {form for form in forms if form}


def _leaks_expected_answer(message: str, expected_answer: str | None) -> bool:
    """Conservatively detect direct answer disclosure without fuzzy substring matching."""
    if not isinstance(expected_answer, str) or not expected_answer.strip():
        return False
    normalized_message = _normalise_text(message)
    normalized_expected = _normalise_text(expected_answer)

    # Text answers are checked as whole phrases, not arbitrary substrings.
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\s*/\s*[+-]?\d+)?", expected_answer.strip()):
        phrase = re.escape(normalized_expected)
        if re.search(rf"(?<!\w){phrase}(?!\w)", normalized_message):
            return True
        # Also check a spoken-number variant, e.g. "subtract 4" -> "subtract four".
        spoken = normalized_expected
        for digit, word in _DIGIT_TO_WORD.items():
            spoken = re.sub(rf"(?<!\w){digit}(?!\w)", word, spoken)
        if spoken != normalized_expected:
            return bool(re.search(rf"(?<!\w){re.escape(spoken)}(?!\w)", normalized_message))
        return False

    forms = _numeric_forms(expected_answer.strip())
    for form in forms:
        # A one-character numeric answer is too ambiguous to scan as a free token;
        # only reject it when the message explicitly presents it as an answer/equation.
        if len(form) == 1 and form.isdigit():
            if normalized_message.strip() == form:
                return True
            explicit = re.compile(
                rf"(?:\b(?:answer|result)\s*(?:is|=|:)\s*|\b[xX]\s*=\s*|\bit\s+(?:is|equals)\s+){re.escape(form)}(?!\d)",
                re.IGNORECASE,
            )
            if explicit.search(message):
                return True
            continue
        token = re.compile(rf"(?<![\w.]){re.escape(form)}(?!\w)", re.IGNORECASE)
        if token.search(normalized_message):
            return True
    return False


def validate_suggestion(
    suggestion: Any,
    *,
    answer_status: str,
    expected_answer: str | None = None,
    progression_verified: bool = False,
    lesson_complete_verified: bool = False,
) -> dict[str, Any]:
    """Validate a model suggestion against authoritative deterministic state.

    Passing validation is not evidence that the message is semantically correct.
    The answer verifier and curriculum remain authoritative.
    """
    if not isinstance(suggestion, dict) or set(suggestion) != _REQUIRED_KEYS:
        raise PedagogicalValidationError("Suggestion must contain exactly the required fields.")

    message = suggestion["student_facing_message"]
    action = suggestion["pedagogical_action"]
    candidates = suggestion["misconception_candidates"]

    if not isinstance(message, str) or not message.strip():
        raise PedagogicalValidationError("student_facing_message must be a non-empty string.")
    if len(message) > 400:
        raise PedagogicalValidationError("student_facing_message exceeds 400 characters.")
    if _has_control_characters(message):
        raise PedagogicalValidationError("student_facing_message contains control characters.")
    if message.count("?") > 1:
        raise PedagogicalValidationError("Use at most one question per message.")

    if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
        raise PedagogicalValidationError("Unsupported pedagogical_action.")
    if not isinstance(answer_status, str) or answer_status not in _ACTIONS_BY_STATUS:
        raise PedagogicalValidationError("Unknown deterministic answer status.")
    if action not in _ACTIONS_BY_STATUS[answer_status]:
        raise PedagogicalValidationError("Action is incompatible with deterministic answer status.")

    if suggestion["requires_verification"] is not True:
        raise PedagogicalValidationError("requires_verification must be exactly True.")

    if not isinstance(candidates, list) or len(candidates) > 3:
        raise PedagogicalValidationError("misconception_candidates must contain at most three items.")
    if any(
        not isinstance(candidate, str)
        or not candidate.strip()
        or len(candidate) > 160
        or _has_control_characters(candidate)
        for candidate in candidates
    ):
        raise PedagogicalValidationError("Each misconception candidate must be a valid non-empty string.")

    if _CORRECT_CLAIMS.search(message) and answer_status != "CORRECT":
        raise PedagogicalValidationError("The model cannot claim an unverified answer is correct.")
    if _INCORRECT_CLAIMS.search(message) and answer_status == "CORRECT":
        raise PedagogicalValidationError("The model cannot contradict a verified correct answer.")
    if _MASTERY_CLAIMS.search(message):
        raise PedagogicalValidationError("The model cannot independently claim learner mastery.")
    if _COMPLETION_CLAIMS.search(message) and not lesson_complete_verified:
        raise PedagogicalValidationError("Lesson completion has not been verified.")
    if _PROGRESSION_CLAIMS.search(message) and not progression_verified:
        raise PedagogicalValidationError("Curriculum progression has not been verified.")
    if _leaks_expected_answer(message, expected_answer):
        raise PedagogicalValidationError("The suggestion reveals the expected answer.")

    # Return a copy so callers cannot accidentally mutate the provider's object.
    return dict(suggestion)
