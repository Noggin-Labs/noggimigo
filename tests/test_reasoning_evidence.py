"""Tests for the reasoning-evidence representation and its invariants."""

import pytest

from noggimigo.reasoning_evidence import (
    ReasoningEvidenceError,
    ReasoningRecord,
    from_answer_check,
)


def test_inference_requires_supporting_evidence():
    with pytest.raises(ReasoningEvidenceError):
        ReasoningRecord("q1").add_inference("inf1", "learner added instead of subtracted", supporting=())


def test_inference_cannot_cite_unknown_evidence():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 14")
    with pytest.raises(ReasoningEvidenceError):
        record.add_inference("inf1", "invalid operation", supporting=("work_1", "work_999"))


def test_confidence_must_be_a_probability():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 14")
    with pytest.raises(ReasoningEvidenceError):
        record.add_inference("inf1", "x", supporting=("work_1",), confidence=1.4)


def test_a_quotation_is_observed_not_verified():
    """Quoting a step is not evidence that it is correct."""
    record = ReasoningRecord("q1")
    item = record.add_observation("work_1", "2x = 14")
    assert item.provenance == "OBSERVED"


def test_mark_verified_requires_an_agreeing_check():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 8")
    promoted = record.mark_verified("work_1", checked_by="algebra_check", agrees=True)
    assert promoted.provenance == "VERIFIED"


def test_failed_check_keeps_observed_grade_and_records_contradiction():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 14")
    item = record.mark_verified("work_1", checked_by="algebra_check", agrees=False)
    assert item.provenance == "OBSERVED"
    assert record.summary()["n_contradictions"] == 1


def test_contradicting_evidence_is_preserved():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 14")
    record.add_observation("work_2", "2x = 8")
    record.add_inference(
        "inf1", "the two lines are inconsistent", supporting=("work_1",), contradicting=("work_2",)
    )
    summary = record.summary()
    assert summary["conclusions_with_conflicting_evidence"] == 1


def test_unknown_items_are_counted_separately():
    record = ReasoningRecord("q1")
    record.add_unknown("reasoning_path", "final answer alone does not determine method")
    assert record.summary()["n_unresolved_unknowns"] == 1


def test_evidence_cannot_be_constructed_as_inferred():
    record = ReasoningRecord("q1")
    with pytest.raises(ReasoningEvidenceError):
        record.add_inference("inf1", "x", supporting=())
    with pytest.raises(ReasoningEvidenceError):
        from noggimigo.reasoning_evidence import EvidenceItem

        EvidenceItem("e1", "observed_work", "text", "INFERRED")


def test_duplicate_evidence_ids_are_rejected():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "a")
    with pytest.raises(ReasoningEvidenceError):
        record.add_observation("work_1", "b")


def test_schema_has_no_learner_trait_field():
    """The representation cannot store a diagnosis about the learner as a person."""
    record = ReasoningRecord("q1")
    blob = str(record.to_dict())
    for forbidden in ("ability", "disability", "attention", "motivation", "intelligence"):
        assert forbidden not in blob


def test_serialisation_preserves_provenance():
    record = ReasoningRecord("q1")
    record.add_observation("work_1", "2x = 8")
    record.mark_verified("work_1", checked_by="algebra_check", agrees=True)
    record.add_unknown("reasoning_path", "unknown")
    record.add_inference("inf1", "isolated x correctly", supporting=("work_1",))
    data = record.to_dict()
    assert data["evidence"][0]["provenance"] == "VERIFIED"
    assert data["inferences"][0]["provenance"] == "INFERRED"
    assert data["summary"]["counts_by_provenance"]["VERIFIED"] == 1


def test_from_answer_check_never_claims_reasoning():
    record = from_answer_check(
        "step_1", "0.25", expected_answer="1/4", status="CORRECT", agrees=True
    )
    data = record.to_dict()
    assert data["evidence"][0]["provenance"] == "VERIFIED"
    assert any(item["provenance"] == "UNKNOWN" for item in data["evidence"])
    assert all("reason" not in inf["statement"].lower().replace("reasoning_path", "")
               for inf in data["inferences"])
