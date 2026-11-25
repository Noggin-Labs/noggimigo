import json

import pytest

from noggimigo.ollama_provider import OllamaLocalTutor


VALID_SUGGESTION = {
    "student_facing_message": "What happens if you split each half into two equal parts?",
    "pedagogical_action": "ASK_GUIDING_QUESTION",
    "misconception_candidates": [],
    "requires_verification": True,
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def fake_opener_for(payload, captured):
    def opener(request, *, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(payload)
    return opener


def test_ollama_provider_posts_chat_and_parses_structured_output():
    captured = {}
    api_response = {"message": {"role": "assistant", "content": json.dumps(VALID_SUGGESTION)}}
    tutor = OllamaLocalTutor(opener=fake_opener_for(api_response, captured))

    result = tutor.generate(
        "Explain equivalent fractions.",
        "I don't understand.",
        lesson_context={"title": "Fractions"},
        deterministic_feedback="Try comparing equal-sized wholes.",
    )

    assert result == VALID_SUGGESTION
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["body"]["model"] == "llama3.2:latest"
    assert captured["body"]["stream"] is False
    assert captured["body"]["format"] == "json"
    assert captured["body"]["options"]["temperature"] == 0
    assert captured["body"]["messages"][0]["role"] == "system"


def test_ollama_provider_rejects_missing_message_content():
    captured = {}
    tutor = OllamaLocalTutor(
        opener=fake_opener_for({"message": {"role": "assistant"}}, captured)
    )

    with pytest.raises(RuntimeError, match="message content"):
        tutor.generate("Prompt", "Response")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model": ""},
        {"base_url": ""},
        {"timeout": 0},
        {"timeout": True},
        {"max_new_tokens": 0},
        {"max_new_tokens": True},
    ],
)
def test_ollama_provider_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        OllamaLocalTutor(**kwargs)


def test_ollama_provider_propagates_connection_errors():
    def broken_opener(request, *, timeout):
        raise TimeoutError("local service timed out")

    tutor = OllamaLocalTutor(opener=broken_opener)
    with pytest.raises(TimeoutError):
        tutor.generate("Prompt", "Response")
