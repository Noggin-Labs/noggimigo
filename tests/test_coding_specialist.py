import pytest

from noggimigo.coding_specialist import PythonSyntaxSpecialist


@pytest.fixture
def specialist():
    return PythonSyntaxSpecialist()


def test_valid_python_is_analysed(specialist):
    result = specialist.analyse(
        prompt="Write an addition function.",
        response="def add(a, b):\n    return a + b",
    )

    assert result.status == "ANALYSED"
    assert any("syntactically valid" in claim for claim in result.claims)


def test_invalid_python_reports_syntax_error(specialist):
    result = specialist.analyse(
        prompt="Write a function.",
        response="def add(a, b)\n    return a + b",
    )

    assert result.status == "ANALYSED"
    assert any("syntax error" in claim for claim in result.claims)


def test_empty_submission_abstains(specialist):
    result = specialist.analyse(
        prompt="Write a function.",
        response="   ",
    )

    assert result.status == "INSUFFICIENT_EVIDENCE"


def test_large_submission_is_rejected():
    specialist = PythonSyntaxSpecialist(max_source_chars=20)

    result = specialist.analyse(
        prompt="Write code.",
        response="x = 1\n" * 10,
    )

    assert result.status == "INSUFFICIENT_EVIDENCE"


def test_valid_syntax_does_not_claim_logical_correctness(specialist):
    result = specialist.analyse(
        prompt="Write a function that adds two numbers.",
        response="def add(a, b):\n    return a - b",
    )

    assert result.status == "ANALYSED"
    assert any(
        "Logical correctness has not been established." in item
        for item in result.uncertainties
    )


def test_code_is_not_executed(specialist):
    result = specialist.analyse(
        prompt="Write Python.",
        response="raise RuntimeError('this must not execute')",
    )

    assert result.status == "ANALYSED"
    assert any("syntactically valid" in claim for claim in result.claims)
