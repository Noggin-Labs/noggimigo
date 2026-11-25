"""Optional local Ollama adapter for Noggimigo.

The model proposes wording only. Deterministic verification and pedagogy
validation remain in the session runtime.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional
from urllib.request import Request, urlopen

from .hf_provider import build_messages, parse_model_output

DEFAULT_MODEL = "llama3.2:latest"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 60.0


class OllamaLocalTutor:
    """Generate a structured tutoring suggestion through Ollama's local API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_new_tokens: int = 180,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string.")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty string.")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or timeout <= 0
        ):
            raise ValueError("timeout must be a positive number.")
        if (
            isinstance(max_new_tokens, bool)
            or not isinstance(max_new_tokens, int)
            or max_new_tokens <= 0
        ):
            raise ValueError("max_new_tokens must be a positive integer.")

        self.model = model.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)
        self.max_new_tokens = max_new_tokens
        self._opener = opener or urlopen

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
        """Return one parsed candidate; network and parse failures propagate."""

        messages = build_messages(
            prompt,
            learner_response,
            subject=subject,
            level=level,
            lesson_context=lesson_context,
            deterministic_feedback=deterministic_feedback,
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": self.max_new_tokens,
            },
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self._opener(request, timeout=self.timeout) as response:
            raw_response = response.read()

        try:
            response_data = json.loads(raw_response)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
            raise RuntimeError("Ollama returned an invalid API response.") from exc

        if not isinstance(response_data, dict):
            raise RuntimeError("Ollama API response must be a JSON object.")

        message = response_data.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Ollama API response did not contain a message object.")

        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama API response did not contain message content.")

        return parse_model_output(content)
