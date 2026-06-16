from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import statistics
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.shots import Alcohol


@dataclass
class TurnRecord:
    """Once recorded player turn."""
    round_number: int
    glass_position: int  # 0, 1, or 2
    decision_ms: int  # time taken to pick
    alcohol_chosen: Alcohol
    was_hidden: bool
    cards_played: list[str]  # card IDs used this turn


class PatternTracker:
    """
    Tracks player behavior patterns within a run.
    Nina reads this to inform pick decisions and tell generation.

    Cleared every new run.
    """
    HISTORY_SIZE = 10

    def __init__(self):
        self._history: deque[TurnRecord] = deque(maxlen=self.HISTORY_SIZE)
        self._position_count = {0: 0, 1: 0, 2: 0}
        self._total_turns = 0
        self._trick_cards_used = 0
        self._consecutive_low = 0  # current streak of low-ABV picks
        self._max_low_streak = 0

    # --- Recording ---

    def record_turn(self, record: TurnRecord) -> None:
        self._history.append(record)
        self._position_count[record.glass_position] = (
                self._position_count.get(record.glass_position, 0) + 1
        )
        self._total_turns += 1

        # Trick card tracking
        trick_ids = {"palmed_switch", "cup_shuffle", "doctored_glass",
                     "sleight_of_hand", "fake_out", "blame_bartender"}
        for card in record.cards_played:
            if card in trick_ids:
                self._trick_cards_used += 1

        if record.alcohol_chosen.abv < 20:
            self._consecutive_low += 1
            self._max_low_streak = max(self._max_low_streak, self._consecutive_low)
        else:
            self._consecutive_low = 0

        ...
