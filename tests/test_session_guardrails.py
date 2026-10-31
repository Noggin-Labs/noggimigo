from noggimigo.session import NoggimigoSession


class FixedModel:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
    def generate(self, *args, **kwargs):
        if self.error:
            raise self.error
        return self.output


def output(message, action="ASK_GUIDING_QUESTION", verification=True):
    return {
        "student_facing_message": message,
        "pedagogical_action": action,
        "misconception_candidates": [],
        "requires_verification": verification,
    }


def test_valid_model_suggestion_is_attached_without_changing_verification():
    model = FixedModel(output("What does the denominator tell us?"))
    result = NoggimigoSession(model=model).submit("3/4")
    assert result["status"] == "INCORRECT"
    assert result["advanced"] is False
    assert result["model_message"] == "What does the denominator tell us?"


def test_expected_answer_leakage_falls_back_to_deterministic_feedback():
    model = FixedModel(output("The answer is 1/4."))
    result = NoggimigoSession(model=model).submit("3/4")
    assert result["model_fallback"] is True
    assert "model_message" not in result
    assert result["advanced"] is False


def test_model_cannot_claim_incorrect_answer_is_correct():
    model = FixedModel(output("Correct!", "ASK_GUIDING_QUESTION"))
    result = NoggimigoSession(model=model).submit("3/4")
    assert result["model_fallback"] is True
    assert result["status"] == "INCORRECT"


def test_model_cannot_change_verified_progression():
    model = FixedModel(output("What helped you identify the remaining part?"))
    session = NoggimigoSession(model=model)
    result = session.submit("1/4")
    assert result["status"] == "CORRECT"
    assert result["advanced"] is True
    assert session.current_prompt()["progress"] == "2/2"


def test_false_verification_flag_falls_back():
    model = FixedModel(output("Try drawing the parts.", verification=False))
    result = NoggimigoSession(model=model).submit("3/4")
    assert result["model_fallback"] is True
    assert "model_message" not in result


def test_provider_failure_does_not_crash_or_change_deterministic_result():
    model = FixedModel(error=RuntimeError("provider unavailable"))
    result = NoggimigoSession(model=model).submit("3/4")
    assert result["model_fallback"] is True
    assert result["status"] == "INCORRECT"
    assert result["advanced"] is False
