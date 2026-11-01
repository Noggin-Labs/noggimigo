import math

import pytest

chess = pytest.importorskip("chess")

from noggimigo.tutor_rl import ChessTutorJudge, JudgeConfig, judge_move


def test_best_move_receives_maximum_quality():
    result = judge_move(
        fen=chess.STARTING_FEN,
        move_uci="e2e4",
        centipawn_loss=0,
    )
    assert result.legal
    assert result.move_quality == pytest.approx(1.0)
    assert result.reward == pytest.approx(1.0)


def test_move_quality_decreases_with_centipawn_loss():
    judge = ChessTutorJudge()

    good = judge.evaluate(
        fen=chess.STARTING_FEN,
        move_uci="e2e4",
        centipawn_loss=100,
    )
    worse = judge.evaluate(
        fen=chess.STARTING_FEN,
        move_uci="d2d4",
        centipawn_loss=500,
    )

    assert good.reward > worse.reward


def test_illegal_move_receives_configured_penalty():
    result = judge_move(
        fen=chess.STARTING_FEN,
        move_uci="e2e5",
        centipawn_loss=0,
    )
    assert not result.legal
    assert result.reward == -1.0
    assert result.reason == "illegal_move"


def test_style_and_perception_gates_multiply_quality():
    result = judge_move(
        fen=chess.STARTING_FEN,
        move_uci="e2e4",
        centipawn_loss=0,
        style_score=0.8,
        perception_score=0.5,
    )
    assert result.reward == pytest.approx(0.4)


def test_invalid_gate_score_is_rejected():
    with pytest.raises(ValueError):
        judge_move(
            fen=chess.STARTING_FEN,
            move_uci="e2e4",
            centipawn_loss=0,
            style_score=1.5,
        )


def test_missing_engine_score_is_rejected_for_legal_move():
    with pytest.raises(ValueError):
        judge_move(
            fen=chess.STARTING_FEN,
            move_uci="e2e4",
            centipawn_loss=None,
        )


def test_mate_loss_is_clipped():
    config = JudgeConfig(mate_clip_cp=1500, scale_cp=500)
    result = judge_move(
        fen=chess.STARTING_FEN,
        move_uci="e2e4",
        centipawn_loss=3000,
        config=config,
    )
    assert result.move_quality == pytest.approx(math.exp(-3))


def test_invalid_fen_is_rejected():
    with pytest.raises(ValueError):
        judge_move(
            fen="not a FEN",
            move_uci="e2e4",
            centipawn_loss=0,
        )
