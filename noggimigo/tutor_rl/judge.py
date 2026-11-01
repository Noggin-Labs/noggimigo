"""Deterministic reward calculation for Noggimigo's chess tutor RL pipeline.

The judge validates moves and combines engine-derived move quality with
optional style and board-perception scores.

It does not run a chess engine or a language model. Those components must
supply their own scores.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import chess


@dataclass(frozen=True, slots=True)
class JudgeConfig:
    """Reward parameters matching configs/tutor_rl/*.yaml."""

    mate_clip_cp: int = 1500
    scale_cp: float = 500.0
    illegal_reward: float = -1.0

    def __post_init__(self) -> None:
        if self.mate_clip_cp <= 0:
            raise ValueError("mate_clip_cp must be positive.")
        if not math.isfinite(self.scale_cp) or self.scale_cp <= 0:
            raise ValueError("scale_cp must be finite and positive.")
        if not math.isfinite(self.illegal_reward):
            raise ValueError("illegal_reward must be finite.")


@dataclass(frozen=True, slots=True)
class JudgeResult:
    """Auditable result of one reward evaluation."""

    reward: float
    legal: bool
    move_uci: str
    centipawn_loss: float | None
    move_quality: float
    style_score: float | None
    perception_score: float | None
    reason: str


def _validate_gate_score(name: str, score: float | None) -> None:
    if score is None:
        return
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")


class ChessTutorJudge:
    """Score chess-tutor actions using deterministic, inspectable rules.

    The move-quality term uses:

        exp(-min(centipawn_loss, mate_clip_cp) / scale_cp)

    A zero centipawn loss receives a quality score of 1.0. Larger losses
    receive progressively smaller scores.

    Optional style and perception scores act as multiplicative gates.
    Omitting either score leaves that gate neutral (1.0).
    """

    def __init__(self, config: JudgeConfig | None = None) -> None:
        self.config = config or JudgeConfig()

    def evaluate(
        self,
        *,
        fen: str,
        move_uci: str,
        centipawn_loss: float | None,
        style_score: float | None = None,
        perception_score: float | None = None,
    ) -> JudgeResult:
        """Evaluate a proposed move and return its reward.

        Args:
            fen: Position before the proposed move.
            move_uci: Proposed move in UCI notation.
            centipawn_loss: Non-negative engine-derived loss for the move.
                The engine's score perspective and comparison method must
                be consistent across the dataset.
            style_score: Optional style-gate score in [0, 1].
            perception_score: Optional board-perception score in [0, 1].

        Illegal moves receive illegal_reward without applying the gates.
        Invalid inputs raise ValueError rather than silently receiving a
        reward.
        """
        _validate_gate_score("style_score", style_score)
        _validate_gate_score("perception_score", perception_score)

        if centipawn_loss is not None:
            if not math.isfinite(centipawn_loss) or centipawn_loss < 0:
                raise ValueError(
                    "centipawn_loss must be finite and non-negative."
                )

        try:
            board = chess.Board(fen)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid FEN position.") from exc

        if not board.is_valid():
            raise ValueError("FEN describes an invalid chess position.")

        try:
            move = chess.Move.from_uci(move_uci)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid UCI move: {move_uci!r}") from exc

        if board.is_game_over():
            raise ValueError("Cannot judge a move after the game has ended.")

        if move not in board.legal_moves:
            return JudgeResult(
                reward=self.config.illegal_reward,
                legal=False,
                move_uci=move_uci,
                centipawn_loss=centipawn_loss,
                move_quality=0.0,
                style_score=style_score,
                perception_score=perception_score,
                reason="illegal_move",
            )

        if centipawn_loss is None:
            raise ValueError(
                "centipawn_loss is required for a legal move."
            )

        clipped_loss = min(
            centipawn_loss,
            float(self.config.mate_clip_cp),
        )
        move_quality = math.exp(
            -clipped_loss / self.config.scale_cp
        )

        style_gate = 1.0 if style_score is None else style_score
        perception_gate = (
            1.0 if perception_score is None else perception_score
        )

        reward = move_quality * style_gate * perception_gate

        return JudgeResult(
            reward=reward,
            legal=True,
            move_uci=move_uci,
            centipawn_loss=centipawn_loss,
            move_quality=move_quality,
            style_score=style_score,
            perception_score=perception_score,
            reason="scored",
        )


def judge_move(
    *,
    fen: str,
    move_uci: str,
    centipawn_loss: float | None,
    style_score: float | None = None,
    perception_score: float | None = None,
    config: JudgeConfig | None = None,
) -> JudgeResult:
    """Convenience function for one-off reward evaluation."""
    return ChessTutorJudge(config).evaluate(
        fen=fen,
        move_uci=move_uci,
        centipawn_loss=centipawn_loss,
        style_score=style_score,
        perception_score=perception_score,
    )
