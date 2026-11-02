"""Domain-specialist routing for Noggimigo.

Specialists analyse learner responses within a specific domain.
They must distinguish verified evidence from uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Literal

from noggimigo.answer_verifier import verify_answer


SpecialistStatus = Literal[
    "ANALYSED",
    "INSUFFICIENT_EVIDENCE",
    "ERROR",
]


@dataclass(frozen=True)
class SpecialistResult:
    """Structured result returned by a domain specialist."""

    domain: str
    status: SpecialistStatus

    claims: tuple[str, ...] = ()
    verified_steps: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    requires_human_review: bool = False


class DomainSpecialist(Protocol):
    """Interface implemented by every domain specialist."""

    domain: str

    def analyse(
        self,
        *,
        prompt: str,
        response: str,
        expected_answer: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> SpecialistResult:
        ...


class DomainRegistry:
    """Registers and routes requests to domain specialists."""

    def __init__(self) -> None:
        self._specialists: dict[str, DomainSpecialist] = {}

    @staticmethod
    def _normalise(domain: str) -> str:
        return domain.strip().lower().replace("_", "-")

    def register(self, specialist: DomainSpecialist) -> None:
        domain = self._normalise(specialist.domain)

        if not domain:
            raise ValueError("Specialist domain cannot be empty.")

        if domain in self._specialists:
            raise ValueError(
                f"A specialist is already registered for '{domain}'."
            )

        self._specialists[domain] = specialist

    def get(self, domain: str) -> DomainSpecialist | None:
        return self._specialists.get(self._normalise(domain))

    def analyse(
        self,
        domain: str,
        *,
        prompt: str,
        response: str,
        expected_answer: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> SpecialistResult:

        normalized_domain = self._normalise(domain)
        specialist = self.get(normalized_domain)

        if specialist is None:
            return SpecialistResult(
                domain=normalized_domain,
                status="INSUFFICIENT_EVIDENCE",
                uncertainties=(
                    "No specialist is registered for this domain.",
                ),
            )

        try:
            return specialist.analyse(
                prompt=prompt,
                response=response,
                expected_answer=expected_answer,
                context=context,
            )

        except Exception:
            # Do not expose exception messages, learner responses,
            # filesystem paths, or other potentially sensitive data.
            return SpecialistResult(
                domain=normalized_domain,
                status="ERROR",
                uncertainties=(
                    "The specialist could not complete its analysis.",
                ),
                requires_human_review=True,
            )


@dataclass
class MathAnswerSpecialist:
    """Checks mathematical answer equivalence.

    This specialist does not diagnose reasoning or misconceptions.
    """

    domain: str = field(default="math", init=False)

    def analyse(
        self,
        *,
        prompt: str,
        response: str,
        expected_answer: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> SpecialistResult:

        if expected_answer is None:
            return SpecialistResult(
                domain=self.domain,
                status="INSUFFICIENT_EVIDENCE",
                uncertainties=(
                    "An expected answer is required for verification.",
                    "The learner's reasoning cannot be inferred from "
                    "the final answer alone.",
                ),
            )

        verification = verify_answer(
            response,
            expected_answer,
        )

        if verification.status in {"INVALID", "AMBIGUOUS"}:
            return SpecialistResult(
                domain=self.domain,
                status="INSUFFICIENT_EVIDENCE",
                uncertainties=(
                    verification.reason
                    or "The answer could not be reliably interpreted.",
                ),
            )

        if verification.correct:
            return SpecialistResult(
                domain=self.domain,
                status="ANALYSED",
                claims=("The submitted answer matches the expected answer.",),
                evidence_refs=("provided_expected_answer",),
            )

        return SpecialistResult(
            domain=self.domain,
            status="ANALYSED",
            claims=(
                "The submitted answer does not match the expected answer.",
            ),
            uncertainties=(
                "The underlying reasoning or misconception is unknown.",
                "The learner's working is needed for diagnostic analysis.",
            ),
            evidence_refs=("provided_expected_answer",),
        )
