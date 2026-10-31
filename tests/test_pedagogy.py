import pytest

from noggimigo.pedagogy import PedagogicalValidationError, validate_suggestion


def suggestion(**overrides):
    data = {
        "student_facing_message": "What could you try first?",
        "pedagogical_action": "ASK_GUIDING_QUESTION",
        "misconception_candidates": [],
        "requires_verification": True,
    }
    data.update(overrides)
    return data


def validate(data, *, status="INCORRECT", expected="1/4", **kwargs):
    return validate_suggestion(data, answer_status=status, expected_answer=expected, **kwargs)


def test_valid_suggestion_is_accepted():
    assert validate(suggestion())["pedagogical_action"] == "ASK_GUIDING_QUESTION"


@pytest.mark.parametrize("bad", [None, [], "message", {"student_facing_message": "hi"}])
def test_missing_or_invalid_top_level_structure_is_rejected(bad):
    with pytest.raises(PedagogicalValidationError):
        validate(bad)

@pytest.mark.parametrize("message", ["", "   ", "x" * 401, "Try\x00this", "First? Second?"])
def test_invalid_messages_are_rejected(message):
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message=message))

@pytest.mark.parametrize("action,status", [("GIVE_SMALL_HINT", "CORRECT"), ("ACKNOWLEDGE_AND_CONTINUE", "INCORRECT"), ("NOPE", "INCORRECT"), (None, "INCORRECT"), ([], "INCORRECT")])
def test_incompatible_or_unsupported_actions_are_rejected(action, status):
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(pedagogical_action=action), status=status)

@pytest.mark.parametrize("status,action", [
    ("CORRECT", "GIVE_SMALL_HINT"),
    ("INCORRECT", "ACKNOWLEDGE_AND_CONTINUE"),
    ("INVALID", "ACKNOWLEDGE_AND_CONTINUE"),
    ("AMBIGUOUS", "ACKNOWLEDGE_AND_CONTINUE"),
])
def test_action_status_mismatch_is_rejected(status, action):
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(pedagogical_action=action), status=status)


def test_expected_answer_fraction_and_decimal_leakage_are_rejected():
    for message in ("The answer is 1/4.", "That is 0.25 of the whole."):
        with pytest.raises(PedagogicalValidationError):
            validate(suggestion(student_facing_message=message))


def test_text_answer_leakage_is_rejected():
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message="The answer is subtract 4."), expected="subtract 4")


def test_single_digit_answer_only_rejected_when_explicitly_given():
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message="The answer is 3."), expected="3")
    assert validate(suggestion(student_facing_message="Try step 3 first."), expected="3")


def test_false_verification_flag_is_rejected():
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(requires_verification=False))


def test_excessive_or_invalid_misconception_candidates_are_rejected():
    for candidates in (["a", "b", "c", "d"], [""], [1], ["x" * 161]):
        with pytest.raises(PedagogicalValidationError):
            validate(suggestion(misconception_candidates=candidates))


def test_unsupported_correctness_and_progression_claims_are_rejected():
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message="Correct! Try another way."), status="INCORRECT")
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message="You have advanced to the next question."), status="CORRECT")


def test_verified_correctness_claim_is_allowed_but_mastery_claim_is_not():
    data = suggestion(student_facing_message="Correct! What helped you decide?", pedagogical_action="ACKNOWLEDGE_AND_CONTINUE")
    assert validate(data, status="CORRECT", expected="1/4", progression_verified=True)
    with pytest.raises(PedagogicalValidationError):
        validate(suggestion(student_facing_message="You mastered fractions!", pedagogical_action="ACKNOWLEDGE_AND_CONTINUE"), status="CORRECT", progression_verified=True)


def test_completion_claim_requires_verified_completion():
    data = suggestion(student_facing_message="Lesson complete!", pedagogical_action="ACKNOWLEDGE_AND_CONTINUE")
    with pytest.raises(PedagogicalValidationError):
        validate(data, status="CORRECT", expected="1/8", progression_verified=True)
    assert validate(data, status="CORRECT", expected="1/8", progression_verified=True, lesson_complete_verified=True)


def test_unknown_or_malformed_answer_status_is_rejected():
    with pytest.raises(PedagogicalValidationError):
        validate_suggestion(suggestion(), answer_status=[])
