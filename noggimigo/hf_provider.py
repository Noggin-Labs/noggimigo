
"""Optional local Hugging Face model adapter for Noggimigo.

This module deliberately does not replace Noggimigo's deterministic lesson,
answer-checking, misconception, or accommodation logic. It generates a
candidate tutoring utterance; the application remains responsible for checking
answers and deciding whether the utterance is safe and pedagogically valid.
"""
from __future__ import annotations

import json
import re
from contextlib import nullcontext
from typing import Any, Callable, Optional

DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"
MAX_MISCONCEPTION_CANDIDATES = 3

PEDAGOGICAL_ACTIONS = {
    "ASK_GUIDING_QUESTION",
    "GIVE_SMALL_HINT",
    "ACKNOWLEDGE_AND_CONTINUE",
    "ASK_WHAT_IS_CONFUSING",
    "EXPLAIN_ONE_STEP",
}

SYSTEM_PROMPT = """You are Noggimigo, a patient Socratic learning assistant.
Help the learner reason; do not rush to give the final answer.
Use the supplied lesson context as the source of truth.
Ask at most one clear question at a time. Keep language concise and encouraging.
Never infer or diagnose a disability, attention state, intelligence, or emotion
from a learner's writing or response time. Do not claim to measure brain activity.
Do not invent mathematical facts. If uncertain, ask a clarifying question.
Return exactly one JSON object with these keys:
{
  "student_facing_message": "string",
  "pedagogical_action": "one allowed action",
  "misconception_candidates": ["string", "..."],
  "requires_verification": true
}
The pedagogical_action must be one of:
ASK_GUIDING_QUESTION, GIVE_SMALL_HINT, ACKNOWLEDGE_AND_CONTINUE,
ASK_WHAT_IS_CONFUSING, EXPLAIN_ONE_STEP.
Set requires_verification to true whenever the message contains a factual,
mathematical, or lesson-progression claim."""


class ModelOutputError(ValueError):
    """Raised when the model does not return the required structured output."""


def build_messages(
    prompt: str,
    learner_response: str,
    *,
    subject: str = "mathematics",
    level: str = "unspecified",
    lesson_context: Optional[dict[str, Any]] = None,
    deterministic_feedback: Optional[str] = None,
) -> list[dict[str, str]]:
    """Build a minimal, non-identifying prompt; do not include learner PII."""
    context = {
        "subject": subject,
        "level": level,
        "lesson_context": lesson_context or {},
        "deterministic_feedback": deterministic_feedback,
    }

    user_content = (
        "Lesson context (JSON):\n"
        + json.dumps(context, ensure_ascii=False, sort_keys=True)
        + "\nCurrent tutor prompt:\n"
        + prompt
        + "\nLearner response:\n"
        + learner_response
        + "\nRespond with the required JSON object only."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_model_output(raw: str) -> dict[str, Any]:
    """Parse and validate the model output contract; reject malformed output."""
    if not isinstance(raw, str):
        raise ModelOutputError("Model output must be a string.")

    candidate = raw.strip()

    if not candidate:
        raise ModelOutputError("Model output was empty.")

    # Permit a fenced JSON response, but no surrounding explanatory prose.
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        candidate,
        flags=re.S | re.I,
    )
    if fenced:
        candidate = fenced.group(1)

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ModelOutputError("Model output was not valid JSON.") from exc

    required = {
        "student_facing_message",
        "pedagogical_action",
        "misconception_candidates",
        "requires_verification",
    }

    if not isinstance(data, dict) or set(data) != required:
        raise ModelOutputError("Model output did not match the required keys.")

    message = data["student_facing_message"]
    if not isinstance(message, str) or not message.strip():
        raise ModelOutputError(
            "student_facing_message must be a non-empty string."
        )

    action = data["pedagogical_action"]
    if not isinstance(action, str) or action not in PEDAGOGICAL_ACTIONS:
        raise ModelOutputError("Unknown pedagogical_action.")

    candidates = data["misconception_candidates"]
    if (
        not isinstance(candidates, list)
        or len(candidates) > MAX_MISCONCEPTION_CANDIDATES
        or not all(
            isinstance(item, str) and item.strip()
            for item in candidates
        )
    ):
        raise ModelOutputError(
            "misconception_candidates must contain at most three "
            "non-empty strings."
        )

    if not isinstance(data["requires_verification"], bool):
        raise ModelOutputError(
            "requires_verification must be a boolean."
        )

    return data


class HuggingFaceLocalTutor:
    """Lazy-loaded Transformers adapter; model weights stay on the user's device."""

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        *,
        max_new_tokens: int = 180,
        loader: Optional[Callable[..., tuple[Any, Any]]] = None,
    ):
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("model_id must be a non-empty string.")

        if (
            not isinstance(max_new_tokens, int)
            or isinstance(max_new_tokens, bool)
            or max_new_tokens <= 0
        ):
            raise ValueError("max_new_tokens must be a positive integer.")

        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self._loader = loader
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return

        if self._loader is not None:
            self._tokenizer, self._model = self._loader(self.model_id)
            if self._tokenizer is None or self._model is None:
                raise RuntimeError("The custom model loader returned an invalid pair.")
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Local model dependencies are missing. Install the optional "
                "requirements in requirements-hf-local.txt."
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype="auto",
            device_map="auto",
        )
        self._model.eval()

    def generate(
        self,
        prompt: str,
        learner_response: str,
        *,
        subject: str = "mathematics",
        level: str = "unspecified",
        lesson_context: Optional[dict[str, Any]] = None,
        deterministic_feedback: Optional[str] = None,
    ) -> dict[str, Any]:
        self._load()

        messages = build_messages(
            prompt,
            learner_response,
            subject=subject,
            level=level,
            lesson_context=lesson_context,
            deterministic_feedback=deterministic_feedback,
        )

        encoded = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )

        # Move inputs to the model's input device without assuming CUDA exists.
        input_device = getattr(self._model, "device", None)
        if input_device is not None:
            encoded = encoded.to(input_device)

        try:
            import torch
            inference_context = torch.inference_mode()
        except ImportError:
            # Mock loaders remain usable without heavyweight dependencies.
            inference_context = nullcontext()

        with inference_context:
            output = self._model.generate(
                encoded,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        new_tokens = output[0][encoded.shape[-1]:]
        raw = self._tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        )

        return parse_model_output(raw)
