# Noggimigo architecture: authoritative vs advisory components

**Audited commit:** `bc0cfd9` (+ this sprint's uncommitted changes).
**Verification:** `pytest -q` → **145 passed** in 0.29 s (Python 3.12.3).

## 1. Component authority

| Component | Role | Authority | Evidence |
|---|---|---|---|
| `answer_verifier.py` | Parses a learner answer and decides equality with the expected answer | **AUTHORITATIVE** | `session.submit` branches only on `check.status` |
| `curriculum.py` | Static lesson graph: question, expected answer, hint, misconception map | **AUTHORITATIVE** | Index into `CURRICULUM[lesson_id]["nodes"]` |
| `session.py` | Owns `index`, `history`, mastery; applies progression | **AUTHORITATIVE** | `index += 1` only inside the `is_correct` branch |
| `mastery.py` | BKT/MIRT estimates from observed correctness | Derived (authoritative for reporting only) | `observe(..., correct=is_correct)` |
| `specialists.py` | Domain analysis; abstains on insufficient evidence | Advisory | `DomainRegistry.analyse` returns a `SpecialistResult` |
| `pedagogy.py` | Validates a model suggestion against deterministic state | **ENFORCEMENT** | Raises `PedagogicalValidationError` |
| `hf_provider.py` | Builds prompts, parses model JSON | Advisory + structural validation | `parse_model_output` |
| `reasoning_evidence.py` | Records evidence with enforced provenance | Advisory (new this sprint) | Invariants in the module |
| `intent.py` | TF-IDF intent labelling of learner text | Advisory | Not consulted for correctness |
| `chess/` | Deterministic board wrapper around python-chess | Authoritative within chess lessons | New location this sprint |

## 2. Submit path (authoritative first, model last)

```
submit(answer)
 ├─ if complete: return {status: COMPLETE}                       (no model call)
 ├─ node = lesson.nodes[index]
 ├─ check = verify_answer(answer, node.answer)          ← AUTHORITATIVE verdict
 ├─ mastery.observe(node.components, correct=is_correct)
 ├─ if CORRECT: index += 1                                       ← AUTHORITATIVE progression
 │   else: feedback = node.misconceptions.get(normalised answer, generic)
 ├─ record history event (raw answer retained, bounded)
 └─ if model is not None:                                        ← ADVISORY only
      try: suggestion = model.generate(...)
      except Exception: result["model_fallback"] = True          (no exception text kept)
      else: validate_suggestion(...)                             ← may reject
            on reject: model_fallback = True
            on accept: result["model_message"], ["pedagogical_action"] = ...
```

Two properties follow directly and are tested:

- The model is invoked **after** progression. Even a perfect adversarial model output cannot change `index` on this call.
- Every model failure mode (exception, malformed JSON, invalid action, claim violation, answer leak) degrades to the same deterministic feedback the application already computed.

## 3. Defects found in this audit

| ID | Defect | Impact | Status |
|---|---|---|---|
| A1 | `tests/test_chess_board.py` imported `noggimigo.chess`, which did not exist; the implementation was at `data/chess/board.py`, which `packages.find` does not ship | 8 chess tests never ran; the chess feature was not installable | **Fixed** — implementation moved to `noggimigo/chess/`, old path is a shim |
| A2 | `ChessBoard()` passed `fen=None` to `chess.Board`, which yields an *empty* board with zero pieces, so `is_valid()` failed | Every no-argument `ChessBoard()` raised `ValueError: Invalid chess position.` | **Fixed** — uses `chess.Board()` when `fen is None` |
| A3 | Correctness/progression/mastery claim detectors missed common phrasings ("That's right!", "You've mastered this!", "Let's move on") | Model could assert unverified correctness | **Fixed** — patterns widened; covered by tests A3–A5 |
| A4 | Answer-leak check knew only "1/4"/"0.25", not "one quarter" | Model could speak the answer | **Fixed** — fraction-word map and spoken-digit variant |
| A5 | `expected_numeric` parameter accepted and silently ignored (found in phase 1) | Dead API surface | Open — low severity |
| A6 | History retains raw learner answers in memory | Retention obligation for any UI that persists it | **Documented**, not changed (behaviour may be intended) |

## 4. Limitations of this review

- The audit is static plus test-based. No dynamic taint analysis, fuzzing at scale, or sandbox escape testing was performed.
- `intent.py` and `mastery.py` were inspected for authority but not adversarially fuzzed.
- Passing 145 tests demonstrates the absence of the specific failures tested; it is not evidence of comprehensive security.
- No real model was run. Every model interaction in the suite is a stub, so tokeniser/provider behaviour is exercised only at the structural level.
