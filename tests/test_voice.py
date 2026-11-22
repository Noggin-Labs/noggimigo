from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from noggimigo.voice import VOICE_PERSONA, KokoroLocalVoice, VoiceSettings


def test_voice_persona_has_a_defined_identity():
    assert VOICE_PERSONA["name"] == "Migo"
    assert "curious" in VOICE_PERSONA["personality"]
    assert "patient and Socratic" in VOICE_PERSONA["teaching_style"]


@pytest.mark.parametrize("speed", [0.49, 2.01, True, "fast"])
def test_voice_settings_reject_invalid_speed(speed):
    with pytest.raises(ValueError):
        VoiceSettings(speed=speed)


def test_voice_settings_accept_valid_speed():
    settings = VoiceSettings(speed=0.9)
    assert settings.speed == 0.9
    assert settings.voice_id == "af_sarah"


def test_local_voice_synthesizes_and_plays_audio(tmp_path, monkeypatch):
    model = tmp_path / "model.onnx"
    voices = tmp_path / "voices.bin"
    model.touch()
    voices.touch()
    calls = {}

    class FakeKokoro:
        def __init__(self, model_path, voices_path):
            calls["assets"] = (model_path, voices_path)

        def create(self, text, *, voice, speed, lang):
            calls["synthesis"] = (text, voice, speed, lang)
            return [0.1, 0.2], 24000

    fake_audio = SimpleNamespace(
        play=lambda samples, rate: calls.update(play=(samples, rate)),
        wait=lambda: calls.update(waited=True),
    )
    monkeypatch.setitem(sys.modules, "kokoro_onnx", SimpleNamespace(Kokoro=FakeKokoro))
    monkeypatch.setitem(sys.modules, "sounddevice", fake_audio)

    speaker = KokoroLocalVoice(
        VoiceSettings(
            model_path=str(model),
            voices_path=str(voices),
            voice_id="af_sarah",
            speed=0.9,
        )
    )
    speaker.speak("Let's solve this one step at a time.")

    assert calls["assets"] == (str(model), str(voices))
    assert calls["synthesis"] == (
        "Let's solve this one step at a time.",
        "af_sarah",
        0.9,
        "en-us",
    )
    assert calls["play"] == ([0.1, 0.2], 24000)
    assert calls["waited"] is True


def test_local_voice_rejects_missing_model_before_importing_backend(tmp_path):
    speaker = KokoroLocalVoice(
        VoiceSettings(
            model_path=str(tmp_path / "missing.onnx"),
            voices_path=str(tmp_path / "voices.bin"),
        )
    )
    with pytest.raises(FileNotFoundError, match="Kokoro model not found"):
        speaker.speak("Hello.")
