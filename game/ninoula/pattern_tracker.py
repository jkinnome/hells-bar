from __future__ import annotations

import random
import statistics
from collections import deque
from dataclasses import dataclass
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

    # --- Pattern Queries ---

    @property
    def preferred_position(self) -> int | None:
        """
        Which glass position (0/1/2) the player picks most.
        Returns None if no clear preference (all around within 1 pick of each other).
        """
        if self._total_turns < 3:
            return None
        counts: dict[int, int] = self._position_count
        # noinspection PyTypeChecker
        top = max(counts, key=counts.get)
        second = sorted(counts.values())[-2]
        if counts[top] - second >= 2:  # preference
            return top
        return None

    @property
    def is_decisive(self) -> bool:
        """True if player consistently picks quickly (around 3 seconds)"""
        if len(self._history) < 2:
            return False
        times = [r.decision_ms for r in self._history]
        return statistics.mean(times) < 3000

    @property
    def is_cautious(self) -> bool:
        """current or historical low-ABV streak >= 3."""
        return self._consecutive_low >= 3 or self._max_low_streak >= 3

    @property
    def is_reckless(self) -> bool:
        """Consistently picks high-ABV shots regardless of risk."""
        if len(self._history) < 3:
            return False
        recent_abv = [r.alcohol_chosen.abv for r in list(self._history)[-3:]]
        return all(a >= 38 for a in recent_abv)

    @property
    def uses_tricks_heavily(self) -> bool:
        return self._trick_cards_used >= 2

    @property
    def current_low_streak(self) -> int:
        return self._consecutive_low

    def predict_player_pick(self, available_positions: list[int]) -> int | None:
        """
        Nina's prediction of which glass the player will likely pick.
        Used to influence her own pick (avoid the glass she thinks you want,
        or try to predict and react in irritated.)

        Returns a position index or None if no clear prediction.
        """
        if not available_positions:
            return None

        # Preferred position bias
        pref = self.preferred_position
        if pref is not None and pref in available_positions:
            # if player is decisive, they're more predictable
            confidence = 0.65 if self.is_decisive else 0.45
            if random.random() < confidence:
                return pref

        # Catious players avoid the last glass (sin glass)
        if self.is_cautious and len(available_positions) > 1:
            non_last = [p for p in available_positions if p != max(available_positions)]
            if non_last:
                return non_last[0]

        return None  # no prediction

    def summary_for_nina(self) -> dict:
        """
        Structured summary Nina can read for dialogue, tells or mood
        """
        return {
            "decisive": self.is_decisive,
            "cautious": self.is_cautious,
            "reckless": self.is_reckless,
            "preferred_position": self.preferred_position,
            "tricks_heavy": self.uses_tricks_heavily,
            "low_streak": self._consecutive_low,
            "total_turns": self._total_turns,
        }
