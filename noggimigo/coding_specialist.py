"""Static Python syntax analysis for Noggimigo.

This module parses source code but never executes it.
A successful parse does not establish program correctness.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Mapping

from .specialists import SpecialistResult


@dataclass
class PythonSyntaxSpecialist:
    domain: str = field(default="coding", init=False)
    max_source_chars: int = 20_000

    def analyse(
        self,
        *,
        prompt: str,
        response: str,
        expected_answer: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> SpecialistResult:

        source = response.strip()

        if not source:
            return SpecialistResult(
                domain=self.domain,
                status="INSUFFICIENT_EVIDENCE",
                uncertainties=("No Python source code was provided.",),
            )

        if len(source) > self.max_source_chars:
            return SpecialistResult(
                domain=self.domain,
                status="INSUFFICIENT_EVIDENCE",
                uncertainties=(
                    f"Source exceeds the {self.max_source_chars}-character limit.",
                ),
            )

        try:
            ast.parse(source, filename="<learner-submission>", mode="exec")

        except SyntaxError as error:
            location = (
                f"Line {error.lineno}"
                if error.lineno is not None
                else "Unknown line"
            )

            return SpecialistResult(
                domain=self.domain,
                status="ANALYSED",
                claims=("The submitted Python code contains a syntax error.",),
                uncertainties=(
                    f"{location}: {error.msg}",
                    "Syntax analysis does not identify the learner's reasoning.",
                ),
                evidence_refs=("python_ast_parser",),
            )

        except (ValueError, TypeError, MemoryError):
            return SpecialistResult(
                domain=self.domain,
                status="ERROR",
                uncertainties=("The source could not be parsed safely.",),
                requires_human_review=True,
            )

        return SpecialistResult(
            domain=self.domain,
            status="ANALYSED",
            claims=("The submitted code is syntactically valid Python.",),
            uncertainties=(
                "Runtime behaviour has not been tested.",
                "Logical correctness has not been established.",
                "No assumptions about the learner's understanding are made.",
            ),
            evidence_refs=("python_ast_parser",),
        )
