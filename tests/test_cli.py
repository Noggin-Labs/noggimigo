from noggimigo import cli


class StaticTutor:
    def __init__(self, model_id):
        self.model_id = model_id

    def generate(self, *args, **kwargs):
        return {
            "student_facing_message": "What do the shaded parts represent?",
            "pedagogical_action": "ASK_GUIDING_QUESTION",
            "misconception_candidates": [],
            "requires_verification": True,
        }


class StaticVoice:
    def __init__(self, settings):
        self.settings = settings
        self.messages = []
        instances.append(self)

    def speak(self, message):
        self.messages.append(message)


instances = []


def test_cli_uses_deterministic_mode_by_default(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "exit")
    cli.main([])
    output = capsys.readouterr().out
    assert "deterministic mode" in output
    assert "local model:" not in output


def test_cli_can_enable_local_model_and_display_validated_message(monkeypatch, capsys):
    monkeypatch.setattr(cli, "HuggingFaceLocalTutor", StaticTutor)
    answers = iter(["wrong", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.main(["--model", "--model-id", "example/local-tutor"])
    output = capsys.readouterr().out
    assert "local model: example/local-tutor" in output
    assert "What do the shaded parts represent?" in output
    assert "Not quite." not in output


def test_cli_can_speak_without_changing_visible_text(monkeypatch, capsys):
    instances.clear()
    monkeypatch.setattr(cli, "KokoroLocalVoice", StaticVoice)
    monkeypatch.setattr("builtins.input", lambda _: "exit")
    cli.main(["--speak", "--tts-voice", "af_sarah", "--speech-speed", "0.9"])
    output = capsys.readouterr().out
    assert "Speech enabled (Kokoro voice: af_sarah)." in output
    assert "Noggimigo tutor" in output
    assert instances
    assert "Hello! I'm Migo." in instances[0].messages


def test_cli_rejects_unknown_lesson(capsys):
    try:
        cli.main(["--lesson", "not-a-lesson"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("argparse should reject an unknown lesson")
