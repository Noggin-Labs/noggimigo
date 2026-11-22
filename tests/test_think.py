import pytest

from noggimigo.think import build_teaching_plan


def plan(status, **kwargs):
    return build_teaching_plan(
        status,
        question="Solve the next step.",
        deterministic_feedback="Try one small step.",
        **kwargs,
    )


def test_correct_answer_produces_continue_plan_without_mastery_claim():
    result = plan("CORRECT").to_dict()
    assert result["learner_state"] == "verified_correct"
    assert result["pedagogical_action"] == "ACKNOWLEDGE_AND_CONTINUE"
    assert "mastery" in result["must_avoid"][0].lower()
    assert result["requires_verification"] is True


def test_incorrect_answer_uses_one_step_hint_by_default():
    result = plan("INCORRECT", hint="Undo addition with subtraction.").to_dict()
    assert result["strategy"] == "one_step_scaffold"
    assert result["focus"] == "Undo addition with subtraction."
    assert result["pedagogical_action"] == "GIVE_SMALL_HINT"


def test_incorrect_answer_can_use_guided_reconsideration():
    result = plan(
        "INCORRECT",
        hint="Undo addition.",
        preferences={"one_step_at_a_time": False},
    ).to_dict()
    assert result["strategy"] == "guided_reconsideration"
    assert result["focus"] == "Invite the learner to check one part of their approach."


def test_ambiguous_answer_requests_clarification_not_judgement():
    result = plan("AMBIGUOUS").to_dict()
    assert result["learner_state"] == "response_ambiguous"
    assert result["pedagogical_action"] == "ASK_WHAT_IS_CONFUSING"
    assert "Treating the response as correct or incorrect" in result["must_avoid"]


def test_invalid_answer_requests_rephrase_without_calling_it_wrong():
    result = plan("INVALID").to_dict()
    assert result["learner_state"] == "response_uninterpretable"
    assert result["pedagogical_action"] == "ASK_GUIDING_QUESTION"
    assert "Calling the answer mathematically wrong" in result["must_avoid"]


def test_hint_request_uses_explicit_curriculum_hint():
    result = plan("HINT_REQUESTED", hint="Look at the denominator.").to_dict()
    assert result["strategy"] == "give_curriculum_hint"
    assert result["focus"] == "Look at the denominator."
    assert result["pedagogical_action"] == "GIVE_SMALL_HINT"


def test_hint_request_without_hint_asks_a_guiding_question():
    result = plan("HINT_REQUESTED").to_dict()
    assert result["strategy"] == "ask_guiding_question"
    assert result["focus"].startswith("Ask what part")


@pytest.mark.parametrize("status", ["UNKNOWN", "", None])
def test_unsupported_status_is_rejected(status):
    with pytest.raises(ValueError):
        plan(status)


def test_missing_question_or_feedback_is_rejected():
    with pytest.raises(ValueError):
        build_teaching_plan("CORRECT", question=" ", deterministic_feedback="feedback")
    with pytest.raises(ValueError):
        build_teaching_plan("CORRECT", question="Question?", deterministic_feedback="")


def test_invalid_preference_type_is_rejected():
    with pytest.raises(ValueError):
        plan("INCORRECT", preferences={"one_step_at_a_time": "yes"})
