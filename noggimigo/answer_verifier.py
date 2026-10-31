"""Safe, deterministic answer parsing and equivalence checking."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from fractions import Fraction

@dataclass(frozen=True)
class VerificationResult:
    correct: bool
    status: str
    normalized: str | None = None
    reason: str = ""

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_FRACTION = re.compile(r"^([+-]?\d+)\s*/\s*([+-]?\d+)$")


def parse_math_answer(text: str) -> Fraction | str | None:
    """Parse a deliberately narrow mathematical answer; reject malformed input."""
    value = " ".join(text.strip().lower().split())
    value = value.replace("−", "-")
    if not value:
        return None
    fraction = _FRACTION.fullmatch(value)
    if fraction:
        numerator, denominator = map(int, fraction.groups())
        if denominator == 0:
            return None
        return Fraction(numerator, denominator)
    if _NUMBER.fullmatch(value):
        try:
            return Fraction(Decimal(value))
        except InvalidOperation:
            return None
    return value


def verify_answer(student: str, expected: str, *, expected_numeric: float | None = None) -> VerificationResult:
    """Verify exact text or mathematical equivalence without fuzzy acceptance."""
    student_value = parse_math_answer(student)
    expected_value = parse_math_answer(expected)
    if student_value is None:
        return VerificationResult(False, "INVALID", reason="Enter an answer such as 1/4 or 0.25.")
    if isinstance(expected_value, Fraction) and isinstance(student_value, Fraction):
        correct = student_value == expected_value
        return VerificationResult(correct, "CORRECT" if correct else "INCORRECT", str(student_value), "")
    if isinstance(expected_value, str) and isinstance(student_value, str):
        normalized_student = student_value.casefold()
        normalized_expected = expected_value.casefold()
        correct = normalized_student == normalized_expected
        return VerificationResult(correct, "CORRECT" if correct else "INCORRECT", normalized_student, "")
    return VerificationResult(False, "AMBIGUOUS", reason="Please give the requested form of the answer.")
