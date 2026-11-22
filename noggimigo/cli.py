"""Command-line interface backed by the shared session manager."""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from .curriculum import lesson_ids
from .hf_provider import DEFAULT_MODEL_ID, HuggingFaceLocalTutor
from .session import NoggimigoSession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Noggimigo local tutor")
    parser.add_argument("--lesson", choices=lesson_ids(), default="fractions_intro")
    parser.add_argument(
        "--model",
        action="store_true",
        help="enable the optional local Hugging Face tutor (downloads model weights if needed)",
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help=f"local Hugging Face model ID (default: {DEFAULT_MODEL_ID})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    model = HuggingFaceLocalTutor(model_id=args.model_id) if args.model else None
    session = NoggimigoSession(args.lesson, model=model)

    mode = f"local model: {args.model_id}" if model else "deterministic mode"
    print(f"Noggimigo tutor ({mode}). Type 'hint', 'reset', or 'exit'.")

    while not session.complete:
        prompt = session.current_prompt()
        print(f"\n[{prompt['progress']}] {prompt['question']}")
        answer = input("> ").strip()

        if answer.lower() == "exit":
            break
        if answer.lower() == "reset":
            session.reset()
            continue

        result = (
            session.request_hint()
            if answer.lower() in {"hint", "help", "?"}
            else session.submit(answer)
        )

        # A model message is displayed only after the session has validated it
        # against deterministic answer and progression state. Otherwise the
        # deterministic feedback remains the user-facing fallback.
        print(result.get("model_message") or result["feedback"])

    if session.complete:
        print("\nLesson complete. Nice work!")


if __name__ == "__main__":
    main()
