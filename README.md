# Noggimigo 🧠

> **Local Socratic AI Tutoring Engine & Neuroadaptive Scaffolding System for Special Educational Needs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Preprint: Zenodo](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.21872418-blue)](https://doi.org/10.5281/zenodo.21872418)

---

## 📌 Overview

**Noggimigo** is an open-source, local Socratic AI tutoring engine and neuroadaptive scaffolding framework created by **@FolatheDuckofDuckingburg** (Founder & Theoretical Neuroscience Lead at Noggin Labs). 

Unlike conventional conversational models that directly output solutions, Noggimigo acts as an empathetic, step-by-step Socratic coach. It decomposes complex mathematical and logical concepts into micro-steps, diagnoses specific conceptual misconceptions using a structured error taxonomy, and integrates real-time biophysical telemetry derived from **Neural Feedback Optimization Theory (NFOT)**.

Noggimigo is engineered specifically to prevent cognitive fatigue and learning erasure in special education workflows, featuring dedicated accommodation adapters for **ADHD**, **Autism**, and **Dyslexia**.

---

## 🔬 Core Architecture

Noggimigo operates through a modular four-pillar computational pipeline:

```
+-----------------------------------------------------------------------------------+
|                            NoggimigoTutorEngine                                   |
|                                                                                   |
|  +---------------------------+             +-----------------------------------+  |
|  |   SocraticReasoningCore   |             |            NFOTEngine             |  |
|  | - Intent Classifier       |             | - Write-Back Gap (L) Tracking     |  |
|  | - Error Taxonomy Diagnosis|             | - Lorentzian Efficiency E(L)      |  |
|  | - Micro-Step Decomposition|             | - ABETH Synaptic Bias Detection   |  |
|  +-------------+-------------+             +-----------------+-----------------+  |
|                |                                             |                    |
|                +----------------------+----------------------+                    |
|                                       |                                           |
|                                       v                                           |
|                      +----------------------------------+                         |
|                      |    DisabilityScaffoldAdapter     |                         |
|                      | (ADHD / Autism / Dyslexia Rules) |                         |
|                      +----------------------------------+                         |
+-----------------------------------------------------------------------------------+
```

### 1. `SocraticReasoningCore`
- **Semantic Intent Classifier (`NoggimigoIntentAI`):** Utilizes local semantic matching to classify student intent without relying on cloud LLM APIs.
- **Misconception Error Taxonomy:** Dynamically diagnoses procedural and conceptual errors including:
  - `INVERSION_ERROR`: Swapped numerator/denominator or parts of a whole.
  - `HALVING_ERROR` / `HALF_ERROR`: Off-by-one division in remaining equal slices or incorrect half assumptions.
  - `INVERSE_ERROR`: Applied addition instead of subtraction (or vice versa).
  - `ORDER_ERROR`: Out-of-sequence algebraic steps.
  - `MULTIPLY_ERROR` & `DOUBLING_ERROR`: Factor reduction and scale mistakes.
  - `CONCEPTUAL_GAP`: General foundational understanding gaps.
- **Micro-Step Scaffolding:** Breaks multi-step problems (algebra, fractions, pattern recognition) into guided sub-questions.

### 2. `NFOTEngine` (Neuroadaptive Telemetry)
- **Write-Back Gap ($L$):** Measures real-time interaction latency ($L = t_{\text{feedback}} - t_0$).
- **Lorentzian Efficiency Law:** Calculates biological efficacy $E(L) = \frac{c}{L^2 + c}$.
- **ABETH Bias Classification:** Applies the *Asymmetric Biological Eligibility Trace Hypothesis* to detect whether feedback timing favors potentiation (`POTENTIATION_FAVORED`) or risks synaptic fatigue/depressive drift (`DEPRESSIVE_BIAS`).
- **EEG Spectral Analysis:** Monitors Theta-to-Beta Ratio (TBR) and Alpha/Beta spectral power to detect `ATTENTION_DECAY` ($TBR > 2.0$) and trigger automated micro-prompt adjustments before cognitive overload occurs.

### 3. `DisabilityScaffoldAdapter`
- **ADHD Profile:** Enforces 1-step micro-chunks, disables stressful countdown timers, increases visual encouragement frequency, and boosts reward feedback.
- **Autism Profile:** Provides predictable visual layouts, literal and non-ambiguous phrasing, and explicit step-by-step guidance.
- **Dyslexia Profile:** Formats prompts with wide font spacing, simplified reading grade levels, and native text-to-speech (TTS) accessibility hooks.

### 4. `LessonGenerator` & `NogginLessonBuilder`
- Procedurally generates math, algebra, and sequence lessons with dynamic parameterization.
- Includes a robust fallback mechanism to ensure uninterrupted learning if procedural generation or local AI models encounter latency timeouts.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Standard library dependencies (`json`, `re`, `math`, `time`, `os`, `sys`)

### Installation

```bash
# Clone the repository
git clone https://github.com/Noggin-Labs/noggimigo.git

# Navigate into the repository directory
cd noggimigo

# Run the local interactive CLI tutor
python -m noggimigo.Noggimigo
```

---

## 💻 Code Example

```python
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

print("Efficiency:", response["nfot_telemetry"]["efficiency"])
# Output: 0.55
```

---

## 📊 Telemetry Output Schema

Every interaction returns a structured payload containing both pedagogical and biophysical metrics:

```json
{
  "concept": "algebra_intro",
  "node": "step_1",
  "status": "MISCONCEPTION",
  "error_type": "INVERSE_ERROR",
  "feedback": "🔍 Let me guide you: Adding 4 to both sides gives 2x + 8 = 14...",
  "completed": false,
  "nfot_telemetry": {
    "write_back_gap_ms": 35.0,
    "efficiency": 0.55,
    "abeth_bias": "POTENTIATION_FAVORED",
    "tbr": 1.15,
    "cognitive_state": "HIGH_FOCUS",
    "learning_prediction": {
      "predicted_retention_score": 0.678,
      "readiness_zone": "OPTIMAL_MASTERY_ZONE",
      "recommendation": "Pace standard or accelerated learning steps."
    }
  }
}
```

---

## 📄 Preprints & Theoretical References

1. Kassim, F. A. (2026). *Neural Feedback Optimization Theory*. Zenodo. [DOI: 10.5281/zenodo.21872418](https://doi.org/10.5281/zenodo.21872418)
2. Kassim, F. A. (2026). *The Memory Machine*. Zenodo. [DOI: 10.5281/zenodo.22160425](https://doi.org/10.5281/zenodo.22160425)

---

## 📜 License

This project is open-source software licensed under the **MIT License**.
