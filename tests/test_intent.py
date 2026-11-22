import pytest

from noggimigo.intent import Intent, IntentRecognizer, NoggimigoIntentAI


@pytest.fixture
def recognizer():
    return IntentRecognizer()


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("1/4", Intent.ANSWER_SUBMISSION),
        ("x = 5", Intent.ANSWER_SUBMISSION),
        ("subtract 4", Intent.ANSWER_SUBMISSION),
        ("I think it is one quarter", Intent.ANSWER_SUBMISSION),
        ("Why do we divide here?", Intent.QUESTION),
        ("What does the denominator mean?", Intent.QUESTION),
        ("Can you tell me why?", Intent.QUESTION),
        ("Can I get a hint?", Intent.HINT_REQUEST),
        ("Give me a clue", Intent.ANSWER_SUBMISSION),
        ("Give me a hint", Intent.HINT_REQUEST),
        ("hint", Intent.HINT_REQUEST),
        ("Please explain this another way", Intent.EXPLANATION_REQUEST),
        ("Walk me through the first step", Intent.EXPLANATION_REQUEST),
        ("I don't understand", Intent.CONFUSION),
        ("I'm stuck", Intent.CONFUSION),
        ("This makes no sense", Intent.CONFUSION),
    ],
)
def test_classifies_common_learner_intents(recognizer, message, expected):
    result = recognizer.classify(message)
    assert result.intent is expected
    assert 0.0 <= result.confidence <= 1.0
    assert result.evidence


def test_empty_input_is_uncertain(recognizer):
    result = recognizer.classify("  ")
    assert result.intent is Intent.UNCERTAIN
    assert result.confidence == 0.0


def test_explicit_request_takes_priority_over_question_mark(recognizer):
    assert recognizer.classify("Can I get a hint?").intent is Intent.HINT_REQUEST
    assert recognizer.classify("Can you explain this?").intent is Intent.EXPLANATION_REQUEST


def test_answer_like_text_is_routed_but_never_graded(recognizer):
    result = recognizer.classify("1/4")
    assert result.intent is Intent.ANSWER_SUBMISSION
    assert "authoritative_answer_verifier" in result.evidence[0]


def test_normalization_is_stable(recognizer):
    result = recognizer.classify("  WHY   do we divide HERE? ")
    assert result.normalized_text == "why do we divide here?"
    assert result.intent is Intent.QUESTION


def test_non_string_input_is_rejected(recognizer):
    with pytest.raises(TypeError, match="string"):
        recognizer.classify(None)


def test_compatibility_facade_preserves_legacy_hint_token():
    classifier = NoggimigoIntentAI()
    assert classifier.predict_intent("give me a hint")["intent"] == "hint"
    assert classifier.predict_intent("1/4")["intent"] == "ANSWER_SUBMISSION"


def test_compatibility_facade_validates_threshold():
    with pytest.raises(ValueError, match="min_confidence"):
        NoggimigoIntentAI().predict_intent("hello", min_confidence=1.1)
