"""Chess tutoring functionality for Noggimigo."""

from .board import (
    ChessBoard,
    GameFinishedError,
    IllegalMoveError,
    MoveResult,
)

__all__ = [
    "ChessBoard",
    "GameFinishedError",
    "IllegalMoveError",
    "MoveResult",
]
