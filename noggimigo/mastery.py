"""Small, interpretable online mastery estimators for Noggimigo.

These estimators model answer outcomes only. They do not infer attention,
fatigue, emotion, disability, intelligence, or biological state.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


def _sigmoid(value: float) -> float:
    value = max(-35.0, min(35.0, value))
    return 1.0 / (1.0 + math.exp(-value))


@dataclass(frozen=True)
class BKTParameters:
    p_init: float = 0.20
    p_learn: float = 0.15
    p_guess: float = 0.20
    p_slip: float = 0.10
    p_forget: float = 0.0

    def __post_init__(self) -> None:
        for name in ("p_init", "p_learn", "p_guess", "p_slip", "p_forget"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


class BKTState:
    """Online Bayesian Knowledge Tracing state for one knowledge component."""

    def __init__(self, parameters: BKTParameters | None = None) -> None:
        self.parameters = parameters or BKTParameters()
        self.p_mastery = self.parameters.p_init
        self.observations = 0

    def predict(self) -> float:
        p = self.parameters
        return self.p_mastery * (1.0 - p.p_slip) + (1.0 - self.p_mastery) * p.p_guess

    def update(self, correct: bool, *, elapsed_days: float = 0.0) -> float:
        if elapsed_days < 0:
            raise ValueError("elapsed_days cannot be negative")
        p = self.parameters
        if p.p_forget and elapsed_days:
            self.p_mastery *= math.exp(-p.p_forget * elapsed_days)
        predicted = self.predict()
        if correct:
            likelihood_mastered = 1.0 - p.p_slip
            likelihood_unmastered = p.p_guess
        else:
            likelihood_mastered = p.p_slip
            likelihood_unmastered = 1.0 - p.p_guess
        denominator = self.p_mastery * likelihood_mastered + (1.0 - self.p_mastery) * likelihood_unmastered
        posterior = self.p_mastery if denominator == 0 else self.p_mastery * likelihood_mastered / denominator
        self.p_mastery = posterior + (1.0 - posterior) * p.p_learn
        self.observations += 1
        return predicted


@dataclass(frozen=True)
class MIRTItem:
    """Difficulty and discrimination for one item over named KCs."""

    difficulty: dict[str, float]
    discrimination: dict[str, float]


class MIRTState:
    """Lightweight online multidimensional IRT state.

    This is an auditable baseline, not a production psychometric calibration.
    Parameters should be fit and evaluated against held-out responses before use.
    """

    def __init__(self, knowledge_components: Iterable[str], *, learning_rate: float = 0.08) -> None:
        self.ability = {component: 0.0 for component in knowledge_components}
        self.learning_rate = learning_rate
        self.observations = 0

    def predict(self, item: MIRTItem) -> float:
        score = sum(
            item.discrimination.get(component, 0.0)
            * (self.ability.get(component, 0.0) - item.difficulty.get(component, 0.0))
            for component in self.ability
        )
        return _sigmoid(score)

    def update(self, item: MIRTItem, correct: bool) -> float:
        predicted = self.predict(item)
        error = float(correct) - predicted
        for component in self.ability:
            discrimination = item.discrimination.get(component, 0.0)
            self.ability[component] += self.learning_rate * error * discrimination
        self.observations += 1
        return predicted


class MasteryTracker:
    """Track per-KC BKT mastery plus a MIRT-style next-response prediction."""

    def __init__(self, knowledge_components: Iterable[str]) -> None:
        components = tuple(dict.fromkeys(knowledge_components))
        if not components:
            raise ValueError("at least one knowledge component is required")
        self.knowledge_components = components
        self.bkt = {component: BKTState() for component in components}
        self.mirt = MIRTState(components)

    def observe(
        self,
        knowledge_components: Iterable[str],
        *,
        correct: bool,
        item_difficulty: float = 0.0,
        elapsed_days: float = 0.0,
    ) -> dict[str, object]:
        components = tuple(dict.fromkeys(knowledge_components))
        unknown = set(components) - set(self.knowledge_components)
        if unknown:
            raise ValueError(f"unknown knowledge components: {sorted(unknown)}")
        if not components:
            raise ValueError("an observation must include a knowledge component")
        predictions = {component: self.bkt[component].update(correct, elapsed_days=elapsed_days) for component in components}
        item = MIRTItem(
            difficulty={component: item_difficulty for component in components},
            discrimination={component: 1.0 for component in components},
        )
        mirt_prediction = self.mirt.update(item, correct)
        return {
            "correct": correct,
            "knowledge_components": list(components),
            "bkt_predictions": predictions,
            "bkt_mastery": self.snapshot(),
            "mirt_prediction": round(mirt_prediction, 6),
        }

    def snapshot(self) -> dict[str, float]:
        return {component: round(state.p_mastery, 6) for component, state in self.bkt.items()}

    def mirt_snapshot(self) -> dict[str, float]:
        return {component: round(value, 6) for component, value in self.mirt.ability.items()}
