# Repository layout

This document describes the current GitHub repository layout. It is based on the tracked paths in the repository tree; it is not a proposed or aspirational layout.

```text
noggimigo/
├── .github/
│   ├── FUNDING.yml
│   ├── dependabot.yml
│   └── workflows/
│       ├── codeql.yml
│       └── pages.yml
├── configs/
│   ├── training/
│   │   ├── stage1_chess.yaml
│   │   ├── stage1_l2.yaml
│   │   ├── stage1_math.yaml
│   │   ├── stage2_chess.yaml
│   │   ├── stage2_l2.yaml
│   │   ├── stage2_math.yaml
│   │   └── tutor_sft.yaml
│   └── tutor_rl/
│       ├── prompted_student_reward.yaml
│       └── studentsim_reward.yaml
├── data/
│   ├── chess/
│   ├── l2/raw/
│   └── math/raw/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── THREAT_MODEL.md
│   ├── mastery-study-protocol.md
│   └── REPOSITORY_LAYOUT.md
├── noggimigo/
│   ├── chess/
│   ├── tutor_rl/
│   ├── __init__.py
│   ├── LessonGenerator.py
│   ├── answer_verifier.py
│   ├── cli.py
│   ├── coding_specialist.py
│   ├── curriculum.py
│   ├── evaluation.py
│   ├── hf_provider.py
│   ├── intent.py
│   ├── main.py
│   ├── mastery.py
│   ├── pedagogy.py
│   ├── reasoning_evidence.py
│   ├── session.py
│   └── specialists.py
├── tests/
│   ├── test_adversarial_integrity.py
│   ├── test_chess_board.py
│   ├── test_coding_specialist.py
│   ├── test_hf_provider_guardrails.py
│   ├── test_pedagogy.py
│   ├── test_reasoning_evidence.py
│   ├── test_runtime.py
│   ├── test_session_guardrails.py
│   ├── test_specialists.py
│   └── test_tutor_rl_judge.py
├── .gitignore
├── LICENSE
├── README.md
├── package-lock.json
├── package.json
└── pyproject.toml
```

## What belongs where

- **`noggimigo/`** — importable Python application and library code. Keep runtime modules and Python subpackages here.
- **`tests/`** — automated tests. Mirror the package area or component being tested in test filenames.
- **`docs/`** — architecture, threat model, research protocols, and repository-maintenance documentation.
- **`configs/`** — version-controlled YAML configuration for training and tutor-RL experiments.
- **`data/`** — dataset documentation and small, intentionally tracked data assets. Keep generated datasets, caches, credentials, and learner-identifiable data out of Git.
- **`.github/`** — repository automation and community configuration.

## Important distinction: code repository vs. model checkpoint

This GitHub repository is the Noggimigo application/integration codebase. Its Hugging Face adapter can load the external `Qwen/Qwen3-0.6B` model for local inference. That does **not** mean this repository contains a separately trained Noggimigo checkpoint.

If Noggimigo later publishes trained weights, give those weights a clearly versioned model repository and model card, and document the training data, license, evaluation, and limitations separately from this codebase.

## Maintenance rule

When adding a file, place it in the directory matching its responsibility and update this document if the tracked layout changes. Do not move files solely to make the tree look symmetrical; preserve import paths and update tests/configuration if a genuine package move is necessary.
