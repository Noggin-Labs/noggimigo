"""Command-line interface backed by the shared session manager."""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from .curriculum import lesson_ids
from .hf_provider import DEFAULT_MODEL_ID, HuggingFaceLocalTutor
from .session import NoggimigoSession
from .voice import KokoroLocalVoice, VoiceSettings


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
    parser.add_argument(
        "--speak",
        action="store_true",
        help="speak tutor messages using the optional local Kokoro voice",
    )
    parser.add_argument(
        "--tts-model-path",
        default="models/tts/kokoro-v1.0.onnx",
        help="path to the local Kokoro ONNX model",
    )
    parser.add_argument(
        "--tts-voices-path",
        default="models/tts/voices-v1.0.bin",
        help="path to the local Kokoro voice pack",
    )
    parser.add_argument(
        "--tts-voice",
        default="af_sarah",
        help="Kokoro speaker ID (default: af_sarah)",
    )
    parser.add_argument(
        "--speech-speed",
        type=float,
        default=0.95,
        help="speech speed from 0.5 to 2.0 (default: 0.95)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    model = HuggingFaceLocalTutor(model_id=args.model_id) if args.model else None
    session = NoggimigoSession(args.lesson, model=model)

    voice = None
    if args.speak:
        try:
            voice = KokoroLocalVoice(
                VoiceSettings(
                    model_path=args.tts_model_path,
                    voices_path=args.tts_voices_path,
                    voice_id=args.tts_voice,
                    speed=args.speech_speed,
                )
            )
        except ValueError as exc:
            print(f"[speech disabled: {exc}]")
        else:
            print(f"Speech enabled (Kokoro voice: {args.tts_voice}).")

    def say(message: str) -> None:
        nonlocal voice
        if voice is None:
            return
        try:
            voice.speak(message)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            print(f"[speech unavailable; continuing with text: {exc}]")
            voice = None

    mode = f"local model: {args.model_id}" if model else "deterministic mode"
    print(f"Noggimigo tutor ({mode}). Type 'hint', 'reset', or 'exit'.")
    say("Hello! I'm Noggimigo. Let's work through this together.")

    while not session.complete:
        prompt = session.current_prompt()
        question = f"[{prompt['progress']}] {prompt['question']}"
        print(f"\n{question}")
        say(prompt["question"])
        answer = input("> ").strip()

        if answer.lower() == "exit":
            break
        if answer.lower() == "reset":
            session.reset()
            say("Let's start again.")
            continue

        result = (
            session.request_hint()
            if answer.lower() in {"hint", "help", "?"}
            else session.submit(answer)
        )

        message = result.get("model_message") or result["feedback"]
        print(message)
        say(message)

    if session.complete:
        message = "Lesson complete. Nice work!"
        print(f"\n{message}")
        say(message)


if __name__ == "__main__":
    main()
