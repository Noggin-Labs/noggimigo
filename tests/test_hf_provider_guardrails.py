import json
import pytest

from noggimigo.hf_provider import ModelOutputError, parse_model_output


def valid_payload():
    return {
        "student_facing_message": "What could you try first?",
        "pedagogical_action": "ASK_GUIDING_QUESTION",
        "misconception_candidates": [],
        "requires_verification": True,
    }


@pytest.mark.parametrize(
    "action",
    [None, 1, [], {}, ["ASK_GUIDING_QUESTION"]],
)
def test_invalid_actions_raise_model_output_error(action):
    payload = valid_payload()
    payload["pedagogical_action"] = action

    with pytest.raises(ModelOutputError):
        parse_model_output(json.dumps(payload))


@pytest.mark.parametrize(
    "candidates",
    [None, "invalid", [1], [""], ["a", "b", "c", "d"]],
)
def test_invalid_candidates_are_rejected(candidates):
    payload = valid_payload()
    payload["misconception_candidates"] = candidates

    with pytest.raises(ModelOutputError):
        parse_model_output(json.dumps(payload))


def test_valid_output_is_accepted():
    result = parse_model_output(json.dumps(valid_payload()))
    assert result["requires_verification"] is True


def test_non_boolean_verification_is_rejected():
    payload = valid_payload()
    payload["requires_verification"] = "true"

    with pytest.raises(ModelOutputError):
        parse_model_output(json.dumps(payload))
