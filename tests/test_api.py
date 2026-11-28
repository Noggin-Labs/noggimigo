from fastapi.testclient import TestClient

from noggimigo.api import create_app


def test_create_session_returns_first_prompt_and_isolates_sessions():
    client = TestClient(create_app())
    first = client.post("/api/sessions", json={"lesson_id": "fractions_intro"})
    second = client.post("/api/sessions", json={"lesson_id": "algebra_intro"})

    assert first.status_code == 201
    assert second.status_code == 201
    first_data = first.json()
    second_data = second.json()
    assert first_data["session_id"] != second_data["session_id"]
    assert first_data["prompt"]["progress"] == "1/2"
    assert first_data["lesson"]["topic"] == "fractions"
    assert second_data["lesson"]["topic"] == "algebra"


def test_hint_does_not_advance_the_lesson():
    client = TestClient(create_app())
    created = client.post("/api/sessions", json={"lesson_id": "fractions_intro"}).json()

    hinted = client.post(f"/api/sessions/{created['session_id']}/hint")

    assert hinted.status_code == 200
    assert hinted.json()["result"]["status"] == "HINT_REQUESTED"
    assert hinted.json()["result"]["advanced"] is False
    assert hinted.json()["prompt"]["progress"] == "1/2"


def test_answer_uses_deterministic_verifier_and_advances_only_when_correct():
    client = TestClient(create_app())
    created = client.post("/api/sessions", json={"lesson_id": "fractions_intro"}).json()
    session_id = created["session_id"]

    incorrect = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "3/4"})
    assert incorrect.status_code == 200
    assert incorrect.json()["result"]["status"] == "INCORRECT"
    assert incorrect.json()["result"]["advanced"] is False
    assert incorrect.json()["prompt"]["progress"] == "1/2"

    correct = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "1/4"})
    assert correct.status_code == 200
    assert correct.json()["result"]["status"] == "CORRECT"
    assert correct.json()["result"]["advanced"] is True
    assert correct.json()["prompt"]["progress"] == "2/2"


def test_unknown_and_unsupported_sessions_are_rejected():
    client = TestClient(create_app())

    unsupported = client.post("/api/sessions", json={"lesson_id": "photosynthesis_intro"})
    missing = client.get("/api/sessions/00000000-0000-0000-0000-000000000000")

    assert unsupported.status_code == 422
    assert missing.status_code == 404


def test_blank_and_oversized_answers_are_rejected():
    client = TestClient(create_app())
    created = client.post("/api/sessions", json={"lesson_id": "algebra_intro"}).json()
    session_id = created["session_id"]

    blank = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "   "})
    oversized = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "x" * 201})

    assert blank.status_code == 422
    assert oversized.status_code == 422
