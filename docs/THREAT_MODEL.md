# Noggimigo threat model — model layer vs authoritative state

**Scope:** the optional language-model layer (`hf_provider.py`, `pedagogy.py`) and its interaction with the authoritative deterministic components (`answer_verifier.py`, `curriculum.py`, `session.py`).

**Date:** 2026-11-03 · **Basis:** independent adversarial review, `tests/test_adversarial_integrity.py`.

## 1. The trust boundary

```
learner text ──► answer_verifier (AUTHORITATIVE)  ──► correctness verdict
                       │                                    │
                       │                                    ▼
                       │                          session state / progression (AUTHORITATIVE)
                       │                                    │
                       └──► hf_provider ──► model ──► parse_model_output (structural)
                                                        │
                                                        ▼
                                            pedagogy.validate_suggestion (consistency)
                                                        │
                                                        ▼
                                          student_facing_message (ADVISORY text only)
```

The model contributes **text**. It does not contribute a verdict. `session.submit` computes correctness and progression *before* the model is called, and the model's output can only add `model_message` / `pedagogical_action` keys to the returned dictionary. There is no code path from model output to `index += 1`.

## 2. Threats and controls

| ID | Threat | Control | Residual risk |
|---|---|---|---|
| T1 | Instructions inside a learner answer make a wrong answer "correct" | `verify_answer` parses a narrow numeric/fraction grammar; injected prose cannot parse as the expected value | Low. Prose answers return `AMBIGUOUS`, never `CORRECT`. |
| T2 | Injected text advances the lesson | Progression is computed only from the verifier's `CORRECT` status | Low |
| T3 | Model asserts the answer is correct when it is not | `_CORRECT_CLAIMS` detector; rejection → deterministic feedback | **Medium.** Lexical detector. Phrasings outside the pattern set bypass it (see §4). |
| T4 | Model claims progression/completion/mastery | `_PROGRESSION_CLAIMS`, `_COMPLETION_CLAIMS`, `_MASTERY_CLAIMS`, gated on verified flags | **Medium.** Same lexical limitation. |
| T5 | Model reveals the expected answer | `_leaks_expected_answer` checks numeric forms, decimals, common fraction words, and spoken digits | **Medium.** Open-ended paraphrases ("the number in the denominator") are undetectable. |
| T6 | Malformed model output corrupts state | `parse_model_output` requires exactly four keys and exact types; failures raise `ModelOutputError`; `session.submit` catches and falls back | Low |
| T7 | Provider failure or timeout crashes the session | `except Exception` around `generate`, sets `model_fallback` | Low. The exception text is never copied into the result. |
| T8 | Model output mutates the returned dictionary | `validate_suggestion` returns `dict(suggestion)` (a copy) | Low |
| T9 | Learner PII leaks into the prompt | `build_messages` sends only subject, level, lesson context, deterministic feedback, prompt, learner response; no identifiers | Low. Free-text answers can contain PII the learner typed; see T10. |
| T10 | Answer retention beyond need | `history` keeps raw answers **in memory**, bounded by `history_limit`, cleared on `reset`. No logging, no disk write in this module. | **Medium by design.** Any UI that persists `history` inherits the retention obligation. |
| T11 | Specialist exception leaks paths/DB content | `DomainRegistry.analyse` catches and returns a generic message | Low |
| T12 | Chess subsystem broken/untested | `noggimigo.chess` is now in the package and its 8 tests execute | Resolved this sprint |

## 3. What the controls cannot do

- They do not verify that the model's message is *mathematically true*. A confidently wrong explanation that avoids the claim-detector vocabulary passes.
- They do not verify that a misconception candidate is correct. `misconception_candidates` is bounded in count, type and length only.
- They do not detect prompt injection in the academic sense; they only prevent injection from changing authoritative state.
- They do not sandbox the model. A model that writes to the filesystem through another code path is out of scope here.

## 4. Known gaps (not fixed, deliberately recorded)

These were found by the adversarial suite. They are **undefended** and should not be described as secure:

1. **Vocabulary escape.** A confirmation phrased outside the detector's alternatives (for example a bare "Yep!", "Nice!", or a phrase in another language) is not recognised as a correctness claim. The detector was widened this sprint to cover "That's right", "Spot on", "You've mastered", "Let's move on", but widening a lexical list is not a solution to paraphrase.
2. **Semantic answer leak.** "Think about how many equal pieces the whole is cut into" can communicate the denominator without naming it. No token-level check catches this.
3. **Misconception candidates are unchecked for content.** Bounded in shape only.
4. **Stale-response attribution.** A message generated for step 1 can be displayed while step 2 is active; the application does not bind a message to the state that produced it.

## 5. Severity summary

The design is sound: the model is advisory and cannot alter verdicts or progression. The residual risk is concentrated in **natural-language claim detection (T3/T4/T5)**, which is heuristic and will always be incomplete. Mitigation that does not depend on lexicons — for example, restricting the model to a fixed template vocabulary, or requiring the application to render the correctness verdict itself rather than the model — is the recommended next step.
