"""Deterministic chess board operations for Noggimigo.

This module lives inside the installed package (``noggimigo.chess``) so that it is
shipped by ``pyproject.toml``'s ``packages.find`` and importable by tests and
users. It was previously implemented under ``data/chess/board.py``, which is not
part of the package, so ``from noggimigo.chess import ...`` failed and the eight
chess tests never executed.
"""

from __future__ import annotations

from dataclasses import dataclass

import chess


class IllegalMoveError(ValueError):
    """Raised when a requested move is not legal."""


class GameFinishedError(RuntimeError):
    """Raised when a move is attempted after the game ends."""


@dataclass(frozen=True)
class MoveResult:
    uci: str
    san: str
    fen: str
    turn: str
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool


class ChessBoard:
    """A small, deterministic wrapper around python-chess.

    Board legality is delegated to python-chess; this class adds no rules of its
    own and therefore claims no chess correctness beyond that library.
    """

    def __init__(self, fen: str | None = None):
        # ``chess.Board(None)`` does NOT mean the starting position: it produces an
        # empty 8/8 board with zero pieces, which fails ``is_valid()``. Passing None
        # through made ``ChessBoard()`` raise for every caller. Use the library's own
        # default instead.
        try:
            self._board = chess.Board() if fen is None else chess.Board(fen)
        except ValueError as exc:
            raise ValueError("Invalid chess position.") from exc

        if not self._board.is_valid():
            raise ValueError("Invalid chess position.")

    @classmethod
    def starting_position(cls) -> "ChessBoard":
        return cls()

    @classmethod
    def from_fen(cls, fen: str) -> "ChessBoard":
        return cls(fen)

    @property
    def fen(self) -> str:
        return self._board.fen()

    @property
    def turn(self) -> str:
        return "white" if self._board.turn else "black"

    @property
    def legal_moves(self) -> tuple[str, ...]:
        return tuple(move.uci() for move in self._board.legal_moves)

    @property
    def is_check(self) -> bool:
        return self._board.is_check()

    @property
    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def play(self, uci: str) -> MoveResult:
        if self.is_game_over:
            raise GameFinishedError("The game has ended.")

        try:
            move = chess.Move.from_uci(uci)
        except ValueError as exc:
            raise IllegalMoveError(f"Invalid UCI move: {uci}") from exc

        if move not in self._board.legal_moves:
            raise IllegalMoveError(f"Illegal move: {uci}")

        san = self._board.san(move)
        self._board.push(move)

        return MoveResult(
            uci=uci,
            san=san,
            fen=self.fen,
            turn=self.turn,
            is_check=self._board.is_check(),
            is_checkmate=self._board.is_checkmate(),
            is_stalemate=self._board.is_stalemate(),
        )

    def undo(self) -> str:
        if not self._board.move_stack:
            raise ValueError("There are no moves to undo.")

        return self._board.pop().uci()

    def copy(self) -> "ChessBoard":
        return ChessBoard(self.fen)
