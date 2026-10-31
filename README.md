# Noggimigo

### An open-source, locally runnable Socratic AI tutoring engine.

**Noggimigo** is a Python-based tutoring runtime designed to help learners understand concepts through guided reasoning rather than simply receiving answers.

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
- Bounded interaction history.

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

Noggimigo supports an optional Hugging Face Transformers adapter.

The adapter:

- Loads model weights lazily.
- Supports local inference.
- Requests structured JSON responses.
- Validates generated output.
- Restricts pedagogical actions to an explicit set.
- Falls back to deterministic feedback when generation fails.

The default model is `Qwen/Qwen3-0.6B`.

### Local intent classification

The repository also contains an experimental pure-Python intent classifier.

It combines:

- TF-IDF similarity.
- N-gram overlap.
- Character-level similarity.
- Configurable intent examples.
- Confidence thresholds.

This component is separate from the authoritative answer-verification and lesson-progression engine.

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
| `intent.py` | Experimental intent classification |
| `cli.py` | Command-line interface |
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

Mocked model tests do not constitute validation of real-world tutoring performance or real model inference.

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

```text
noggimigo/
│
├── .github/
│   ├── workflows/
│   └── FUNDING.yml
│
├── configs/
│   ├── training/
│   └── tutor_rl/
│
├── data/
│   ├── chess/
│   ├── l2/
│   └── math/
│
├── noggimigo/
│   ├── __init__.py
│   ├── answer_verifier.py
│   ├── cli.py
│   ├── curriculum.py
│   ├── hf_provider.py
│   ├── intent.py
│   ├── session.py
│   └── LessonGenerator.py
│
├── tests/
│   └── test_runtime.py
│
├── LICENSE
├── README.md
├── SECURITY.md
├── pyproject.toml
└── package-lock.json
```

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

[GitHub Repository](https://github.com/Noggin-Labs/noggimigo) · [Report an Issue](https://github.com/Noggin-Labs/noggimigo/issues)
