"""Small dependency-free metrics for evaluating mastery predictions."""
from __future__ import annotations

from collections.abc import Iterable


def _pairs(predictions: Iterable[float], outcomes: Iterable[bool]) -> list[tuple[float, float]]:
    pairs = [(float(prediction), float(outcome)) for prediction, outcome in zip(predictions, outcomes, strict=True)]
    if not pairs:
        raise ValueError("at least one prediction is required")
    if any(not 0.0 <= prediction <= 1.0 for prediction, _ in pairs):
        raise ValueError("predictions must be between 0 and 1")
    return pairs


def brier_score(predictions: Iterable[float], outcomes: Iterable[bool]) -> float:
    """Mean squared probability error; lower is better."""
    pairs = _pairs(predictions, outcomes)
    return sum((prediction - outcome) ** 2 for prediction, outcome in pairs) / len(pairs)


def expected_calibration_error(predictions: Iterable[float], outcomes: Iterable[bool], *, bins: int = 10) -> float:
    """Weighted absolute gap between predicted and observed success by probability bin."""
    if bins < 2:
        raise ValueError("bins must be at least 2")
    pairs = _pairs(predictions, outcomes)
    buckets: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for prediction, outcome in pairs:
        index = min(bins - 1, int(prediction * bins))
        buckets[index].append((prediction, outcome))
    total = len(pairs)
    return sum(
        len(bucket) / total * abs(sum(p for p, _ in bucket) / len(bucket) - sum(o for _, o in bucket) / len(bucket))
        for bucket in buckets
        if bucket
    )


def monotonicity_violation_rate(values: Iterable[float]) -> float:
    """Fraction of adjacent estimates that decrease, for a no-forgetting trace."""
    sequence = [float(value) for value in values]
    if len(sequence) < 2:
        return 0.0
    violations = sum(current < previous for previous, current in zip(sequence, sequence[1:]))
    return violations / (len(sequence) - 1)
