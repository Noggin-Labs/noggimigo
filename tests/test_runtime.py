import json
import importlib
import pytest
from noggimigo.answer_verifier import verify_answer
from noggimigo.evaluation import brier_score, expected_calibration_error, monotonicity_violation_rate
from noggimigo.mastery import BKTParameters, BKTState, MasteryTracker
from noggimigo.session import NoggimigoSession
from noggimigo.hf_provider import HuggingFaceLocalTutor


def test_public_imports_and_case_sensitive_module():
    importlib.import_module("noggimigo.intent")
    importlib.import_module("noggimigo")
    importlib.import_module("noggimigo.LessonGenerator")

@pytest.mark.parametrize("student, expected", [("0.25", "1/4"), ("2/8", "1/4"), (" 1 / 4 ", "1/4")])
def test_equivalent_math_answers(student, expected):
    assert verify_answer(student, expected).correct

def test_invalid_fraction_and_division_by_zero_rejected():
    assert not verify_answer("1/0", "1/4").correct
    assert not verify_answer("3/4", "1/4").correct

def test_session_progression_and_incorrect_answer_cannot_advance():
    session = NoggimigoSession("fractions_intro")
    assert session.current_prompt()["progress"] == "1/2"
    bad = session.submit("3/4")
    assert bad["advanced"] is False
    assert session.current_prompt()["progress"] == "1/2"
    good = session.submit("0.25")
    assert good["advanced"] is True
    assert session.current_prompt()["progress"] == "2/2"
    assert session.submit("1/8")["completed"] is True
    assert session.complete

def test_hint_reset_and_bounded_history():
    session = NoggimigoSession(history_limit=2)
    session.request_hint(); session.submit("bad"); session.request_hint()
    assert len(session.history) == 2
    session.reset("algebra_intro")
    assert session.current_prompt()["progress"] == "1/2"
    assert not session.history

def test_model_failure_falls_back():
    class Broken:
        def generate(self, *args, **kwargs): raise RuntimeError("no model")
    result = NoggimigoSession(model=Broken()).submit("wrong")
    assert result["advanced"] is False and result["model_fallback"] is True

def test_mocked_model_structured_output():
    good = {"student_facing_message":"What operation undoes +4?","pedagogical_action":"ASK_GUIDING_QUESTION","misconception_candidates":[],"requires_verification":True}
    class Tokenizer:
        eos_token_id = 0
        def apply_chat_template(self, *a, **k):
            class T:
                shape = [1, 3]
                def to(self, device): return self
            return T()
        def decode(self, *a, **k): return json.dumps(good)
    class Model:
        device = "cpu"
        def eval(self): pass
        def generate(self, *a, **k):
            class O:
                def __getitem__(self, i): return [0]
            return O()
    assert HuggingFaceLocalTutor(loader=lambda _: (Tokenizer(), Model())).generate("q", "a")==good


def test_bkt_correct_response_increases_mastery_and_wrong_response_updates_state():
    state = BKTState(BKTParameters(p_init=0.2, p_learn=0.1, p_guess=0.2, p_slip=0.1))
    before = state.p_mastery
    state.update(True)
    after_correct = state.p_mastery
    state.update(False)
    assert after_correct > before
    assert state.p_mastery < after_correct
    assert state.observations == 2


def test_mastery_tracker_returns_bkt_and_mirt_predictions():
    tracker = MasteryTracker(["fractions"])
    event = tracker.observe(["fractions"], correct=True)
    assert event["bkt_mastery"]["fractions"] > 0.2
    assert 0.0 < event["mirt_prediction"] < 1.0
    assert tracker.mirt_snapshot()["fractions"] > 0.0


def test_session_exposes_mastery_and_records_answer_event():
    session = NoggimigoSession("fractions_intro")
    result = session.submit("3/4")
    assert "mastery" in result
    assert result["mastery"]["bkt"]["part_whole"] < 0.2
    assert session.history[-1]["knowledge_components"] == ["part_whole", "fraction_notation"]


def test_study_metrics_are_deterministic_and_bounded():
    predictions = [0.1, 0.8, 0.9, 0.2]
    outcomes = [False, True, True, False]
    assert brier_score(predictions, outcomes) == pytest.approx(0.025)
    assert expected_calibration_error(predictions, outcomes, bins=2) == pytest.approx(0.15)
    assert monotonicity_violation_rate([0.1, 0.2, 0.15, 0.4]) == pytest.approx(1 / 3)
