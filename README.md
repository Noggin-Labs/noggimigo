# Noggimigo

### An open-source, locally runnable Socratic AI tutoring engine.

**Noggimigo** is a Python-based tutoring runtime designed to help learners understand concepts through guided reasoning rather than simply receiving answers.

The package now provides a reusable `NoggimigoSession`, exact fraction/decimal/text verification, bounded session history, hints, reset, progress indicators, configurable presentation preferences, an auditable event log, and a command-line interface. Each curriculum item declares knowledge components; answer outcomes update an interpretable BKT estimate and a lightweight MIRT-style next-response baseline. Dependency-free Brier score, expected calibration error, and monotonicity metrics are available for held-out evaluation. Supported curriculum is intentionally explicit and currently includes `fractions_intro`, `algebra_intro`, and `patterns_sequences`.
Its central design principle is that an AI tutor should adapt its teaching approach to the learner without surrendering educational correctness to a language model.

Noggimigo combines deterministic lesson progression, mathematical answer verification, misconception-aware feedback, configurable teaching preferences, and an optional locally executed language model.

**The model can suggest how to teach. The deterministic engine decides whether an answer is correct.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange)](https://github.com/Noggin-Labs/noggimigo)

---

## Table of Contents

- [The Problem](#the-problem)
- [Our Approach](#our-approach)
- [Features](#features)
- [Architecture](#architecture)
- [Supported Curriculum](#supported-curriculum)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Python API](#python-api)
- [Optional Local AI Model](#optional-local-ai-model)
- [Optional Local Speech](#optional-local-speech)
- [Testing](#testing)
- [Accessibility and Scientific Integrity](#accessibility-and-scientific-integrity)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## The Problem

Traditional tutoring systems frequently prioritize delivering correct answers over helping learners develop an understanding of the underlying concepts.

This creates several problems:

- Learners can receive answers without understanding the reasoning.
- Incorrect answers may not reveal the misconception behind them.
- A single explanation style may not work equally well for every learner.
- Language models can generate convincing but mathematically incorrect explanations.
- Learning systems may make unsupported assumptions about students.

These problems are particularly important when designing educational technology intended to accommodate different learning needs.

## Our Approach

Noggimigo approaches tutoring as a structured, feedback-driven interaction.

Rather than treating the learner's response as a simple input to an answer generator, it uses a deterministic lesson engine to evaluate responses and control progression.

Its optional language model generates candidate teaching messages, while the application retains authority over correctness and lesson state.

The long-term vision is an educational system that accommodates differences in how learners process information without treating those differences as limitations.

## Features

### Deterministic tutoring engine

- Structured, step-by-step lessons.
- Explicit lesson progression.
- Mathematical answer verification.
- Equivalent fraction and decimal recognition.
- Misconception-specific feedback.
- Hints without automatically advancing lessons.
- Session reset and completion tracking.
- Bounded interaction history. Set `history_limit=0` to disable in-memory event retention for a session.

### Configurable teaching preferences

`TeachingPreferences` currently supports:

| Preference | Purpose |
|---|---|
| `short_messages` | Requests shorter prompts |
| `one_step_at_a_time` | Stores a preference for stepwise instruction |
| `hint_intensity` | Configurable hint preference |
| `show_progress` | Configurable progress display preference |

These are presentation and scaffolding preferences, not disability classifications.

### Optional local AI

Noggimigo supports optional local Hugging Face Transformers and Ollama adapters.

The adapter:

- Loads model weights lazily.
- Supports local inference.
- Requests structured JSON responses.
- Validates generated output.
- Restricts pedagogical actions to an explicit set.
- Falls back to deterministic feedback when generation fails.

The default model is `Qwen/Qwen3-0.6B`.

### Local intent classification

The repository contains a dependency-free, rule-based intent router for answer submissions, questions, hint requests, confusion statements, explanation requests, and uncertain input. It returns inspectable routing evidence and never grades answers or changes lesson progression. The classifier is a baseline, not a calibrated language-understanding model. See docs/INTENT_RECOGNITION.md for its scope and limitations.

---

## Architecture

Noggimigo separates educational correctness from language generation.

```text
                 LEARNER
                    |
                    v
             STUDENT RESPONSE
                    |
                    v
          DETERMINISTIC ENGINE
                    |
          +---------+---------+
          |                   |
          v                   v
     ANSWER CHECKER      CURRICULUM
          |                   |
          +---------+---------+
                    |
                    v
             LESSON STATE
                    |
                    v
           FEEDBACK GENERATION
                    |
             +------+------+
             |             |
             v             v
        DETERMINISTIC   OPTIONAL LOCAL
          FEEDBACK       LANGUAGE MODEL
             |             |
             |        OUTPUT VALIDATION
             |             |
             +------+------+
                    |
                    v
             STUDENT FEEDBACK
```

**Important architectural guarantee:** Model-generated text cannot independently mark an answer correct or advance a lesson.

The deterministic engine remains responsible for those decisions.

### Core components

| Module | Responsibility |
|---|---|
| `session.py` | Session state and lesson progression |
| `answer_verifier.py` | Mathematical parsing and answer verification |
| `curriculum.py` | Explicit lesson definitions |
| `hf_provider.py` | Optional local language-model integration |
| `intent.py` | Deterministic learner-message intent routing |
| `cli.py` | Command-line interface |
| `voice.py` | Voice identity and optional local speech output |
| `LessonGenerator.py` | Additional lesson-generation implementation |

---

## Supported Curriculum

The current built-in mathematics curriculum includes:

| Lesson ID | Subject | Learning objective |
|---|---|---|
| `fractions_intro` | Mathematics | Fractions and equivalent representations |
| `algebra_intro` | Mathematics | Inverse operations and variables |
| `patterns_sequences` | Mathematics | Identifying numerical patterns |

The curriculum is deliberately explicit and relatively small.

New lessons should include defined learning objectives, prompts, expected answers, hints, and misconception feedback where appropriate.

---

## Installation

### Requirements

- Python 3.10 or newer.
- pip.
- Git.

Clone the repository:

```bash
git clone https://github.com/Noggin-Labs/noggimigo.git

cd noggimigo
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

Install Noggimigo:

```bash
python -m pip install -e .
```

---

## Getting Started

Launch the command-line tutor:

```bash
python -m noggimigo.cli --lesson fractions_intro
```

Other available lessons:

```bash
python -m noggimigo.cli --lesson algebra_intro
```

```bash
python -m noggimigo.cli --lesson patterns_sequences
```

During a lesson, learners can request:

- `hint` — receive a hint.
- `reset` — restart the lesson.
- `exit` — leave the session.

---

## Python API

Noggimigo can also be integrated into other Python applications.

```python
from noggimigo import NoggimigoSession

# Initialize a lesson
session = NoggimigoSession("algebra_intro")

# Display the current question
print(session.current_prompt())

# Submit an answer
result = session.submit("subtract 4")

print(result["feedback"])
print(result["status"])
print(result["advanced"])
```

### Configure teaching preferences

```python
from noggimigo import (
    NoggimigoSession,
    TeachingPreferences
)

preferences = TeachingPreferences(
    short_messages=True,
    one_step_at_a_time=True,
    hint_intensity=2,
    show_progress=True
)

session = NoggimigoSession(
    "fractions_intro",
    preferences=preferences
)
```

### Request a hint

```python
hint = session.request_hint()

print(hint["feedback"])
```

### Reset a session

```python
session.reset("algebra_intro")
```

---

## Optional Local AI Model

Noggimigo's deterministic core does not require a language model.

To enable local generation, install the optional dependencies:

```bash
python -m pip install -e ".[hf]"
```

Initialize the adapter:

```python
from noggimigo import NoggimigoSession
from noggimigo.hf_provider import HuggingFaceLocalTutor

tutor = HuggingFaceLocalTutor()

session = NoggimigoSession(
    "algebra_intro",
    model=tutor
)

result = session.submit("subtract 4")

print(result["feedback"])
```

The default model is:

`Qwen/Qwen3-0.6B`

Model weights are downloaded lazily through Hugging Face Transformers and cached locally.

Actual inference performance depends on available hardware and the selected model.

No external inference API is required by this adapter.


### Use a locally installed Ollama model\n\nIf Ollama is installed and its local service is running, no additional Python package is required:\n\n```python\nfrom noggimigo import NoggimigoSession\nfrom noggimigo.ollama_provider import OllamaLocalTutor\n\ntutor = OllamaLocalTutor(model=\"llama3.2:latest\")\nsession = NoggimigoSession(\"fractions_intro\", model=tutor)\nresult = session.submit(\"1/4\")\n\nprint(result[\"feedback\"])\nprint(result.get(\"model_message\", \"Deterministic fallback used.\"))\n```\n\nThe adapter uses Ollama's local `/api/chat` endpoint with non-streaming JSON output and temperature 0. It does not download models or use a hosted inference service. Pull and run a model separately with Ollama before using the adapter. A generated message is shown only if the existing pedagogical validator accepts it; this validator checks structural and state consistency, not full mathematical truth.\n\n### Run the tutor with the optional local model

The default CLI uses deterministic feedback and does not download model weights.
To enable the optional local Hugging Face model:

```bash
python -m pip install -e ".[hf]"
python -m noggimigo.cli --lesson fractions_intro --model
```

Choose a different locally runnable Hugging Face model with `--model-id`:

```bash
python -m noggimigo.cli --lesson algebra_intro --model --model-id Qwen/Qwen3-0.6B
```

The first model-backed run may download weights and requires suitable local hardware.
Noggimigo displays a generated message only after its structural and pedagogical
guardrails accept it. If generation or validation fails, the deterministic feedback
is shown instead. The model does not decide whether an answer is correct or whether
the lesson advances.


## Optional Local Speech

Noggimigo's voice is curious, thoughtful, warm, and lightly playful. It uses
concise conversational English, asks one clear question at a time, and avoids
forced praise or infantilizing language.

Speech is optional and runs locally. The default engine integration uses
[Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx); model assets are not
bundled with this repository.

Install the optional speech dependencies:

```powershell
python -m pip install -e ".[voice]"
```

From the repository root, download the model and voice pack into the expected
directory:

```powershell
New-Item -ItemType Directory -Force models/tts | Out-Null
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx" -OutFile "models/tts/kokoro-v1.0.onnx"
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin" -OutFile "models/tts/voices-v1.0.bin"
```

Then launch Noggimigo with speech:

```powershell
python -m noggimigo.cli --speak
```

Choose a different speaker or adjust the speaking speed:

```powershell
python -m noggimigo.cli --speak --tts-voice af_sarah --speech-speed 0.9
```

The default speaker ID is provisional, not a claim that it is Noggimigo's final
voice. Voice IDs and language compatibility depend on the selected Kokoro pack.
Tutor text remains visible alongside speech. Audio failures do not stop the
lesson, and this integration does not send speech to a hosted service.

Kokoro ONNX's runtime is MIT-licensed and its model weights are Apache-2.0;
review upstream notices and model documentation before redistributing assets.

---

## Testing

Install the development testing dependencies:

```bash
python -m pip install -e ".[test]"
```

Run the test suite:

```bash
pytest -q
```

Tests cover imports, equivalent fractions, invalid fractions and division by zero, hints, reset, bounded history, incorrect-answer progression protection, mocked structured model generation, deterministic fallback, BKT updates, MIRT-style prediction, and mastery event logging. Real Qwen inference is not claimed by the unit tests.
The existing tests cover:

- Public package imports.
- Equivalent fractions and decimals.
- Invalid mathematical answers.
- Division-by-zero rejection.
- Incorrect-answer progression protection.
- Session history limits.
- Hint requests and resets.
- Model failure fallback.
- Mocked structured model generation.

Mocked model tests do not constitute validation of real-world tutoring performance or real model inference. The Ollama adapter tests use a mocked HTTP response; they do not establish that Llama 3.2 follows the tutoring contract reliably.

---

## Accessibility and Scientific Integrity

Noggimigo is being developed with the goal of making educational technology more responsive to different learning needs.

However, accessibility must be implemented responsibly.

The current implementation does not diagnose disabilities, infer intelligence, measure attention, or determine a learner's cognitive state.

In particular:

- Teaching preferences are user-controlled.
- Model-generated explanations are not authoritative.
- Mathematical correctness is independently verified.
- The system does not claim to measure brain activity.
- Ordinary response time is not treated as a biological measurement.

Noggimigo's longer-term research direction includes investigating how feedback timing and adaptive teaching strategies might improve educational interactions.

NFOT-related research remains separate from the tutoring engine's correctness guarantees.

---

## Project Structure

The repository is organized by responsibility:

```text
noggimigo/
├── .github/       # Repository automation and community configuration
├── configs/       # Training and tutor-RL configuration
├── data/          # Intentionally tracked data assets
├── docs/          # Architecture, protocols, and project documentation
├── noggimigo/     # Python application and runtime packages
├── tests/         # Automated test suite
├── README.md
├── pyproject.toml
└── LICENSE
```

For the exact tracked directory and file inventory, see
[`docs/REPOSITORY_LAYOUT.md`](docs/REPOSITORY_LAYOUT.md). That document is the
source of truth for the detailed repository tree and placement guidance.

---

## Roadmap

Noggimigo is an evolving research and software project.

Potential development directions include:

- [ ] Expand the structured mathematics curriculum.
- [ ] Develop more comprehensive misconception taxonomies.
- [ ] Improve adaptive Socratic dialogue.
- [ ] Develop and validate accessibility-oriented teaching adapters.
- [ ] Integrate intent classification more deeply into the tutoring workflow.
- [ ] Expand automated testing and real-model evaluation.
- [ ] Investigate neuroadaptive educational feedback.
- [ ] Explore responsible integration of Neural Feedback Optimization Theory (NFOT).
- [ ] Develop more comprehensive learner-controlled personalization.

These are development goals, not claims about currently completed functionality.

---

## Contributing

Contributions are welcome.

Areas of interest include:

- Python development.
- Educational software.
- Mathematics curriculum development.
- Natural language processing.
- Accessibility engineering.
- Machine learning.
- Computational neuroscience.

When contributing, prioritize correctness, reproducibility, accessibility, and clear documentation.

Please open an issue before proposing substantial architectural changes.

Repository:

https://github.com/Noggin-Labs/noggimigo

Issues:

https://github.com/Noggin-Labs/noggimigo/issues

---

## License

Noggimigo is distributed under the **MIT License**.

See [LICENSE](LICENSE) for the complete license text.

---

## About

**Noggimigo is developed by Noggin-Labs.**

Its guiding idea is simple:

> Learning systems should adapt to learners, rather than expecting every learner to adapt to the system.

We are building toward educational technology that supports different ways of thinking through rigorous engineering, responsible AI, and research-driven development.

**Different ways of thinking. More ways to learn.**

The current curriculum is mathematics only and intentionally small. New curriculum should be added as explicit data with deterministic answer checks and tests. The project is MIT licensed.

The proposed validation plan is documented in [`docs/mastery-study-protocol.md`](docs/mastery-study-protocol.md).

### Research boundary

The mastery module is an online baseline for study instrumentation, not a validated psychometric instrument. Its BKT and MIRT-style estimates must be fit, calibrated, and evaluated on held-out learner responses before being used for consequential decisions. The runtime does not infer attention, fatigue, emotion, disability, intelligence, retention, or biological state from response time or text.
[GitHub Repository](https://github.com/Noggin-Labs/noggimigo) · [Report an Issue](https://github.com/Noggin-Labs/noggimigo/issues)
