
import pytest

pytest.importorskip("chess")

from noggimigo.chess import (
    ChessBoard,
    GameFinishedError,
    IllegalMoveError,
)


def test_starting_position_has_20_legal_moves():
    board = ChessBoard.starting_position()
    assert len(board.legal_moves) == 20


def test_legal_move_updates_position():
    board = ChessBoard()
    result = board.play("e2e4")

    assert result.uci == "e2e4"
    assert result.san == "e4"
    assert result.turn == "black"


def test_illegal_move_is_rejected():
    board = ChessBoard()

    with pytest.raises(IllegalMoveError):
        board.play("e2e5")


def test_fen_round_trip():
    original = ChessBoard()
    original.play("e2e4")

    restored = ChessBoard.from_fen(original.fen)

    assert restored.fen == original.fen
    assert restored.legal_moves == original.legal_moves


def test_undo_restores_position():
    board = ChessBoard()
    initial_fen = board.fen

    board.play("e2e4")
    undone = board.undo()

    assert undone == "e2e4"
    assert board.fen == initial_fen


def test_fools_mate_detects_checkmate():
    board = ChessBoard()

    for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
        result = board.play(move)

    assert result.is_check
    assert result.is_checkmate
    assert board.is_game_over


def test_moves_are_rejected_after_game_ends():
    board = ChessBoard()

    for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
        board.play(move)

    with pytest.raises(GameFinishedError):
        board.play("e2e4")


def test_invalid_fen_is_rejected():
    with pytest.raises(ValueError):
        ChessBoard.from_fen("not a valid FEN")
