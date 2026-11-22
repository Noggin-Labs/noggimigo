# Noggimigo Think Engine

## Purpose

The Think engine converts authoritative lesson events into a compact teaching
plan. It is a deterministic decision layer, not a hidden chain-of-thought
transcript and not an answer generator.

## Data flow

1. The session receives a learner response or hint request.
2. The answer verifier classifies answer submissions. The curriculum supplies
   the active question and any authored hint.
3. `build_teaching_plan` selects a teaching goal, strategy, pedagogical action,
   focus, decision basis, and claims to avoid.
4. The session includes that plan in the result and passes it to the optional
   language model as lesson context.
5. The existing pedagogical validator checks any model-proposed message.
   Deterministic feedback remains the fallback.

## Current decision policy

| Event | Strategy | Action |
| --- | --- | --- |
| Verified correct | Brief acknowledgement, then continue | `ACKNOWLEDGE_AND_CONTINUE` |
| Verified incorrect | One-step scaffold, or guided reconsideration | `GIVE_SMALL_HINT` |
| Ambiguous response | Clarify learner intent | `ASK_WHAT_IS_CONFUSING` |
| Invalid response | Request a clearer formulation | `ASK_GUIDING_QUESTION` |
| Explicit hint request | Give the curriculum hint, if available | `GIVE_SMALL_HINT` |

## Guardrails

- The Think engine never verifies an answer or changes curriculum progression.
- A correct answer is not evidence of general mastery.
- Ambiguous input is not silently treated as correct or incorrect.
- Invalid input is not described as a mathematical error.
- The expected answer is not placed in the teaching plan.
- The engine does not infer emotion, disability, intelligence, or attention.
- Plans are decision records, not explanations of private model reasoning.
- Model wording remains untrusted and is subject to the existing validator.

## Example

For an incorrect response in the fractions lesson, the plan records that the
verifier marked the response incorrect and selects the authored one-step hint.
The Speak layer can turn that focus into natural language, but cannot change the
answer status or claim mastery.

## Scope and limitations

The current policy is intentionally small and rule-based. It does not yet
classify open-ended learner questions, diagnose misconceptions semantically,
adapt strategy from longitudinal evidence, or establish that a learner has
mastered a knowledge component. Those require separate evaluation and evidence.
