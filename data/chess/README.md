# Noggimigo Chess Tutor

A chess-learning module for **Noggimigo**, designed to teach chess through guided reasoning rather than simply providing the best move.

## Overview

Noggimigo Chess Tutor aims to help learners understand chess positions, evaluate decisions, recognize tactical patterns, and develop strategic thinking through Socratic dialogue.

Instead of immediately revealing solutions, the tutor encourages learners to reason about the consequences of their moves.

## Design Principles

- **Reasoning before answers:** Encourage learners to discover ideas independently.
- **Legality first:** Chess rules and move validation must be handled by deterministic chess software.
- **Evidence-based explanations:** Distinguish verified chess facts from engine evaluations and instructional interpretations.
- **One question at a time:** Keep tutoring interactions focused and manageable.
- **No unsupported assumptions:** Never infer a learner's intelligence, disability, attention, or emotional state from their chess performance.

## Planned Capabilities

| Capability            | Description                                             |
| --------------------- | ------------------------------------------------------- |
| Board understanding   | Interpret chess positions and board coordinates         |
| Legal move validation | Verify moves against official chess rules               |
| Guided lessons        | Teach chess concepts through structured lessons         |
| Tactical recognition  | Introduce forks, pins, skewers, and discovered attacks  |
| Strategic reasoning   | Explore development, king safety, and centre control    |
| Game analysis         | Explain candidate moves and positional consequences     |
| Progress tracking     | Record lesson completion and demonstrated understanding |

## Proposed Architecture

The module is intended to integrate with Noggimigo's existing tutoring pipeline.

- **Chess rules:** `python-chess`
- **Board representation:** FEN
- **Move notation:** Standard Algebraic Notation (SAN)
- **Engine analysis:** Stockfish (planned)
- **Teaching dialogue:** Noggimigo's language-model provider
- **Validation:** Deterministic checks independent of generated dialogue

The language model must not be treated as the authority on legal moves or chess outcomes.

## Learning Curriculum

1. Chessboard coordinates and orientation
2. Piece movement and captures
3. Check, checkmate, and stalemate
4. Material values and exchanges
5. Opening principles
6. Tactical patterns
7. King safety and positional play
8. Basic endgames
9. Game analysis and reflection

## Output and Verification

Teaching responses should distinguish between:

- **Verified facts:** Legal moves, checks, captures, and game outcomes.
- **Engine evaluations:** Suggested moves and computer-generated assessments.
- **Pedagogical interpretations:** Explanations intended to help the learner understand a position.

Engine evaluations are not automatically proof that a particular explanation is correct.

## Development Status

**Planned module — implementation and validation pending.**

This README describes the intended design, not a claim that all listed capabilities are currently implemented.

## Dependencies

Planned core dependency:

```bash
pip install python-chess
```

Stockfish integration will require a separately available Stockfish engine.

## Integration

The intended interface is an optional chess-learning module within Noggimigo, separate from its general-purpose tutoring functionality.
