from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base.game.persistence.manager import PersistenceManager
    from base.game.state import GameState, RunOutcome


@dataclass
class Unlock:
    id: str
    name: str
    description: str
    nina_quote: str
    condition: str  # human-readable condition (for the unlock screen)


UNLOCKS: list[Unlock] = [
    ...  # TODO: add all unlocks
]

UNLOCK_ID_SET = {u.id for u in UNLOCKS}


class MetaProgressionManager:
    def __init__(self, persistence: "PersistenceManager"):
        self.persistence = persistence

    def check_end_of_run(self, state: "GameState",
                         outcome: "RunOutcome") -> list[Unlock]:
        """
        Called after every run. Checks all unlock conditions.
        Returns list of newly earned unlocks.
        """
        from base.game.state import RunOutcome
        newly_unlocked = []
        runs = self.persistence.runs_played + 1  # +1 for the run just completed

        candidates = [
            ("notebook", runs >= 1),
            ("iron_liver", runs >= 3),
            ("hollow_leg", state.stats.rounds_survived >= 7
             and state.stats.cards_played == 0),
            ("tin_ear", self._alltime_taunts() >= 50),
            ("spite_run", self._alltime_spite() >= 50),
            ("blind_drunk", outcome == RunOutcome.PLAYER_WIN),
            ("the_codex", self._drinks_discovered() >= 10),
            ("daily_challenge", runs >= 5),
        ]

        for unlock_id, condition in candidates:
            if condition and self.persistence.unlock(unlock_id):
                unlock = next(u for u in UNLOCKS if u.id == unlock_id)
                newly_unlocked.append(unlock)

        return newly_unlocked

    def _alltime_taunts(self) -> int:
        # Read from AllTimeStats via persistence
        return self.persistence._data.get("all_time_stats", {}).get("total_taunts_received", 0)

    def _alltime_spite(self) -> int:
        return self.persistence._data.get("all_time_stats", {}).get("total_spite_generated", 0)

    def _drinks_discovered(self) -> int:
        return len(self.persistence._data.get("codex", {}).get("drinks", {}))
