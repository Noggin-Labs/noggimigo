"""Backwards-compatible shim.

The deterministic chess board now lives in the installable package at
``noggimigo.chess``. It previously lived here, under ``data/``, which
``pyproject.toml``'s ``packages.find`` does not ship and which
``tests/test_chess_board.py`` did not import. This module is kept so any external
import of ``data.chess.board`` keeps working, but new code should import
``noggimigo.chess``.
"""

from noggimigo.chess import (
    ChessBoard,
    GameFinishedError,
    IllegalMoveError,
    MoveResult,
)

__all__ = ["ChessBoard", "GameFinishedError", "IllegalMoveError", "MoveResult"]
