"""Structured reasoning-evidence records for Noggimigo.

Design goal: make the difference between *what the learner actually supplied* and
*what the application concludes* mechanically visible, rather than mixing them in
free text.

Four provenance grades, and nothing else:

``OBSERVED``   present in the learner's submission (a quotation, a stated answer).
``VERIFIED``   checked by a deterministic routine against an explicit reference.
``INFERRED``   a conclusion derived from named evidence items; never a fact.
``UNKNOWN``    not determinable from the available submission.

Hard rules enforced here:

1. An ``INFERRED`` item must cite at least one existing evidence item. Inference
   from nothing is rejected.
2. A quotation is ``OBSERVED``. Quoting a learner's step does not make it
   ``VERIFIED``: ``mark_verified`` requires an explicit deterministic check, and a
   failing check keeps the grade at ``OBSERVED`` while recording a contradiction.
3. Confidence is required for inferences and must lie in [0, 1].
4. The schema has no field for a learner trait. It cannot represent "this learner
   is inattentive" because that is not a property of a mathematical response.

This module deliberately does not diagnose misconceptions. It records evidence and
explicitly-labelled inferences so that a human or a downstream rule can decide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Provenance = Literal["OBSERVED", "VERIFIED", "INFERRED", "UNKNOWN"]

PROVENANCE_GRADES: frozenset[str] = frozenset({"OBSERVED", "VERIFIED", "INFERRED", "UNKNOWN"})
EVIDENCE_KINDS: frozenset[str] = frozenset(
    {"student_statement", "observed_work", "assumption", "given"}
)


class ReasoningEvidenceError(ValueError):
    """Raised when an evidence record would violate its own invariants."""


@dataclass(frozen=True)
class EvidenceItem:
    """A single item of supplied evidence or a stated assumption."""

    evidence_id: str
    kind: str
    text: str
    provenance: Provenance
    source_ref: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ReasoningEvidenceError("evidence_id cannot be empty")
        if self.kind not in EVIDENCE_KINDS:
            raise ReasoningEvidenceError(f"unknown evidence kind: {self.kind!r}")
        if self.provenance not in PROVENANCE_GRADES:
            raise ReasoningEvidenceError(f"unknown provenance: {self.provenance!r}")
        if self.provenance == "INFERRED":
            raise ReasoningEvidenceError(
                "evidence items are observed or verified, not inferred; "
                "use add_inference() for conclusions"
            )
        if not self.text.strip():
            raise ReasoningEvidenceError("evidence text cannot be empty")


@dataclass(frozen=True)
class Inference:
    """A conclusion that cites the evidence it rests on."""

    inference_id: str
    statement: str
    supporting: tuple[str, ...]
    contradicting: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not self.inference_id.strip():
            raise ReasoningEvidenceError("inference_id cannot be empty")
        if not self.statement.strip():
            raise ReasoningEvidenceError("inference statement cannot be empty")
        if not self.supporting:
            raise ReasoningEvidenceError(
                "an inference must cite at least one supporting evidence item"
            )
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ReasoningEvidenceError("confidence must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "inference_id": self.inference_id,
            "statement": self.statement,
            "supporting": list(self.supporting),
            "contradicting": list(self.contradicting),
            "confidence": float(self.confidence),
            "provenance": "INFERRED",
        }


@dataclass
class ReasoningRecord:
    """An auditable record of evidence and inferences for one learner response."""

    question_id: str
    _evidence: dict[str, EvidenceItem] = field(default_factory=dict, init=False)
    _inferences: list[Inference] = field(default_factory=list, init=False)
    _contradictions: list[dict[str, str]] = field(default_factory=list, init=False)

    def add_observation(
        self,
        evidence_id: str,
        text: str,
        *,
        kind: str = "observed_work",
        source_ref: str = "",
        note: str = "",
    ) -> EvidenceItem:
        """Record something the learner actually supplied."""
        if evidence_id in self._evidence:
            raise ReasoningEvidenceError(f"duplicate evidence_id: {evidence_id!r}")
        item = EvidenceItem(evidence_id, kind, text, "OBSERVED", source_ref, note)
        self._evidence[evidence_id] = item
        return item

    def add_unknown(self, evidence_id: str, description: str) -> EvidenceItem:
        """Record something the submission does not establish."""
        if evidence_id in self._evidence:
            raise ReasoningEvidenceError(f"duplicate evidence_id: {evidence_id!r}")
        item = EvidenceItem(evidence_id, "given", description, "UNKNOWN")
        self._evidence[evidence_id] = item
        return item

    def mark_verified(self, evidence_id: str, *, checked_by: str, agrees: bool) -> EvidenceItem:
        """Promote an observed item to VERIFIED only if a deterministic check agrees.

        A quotation is not evidence of correctness. If ``agrees`` is False the item
        stays OBSERVED and the failed check is recorded as a contradiction.
        """
        if evidence_id not in self._evidence:
            raise ReasoningEvidenceError(f"unknown evidence_id: {evidence_id!r}")
        current = self._evidence[evidence_id]
        if not checked_by.strip():
            raise ReasoningEvidenceError("checked_by must name the deterministic check")
        if not agrees:
            self._contradictions.append(
                {"evidence_id": evidence_id, "checked_by": checked_by,
                 "result": "check disagreed; grade remains OBSERVED"}
            )
            return current
        promoted = EvidenceItem(
            current.evidence_id, current.kind, current.text, "VERIFIED",
            current.source_ref, current.note,
        )
        self._evidence[evidence_id] = promoted
        return promoted

    def add_inference(
        self,
        inference_id: str,
        statement: str,
        *,
        supporting: tuple[str, ...],
        contradicting: tuple[str, ...] = (),
        confidence: float = 0.5,
    ) -> Inference:
        """Record a conclusion. Every cited id must already exist."""
        for group in (supporting, contradicting):
            for ref in group:
                if ref not in self._evidence:
                    raise ReasoningEvidenceError(f"inference cites unknown evidence: {ref!r}")
        inference = Inference(inference_id, statement, tuple(supporting),
                             tuple(contradicting), confidence)
        self._inferences.append(inference)
        return inference

    def summary(self) -> dict[str, Any]:
        counts = {grade: 0 for grade in ("OBSERVED", "VERIFIED", "INFERRED", "UNKNOWN")}
        for item in self._evidence.values():
            counts[item.provenance] += 1
        counts["INFERRED"] = len(self._inferences)
        return {
            "question_id": self.question_id,
            "counts_by_provenance": counts,
            "n_unresolved_unknowns": counts["UNKNOWN"],
            "n_contradictions": len(self._contradictions),
            "evidence_supported_conclusions": sum(
                1 for inf in self._inferences if inf.supporting and not inf.contradicting
            ),
            "conclusions_with_conflicting_evidence": sum(
                1 for inf in self._inferences if inf.contradicting
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "evidence": [
                {
                    "evidence_id": e.evidence_id, "kind": e.kind, "text": e.text,
                    "provenance": e.provenance, "source_ref": e.source_ref,
                    "note": e.note,
                }
                for e in self._evidence.values()
            ],
            "inferences": [i.to_dict() for i in self._inferences],
            "contradictions": list(self._contradictions),
            "summary": self.summary(),
        }


def from_answer_check(
    question_id: str,
    learner_answer: str,
    *,
    expected_answer: str,
    status: str,
    agrees: bool,
) -> ReasoningRecord:
    """Build a record from one deterministic answer check.

    The learner's final answer is OBSERVED. It becomes VERIFIED only when the
    deterministic verifier returned CORRECT. Nothing about the learner's method is
    recorded, because the final answer alone cannot establish it.
    """
    record = ReasoningRecord(question_id)
    record.add_observation("submitted_answer", learner_answer, kind="student_statement")
    if status == "CORRECT":
        record.mark_verified("submitted_answer", checked_by="answer_verifier", agrees=agrees)
    elif agrees:
        record.mark_verified("submitted_answer", checked_by="answer_verifier", agrees=True)
    record.add_unknown(
        "reasoning_path",
        "The working shown does not establish a unique method for reaching the answer.",
    )
    return record
