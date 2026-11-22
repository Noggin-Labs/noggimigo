"""Noggimigo's learner-facing voice identity and optional local speech output."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

VOICE_PERSONA = {
    "name": "Migo",
    "personality": ("curious", "thoughtful", "warm", "lightly playful"),
    "teaching_style": (
        "patient and Socratic",
        "one clear question at a time",
        "concise explanations",
        "gentle encouragement without constant praise",
    ),
    "accessibility": (
        "use natural conversational English",
        "prefer short, speakable sentences",
        "explain symbols and abbreviations in words when useful",
        "never talk down to the learner",
    ),
}


@dataclass(frozen=True)
class VoiceSettings:
    """Local Kokoro voice configuration; model assets are supplied by the user."""

    model_path: str = "models/tts/kokoro-v1.0.onnx"
    voices_path: str = "models/tts/voices-v1.0.bin"
    voice_id: str = "af_sarah"
    language: str = "en-us"
    speed: float = 0.95

    def __post_init__(self) -> None:
        if not self.model_path or not self.voices_path:
            raise ValueError("TTS model and voice-pack paths must be non-empty.")
        if not self.voice_id or not self.language:
            raise ValueError("voice_id and language must be non-empty.")
        if isinstance(self.speed, bool) or not isinstance(self.speed, (int, float)):
            raise ValueError("speed must be a number between 0.5 and 2.0.")
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError("speed must be between 0.5 and 2.0.")


class KokoroLocalVoice:
    """Lazy-loaded offline TTS playback using Kokoro ONNX."""

    def __init__(self, settings: VoiceSettings | None = None) -> None:
        self.settings = settings or VoiceSettings()
        self._engine: Any | None = None
        self._audio: Any | None = None

    def _load(self) -> None:
        if self._engine is not None:
            return

        model_path = Path(self.settings.model_path)
        voices_path = Path(self.settings.voices_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"Kokoro model not found: {model_path}")
        if not voices_path.is_file():
            raise FileNotFoundError(f"Kokoro voice pack not found: {voices_path}")

        try:
            from kokoro_onnx import Kokoro
            import sounddevice
        except ImportError as exc:
            raise RuntimeError(
                'Speech dependencies are missing. Install Noggimigo with: '
                'python -m pip install -e ".[voice]"'
            ) from exc

        self._engine = Kokoro(str(model_path), str(voices_path))
        self._audio = sounddevice

    def speak(self, text: str) -> None:
        """Synthesize and play a short tutor message locally."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Speech text must be a non-empty string.")
        if len(text) > 2000:
            raise ValueError("Speech text must be at most 2000 characters.")

        self._load()
        samples, sample_rate = self._engine.create(
            text.strip(),
            voice=self.settings.voice_id,
            speed=float(self.settings.speed),
            lang=self.settings.language,
        )
        self._audio.play(samples, sample_rate)
        self._audio.wait()
