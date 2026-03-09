"""Gerenciador de desfazer/refazer baseado em snapshots de estado."""

import time
from typing import List, Optional


class UndoManager:
    """Manages undo/redo operations using full state snapshots.

    Each snapshot is a plain dict produced by serializing the entire
    application state (via the existing ``to_dict`` helpers).

    A *merge threshold* prevents rapid-fire saves (e.g. each keystroke
    in an auto-save field) from flooding the stack: snapshots pushed
    within ``merge_threshold`` seconds of the previous one silently
    replace it instead of creating a new entry.
    """

    def __init__(self, max_size: int = 50, merge_threshold: float = 1.0):
        self._snapshots: List[dict] = []
        self._pointer: int = -1
        self._max_size: int = max_size
        self._merge_threshold: float = merge_threshold
        self._last_push_time: float = 0.0

    # -- public API --------------------------------------------------------

    def push(self, state: dict) -> None:
        """Record a new state snapshot.

        * Identical consecutive states are silently ignored.
        * States arriving within *merge_threshold* seconds of the last
          push replace the tip of the stack (debounce).
        * Any pending redo history is discarded.
        """
        # Identical to the current tip – nothing to do
        if self._pointer >= 0 and self._snapshots[self._pointer] == state:
            return

        now = time.time()

        # Truncate any redo history beyond the current pointer
        self._snapshots = self._snapshots[: self._pointer + 1]

        # Merge into the previous snapshot if within the threshold and there
        # is at least one prior state to fall back to on undo.
        if (
            len(self._snapshots) >= 2
            and (now - self._last_push_time) < self._merge_threshold
        ):
            self._snapshots[self._pointer] = state
        else:
            self._snapshots.append(state)
            self._pointer = len(self._snapshots) - 1

        # Enforce maximum history size (drop oldest entries)
        while len(self._snapshots) > self._max_size:
            self._snapshots.pop(0)
            self._pointer -= 1

        self._last_push_time = now

    def undo(self) -> Optional[dict]:
        """Move one step back and return that snapshot, or ``None``."""
        if not self.can_undo():
            return None
        self._pointer -= 1
        return self._snapshots[self._pointer]

    def redo(self) -> Optional[dict]:
        """Move one step forward and return that snapshot, or ``None``."""
        if not self.can_redo():
            return None
        self._pointer += 1
        return self._snapshots[self._pointer]

    def can_undo(self) -> bool:
        return self._pointer > 0

    def can_redo(self) -> bool:
        return self._pointer < len(self._snapshots) - 1

    def clear(self) -> None:
        """Reset the entire history."""
        self._snapshots.clear()
        self._pointer = -1
        self._last_push_time = 0.0
