# Noggimigo

Noggimigo is an open-source local tutoring runtime. Its deterministic lesson engine owns answer verification and lesson progression. An optional local Hugging Face model can suggest concise Socratic language, but model output is validated and cannot mark an answer correct or advance a lesson.

## Implemented runtime

The package now provides a reusable `NoggimigoSession`, exact fraction/decimal/text verification, bounded session history, hints, reset, progress indicators, configurable presentation preferences, and a command-line interface. Supported curriculum is intentionally explicit and currently includes `fractions_intro`, `algebra_intro`, and `patterns_sequences`.

The optional adapter defaults to `Qwen/Qwen3-0.6B`, loads lazily, supports mocked inference in tests, validates structured JSON responses, and falls back to deterministic feedback if dependencies, weights, or hardware are unavailable. Ordinary tests do not download model weights.

## Installation and CLI

```bash
git clone https://github.com/Noggin-Labs/noggimigo.git
cd noggimigo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m noggimigo.cli --lesson fractions_intro
```

During a lesson, enter `hint`, `reset`, or `exit` as needed.

## Python API

```python
from noggimigo import NoggimigoSession

session = NoggimigoSession("algebra_intro")
print(session.current_prompt())
print(session.submit("subtract 4"))
```

## Optional local model

The core package has no model dependency. To use local generation, install the optional dependencies manually:

```bash
python -m pip install 'transformers>=4.51.0' 'torch>=2.6.0' 'accelerate>=1.2.0'
```

Weights are downloaded lazily to the local Transformers cache. CPU use is supported where the selected model permits it; GPU can improve speed. No API token is required by this project, and no student PII or hidden telemetry is collected.

## Testing

```bash
python -m pip install pytest
pytest -q
```

Tests cover imports, equivalent fractions, invalid fractions and division by zero, hints, reset, bounded history, incorrect-answer progression protection, mocked structured model generation, and deterministic fallback. Real Qwen inference is not claimed by the unit tests.

## Scientific and accessibility boundaries

NFOT-related research code remains separate from tutoring correctness. Ordinary response time is not relabeled as a biological Write-Back Gap, and this package does not infer attention, fatigue, intelligence, retention, disability, or diagnosis. Presentation preferences are user-controlled scaffolding options rather than diagnostic labels.

The current curriculum is mathematics only and intentionally small. New curriculum should be added as explicit data with deterministic answer checks and tests. The project is MIT licensed.
