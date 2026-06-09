"""ALL OF GAME STATE. TEXTUAL WIDGETS ARE NOT ALLOWED TO BE IMPORTED"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.shots import Alcohol


class RunOutcome(Enum):
    IN_PROGRESS = auto()
    PLAYER_WIN = auto()
    PLAYER_LOSS = auto()
    MUTUAL_DRAW = auto()  # possible via Blackout Dagger card
    ABANDONED = auto()


class Difficulty(Enum):
    FORGIVING = auto()
    STANDARD = auto()
    CRUEL = auto()


DIFFICULTY_CONFIG = {
    Difficulty.FORGIVING: {"max_bac": 0.45, "corruption_rate": 0.8, "patience": 15.0},
    Difficulty.STANDARD: {"max_bac": 0.40, "corruption_rate": 1.0, "patience": 8.0},
    Difficulty.CRUEL: {"max_bac": 0.35, "corruption_rate": 1.3, "patience": 5.0}
}


@dataclass
class RunStats:
    """All statistics for a single run. Feeds the Run Summary screen."""
    rounds_survived: int = 0
    shots_drunk: int = 0
    highest_abv_drunk: float = 0.0
    highest_abv_name: str = ""
    total_bac_consumed: float = 0.0
    peak_corruption: float = 0.0
    spite_generated: int = 0
    spite_spent: int = 0
    cards_played: int = 0
    cards_failed: int = 0
    tricks_caught: int = 0
    combos_triggered: int = 0
    taunts_received: int = 0
    chat_actions_used: int = 0
    nina_final_mood: str = ""
    nina_final_bac: float = 0.0
    # Speed tracking
    fastest_turn_ms: int = 999999
    slowest_turn_ms: int = 0
    total_hesitations: int = 0  # times impatience timer fired
    # Streak tracking
    current_low_streak: int = 0  # consecutive low-ABV picks
    max_low_streak: int = 0
    sin_drinks_seen: int = 0
    sin_drinks_survived: int = 0


@dataclass
class GameState:
    """
    Complete state for one run. Made fresh each run (mostly).
    Can be serialized into JSON for saving and loading
    """
    # ---- Basic ----
    player_name: str = "Darling"
    seed: int = 0
    run_number: int = 1
    modifier: str = "none"
    difficulty: Difficulty = Difficulty.STANDARD

    # ---- Round values ----
    player_bac: float = 0.0
    nina_bac: float = 0.0
    corruption: float = 0.0
    spite: int = 0
    round_number: int = 1
    outcome: RunOutcome = RunOutcome.IN_PROGRESS

    # ---- Difficulty config ----
    max_bac: float = 0.4
    patience_seconds: float = 8.0
    corruption_rate: float = 1.0

    # ---- Ninoula ----
    affection: float = 0.0  # 0.0 - 1.0
    tension: float = 0.0  # 0.0 - 1.0

    # ---- Cards & Trinkets ----
    hand: list[str] = field(default_factory=list)  # cards IDs
    equipped_trinkets: list[str] = field(default_factory=list)  # trinket IDs

    # ---- Round state ----
    current_shots: list[Alcohol] = field(default_factory=list)
    player_picked_idx: Optional[int] = None
    nina_picked_idx: Optional[int] = None
    turn_start_time: float = 0.0  # time.monotonic() at turn start

    # ---- Flags ----
    player_turn: bool = False
    sin_drink_active: bool = False  # True if a Sin glass is on the table this round
    last_call_triggered: bool = False  # True once Last Call state fires

    # ---- Statistics ----
    stats: RunStats = field(default_factory=RunStats)

    def __post_init__(self) -> None:
        cfg = DIFFICULTY_CONFIG[self.difficulty]
        self.max_bac = cfg["max_bac"]
        self.patience_seconds = cfg["patience"]
        self.corruption_rate = cfg["corruption_rate"]

    # ---- Computed properties ----
    @property
    def corruption_tier(self) -> int:
        """0 = clean, 1 = mild, 2 = moderate, 3 = severe, 4 = blackout"""
        if self.corruption < 0.2: return 0
        if self.corruption < 0.4: return 1
        if self.corruption < 0.6: return 2
        if self.corruption < 0.8: return 3
        return 4

    @property
    def is_last_call(self) -> bool:
        """True when player is extremely close to black out."""
        return self.player_bac >= self.max_bac * 0.87

    # ---- Mutators ----
    def player_drink(self, shot: Alcohol) -> None:
        gain = shot.abv * 0.005 * self.corruption_rate
        self.player_bac = min(self.player_bac + gain, self.max_bac)
        self.corruption = min(self.corruption + (shot.abv * 0.15) * self.corruption_rate, 1.0)

        self.stats.shots_drunk += 1
        self.stats.total_bac_consumed += gain
        self.stats.peak_corruption = max(self.stats.peak_corruption, self.corruption)

        if shot.abv > self.stats.highest_abv_drunk:
            self.stats.highest_abv_drunk = shot.abv
            self.stats.highest_abv_name = shot.name

        if shot.abv < 20:
            self.stats.current_low_streak += 1
            self.stats.max_low_streak = max(self.stats.max_low_streak, self.stats.current_low_streak)
        else:
            self.stats.current_low_streak = 0

    def gain_spite(self, amount: int) -> None:
        self.spite += amount
        self.stats.spite_generated += amount

    def spend_spite(self, amount: int) -> bool:
        """Spends spite based on amount, returns a bool depending on success."""
        if self.spite < amount:
            return False
        self.spite -= amount
        self.stats.spite_spent += amount
        return True

    def record_turn_end(self) -> None:
        elapsed_s = int((time.monotonic() - self.turn_start_time) * 1000)
        self.stats.fastest_turn_ms += min(self.stats.fastest_turn_ms, elapsed_s)
        self.stats.slowest_turn_ms += max(self.stats.slowest_turn_ms, elapsed_s)

    def to_dict(self) -> dict:
        """Serialize for save file. converts enums to strings."""
        d = asdict(self)
        d["difficulty"] = self.difficulty.name
        d["outcome"] = self.outcome.name
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        d = d.copy()
        d["difficulty"] = Difficulty[d["difficulty"]]
        d["outcome"] = RunOutcome[d["outcome"]]
        d["stats"] = RunStats(**d["stats"])
        return cls(**d)
