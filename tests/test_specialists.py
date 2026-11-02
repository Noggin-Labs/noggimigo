import pytest

from noggimigo.specialists import (
    DomainRegistry,
    MathAnswerSpecialist,
    SpecialistResult,
)


@pytest.fixture
def registry():
    registry = DomainRegistry()
    registry.register(MathAnswerSpecialist())
    return registry


def test_equivalent_fraction_is_correct(registry):
    result = registry.analyse(
        "math",
        prompt="What is one half?",
        response="0.5",
        expected_answer="1/2",
    )

    assert result.status == "ANALYSED"
    assert result.claims
    assert "matches" in result.claims[0]


def test_incorrect_answer_does_not_diagnose_misconception(registry):
    result = registry.analyse(
        "math",
        prompt="Solve 2 + 2.",
        response="5",
        expected_answer="4",
    )

    assert result.status == "ANALYSED"
    assert result.uncertainties
    assert any(
        "reasoning" in item or "misconception" in item
        for item in result.uncertainties
    )


def test_missing_expected_answer_abstains(registry):
    result = registry.analyse(
        "math",
        prompt="Solve 2 + 2.",
        response="4",
    )

    assert result.status == "INSUFFICIENT_EVIDENCE"


def test_unknown_domain_abstains(registry):
    result = registry.analyse(
        "chemistry",
        prompt="Explain the reaction.",
        response="I don't know.",
    )

    assert result.status == "INSUFFICIENT_EVIDENCE"


def test_duplicate_registration_is_rejected(registry):
    with pytest.raises(ValueError):
        registry.register(MathAnswerSpecialist())


def test_specialist_exception_does_not_leak_error(registry):

    class BrokenSpecialist:
        domain = "physics"

        def analyse(self, **kwargs):
            raise RuntimeError("sensitive internal error")

    registry.register(BrokenSpecialist())

    result = registry.analyse(
        "physics",
        prompt="Explain velocity.",
        response="Something.",
    )

    assert result.status == "ERROR"
    assert "sensitive internal error" not in str(result)


def test_invalid_answer_abstains(registry):
    result = registry.analyse(
        "math",
        prompt="What is 1/2?",
        response="",
        expected_answer="1/2",
    )

    assert result.status == "INSUFFICIENT_EVIDENCE"
