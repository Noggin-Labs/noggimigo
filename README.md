# Noggimigo 🧠

> **Local Socratic AI Tutoring Engine with Latency Tracking for Special Educational Needs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

---

## 📌 Overview

**Noggimigo** is an open-source, local Socratic AI tutoring engine created by Folarera Kassim for [Noggin Labs](https://github.com/Noggin-Labs).

Unlike conventional conversational models that directly output solutions, Noggimigo acts as a step-by-step Socratic coach. It decomposes mathematical and logical concepts into micro-steps, diagnoses specific conceptual misconceptions using a structured error taxonomy, and tracks interaction latency at the trial level.

Noggimigo is designed for special education workflows, with accommodation adapters for **ADHD**, **Autism**, and **Dyslexia**.

---

## 🔬 Core Architecture

Noggimigo operates through a modular pipeline:

### 1. `SocraticReasoningCore`

- **Semantic Intent Classifier:** Classifies student intent using local semantic matching, without relying on cloud LLM APIs.
- **Misconception Error Taxonomy:** Diagnoses procedural and conceptual errors including:
  - `INVERSION_ERROR`: Swapped numerator/denominator or parts of a whole.
  - `HALVING_ERROR` / `HALF_ERROR`: Off-by-one division in remaining equal slices, or incorrect half assumptions.
  - `INVERSE_ERROR`: Applied addition instead of subtraction (or vice versa).
  - `ORDER_ERROR`: Out-of-sequence algebraic steps.
  - `MULTIPLY_ERROR` & `DOUBLING_ERROR`: Factor reduction and scale mistakes.
  - `CONCEPTUAL_GAP`: General foundational understanding gaps.
- **Micro-Step Scaffolding:** Breaks multi-step problems (algebra, fractions, pattern recognition) into guided sub-questions.

### 2. `LatencyTracker`

- **Write-Back Gap ($L$):** Measures the real-time interval between a prompt and the student's response ($L = t_{\text{response}} - t_{\text{prompt}}$).
- **Distributional Logging:** Records the full distribution of $L$, not just the mean, so that variance and tail behavior can be examined.
- **Note:** The relationship between $L$ and learning outcomes is a hypothesis under investigation in [NFOT](https://github.com/Noggin-Labs/NFOT). It is not an established mechanism.

### 3. `DisabilityScaffoldAdapter`

- **ADHD Profile:** 1-step micro-chunks, no countdown timers, more frequent encouragement.
- **Autism Profile:** Predictable layouts, literal phrasing, explicit step-by-step guidance.
- **Dyslexia Profile:** Wide font spacing, simplified reading levels, native TTS accessibility hooks.

### 4. `LessonGenerator` & `NogginLessonBuilder`

- Procedurally generates math, algebra, and sequence lessons with dynamic parameterization.
- Includes a robust fallback mechanism to ensure uninterrupted learning if procedural generation or local AI models encounter latency timeouts.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Standard library dependencies (`json`, `re`, `math`, `time`, `os`, `sys`)

### Installation

```
# Clone the repository
git clone https://github.com/Noggin-Labs/noggimigo.git

# Navigate into the repository directory
cd noggimigo

# Run the local interactive CLI tutor
python -m noggimigo.Noggimigo
```
## 💻 Code Example
```
from noggimigo import NoggimigoTutorEngine

# Initialize tutor for basic algebra
tutor = NoggimigoTutorEngine(active_concept="algebra_intro")

# Get current prompt
print("Noggimigo:", tutor.get_current_prompt())
# Output: Solve for x: 2x + 4 = 10. What is the first operation to isolate 2x?

# Evaluate student input with simulated latency (e.g. 35 ms)
response = tutor.evaluate_response(user_input="add 4", latency_ms=35.0)

print(response["feedback"])
# Output: 🔍 Let me guide you: Adding 4 to both sides gives 2x + 8 = 14, which moves further away! Try subtracting 4.
#         💡 Socratic Guidance (INVERSE_ERROR): Applied addition instead of subtraction (or vice versa).

print("Latency:", response["latency_ms"])
# Output: 35.0
```
## 📊 Telemetry Output Schema
Every interaction returns a structured payload containing pedagogical metrics and latency data:
```
{
  "concept": "algebra_intro",
  "node": "step_1",
  "status": "MISCONCEPTION",
  "error_type": "INVERSE_ERROR",
  "feedback": "🔍 Let me guide you: Adding 4 to both sides gives 2x + 8 = 14...",
  "completed": false,
  "latency_ms": 35.0
}
```
## 📄 Related Work
Noggimigo's Socratic scaffolding approach is informed by the literature on theory-guided tutoring systems. For a survey of AI tutoring paradigms, neural solvers, and student simulation frameworks, see:

- Kassim, F. A. (2026). Your LLM is an Incompetent AI Tutoring System. Zenodo. DOI: 10.5281/zenodo.22975179  
- Yang, K., Wang, C., Galley, M., Singh, C., Inala, J. P., Zhai, C., & Gao, J. (2026). StudentSim: Training LLM-based Student Simulators. arXiv.

## 📜 License
This project is open-source software licensed under the MIT License.
