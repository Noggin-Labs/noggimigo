"""Noggimigo: a deterministic local tutoring runtime."""
from .answer_verifier import VerificationResult, parse_math_answer, verify_answer
from .curriculum import CURRICULUM, lesson_ids
from .evaluation import brier_score, expected_calibration_error, monotonicity_violation_rate
from .mastery import BKTParameters, BKTState, MIRTItem, MIRTState, MasteryTracker
from .session import NoggimigoSession, TeachingPreferences

__all__ = [
    "BKTParameters", "BKTState", "CURRICULUM", "MIRTItem", "MIRTState",
    "MasteryTracker", "NoggimigoSession", "TeachingPreferences", "VerificationResult",
    "brier_score", "expected_calibration_error", "monotonicity_violation_rate",
    "lesson_ids", "parse_math_answer", "verify_answer",
]
