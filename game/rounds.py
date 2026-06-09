from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class RoundType(Enum):
    STANDARD = auto()  # 3 mixed shots, default visibility
    BLIND = auto()  # all 3 hidden, no reveals possible
    NINA_FIRST = auto()  # Nina picks before player
    OPEN_TABLE = auto()  # names revealed, ABV hidden
    DOUBLE_OR_NOTHING = auto()  # 1 water, 1 destroyer, 50/50
    SPEED_ROUND = auto()  # 5-second pick timer
    NINAS_SPECIAL = auto()  # 4th glass appears, Nina's addition


# Weighted pool per escalation phase
ROUND_TYPE_POOLS = {
    "early": [(RoundType.STANDARD, 100)],
    "mid": [(RoundType.STANDARD, 50), (RoundType.BLIND, 15),
            (RoundType.NINA_FIRST, 10), (RoundType.OPEN_TABLE, 10),
            (RoundType.DOUBLE_OR_NOTHING, 5), (RoundType.SPEED_ROUND, 5),
            (RoundType.NINAS_SPECIAL, 5)],
    "late": [(RoundType.STANDARD, 35), (RoundType.BLIND, 20),
             (RoundType.NINA_FIRST, 15), (RoundType.OPEN_TABLE, 10),
             (RoundType.DOUBLE_OR_NOTHING, 8), (RoundType.SPEED_ROUND, 7),
             (RoundType.NINAS_SPECIAL, 5)],
    "endgame": [(RoundType.STANDARD, 20), (RoundType.BLIND, 25),
                (RoundType.NINA_FIRST, 15), (RoundType.DOUBLE_OR_NOTHING, 15),
                (RoundType.SPEED_ROUND, 15), (RoundType.NINAS_SPECIAL, 10)],
}


@dataclass
class RoundConfig:
    round_type: RoundType
    num_shots: int = 3
    reveal_count: int = 1  # how many shots start revealed
    timer_seconds: float | None = None  # None = no timer
    nina_picks_first: bool = False


def get_escalation_phase(round_number: int) -> str:
    if round_number <= 3:  return "early"
    if round_number <= 6:  return "mid"
    if round_number <= 9:  return "late"
    return "endgame"


def roll_round_type(round_number: int, modifier: str = "none") -> RoundConfig:
    """Pick a round type for the given round number."""
    # Some modifiers override round type
    if modifier == "blind_drunk":
        return RoundConfig(RoundType.BLIND, reveal_count=0)
    if modifier == "open_bar":
        return RoundConfig(RoundType.OPEN_TABLE, reveal_count=3)

    phase = get_escalation_phase(round_number)
    pool = ROUND_TYPE_POOLS[phase]
    types, weights = zip(*pool)
    chosen = random.choices(list(types), weights=list(weights), k=1)[0]

    configs = {
        RoundType.STANDARD: RoundConfig(chosen, reveal_count=1),
        RoundType.BLIND: RoundConfig(chosen, reveal_count=0),
        RoundType.NINA_FIRST: RoundConfig(chosen, nina_picks_first=True),
        RoundType.OPEN_TABLE: RoundConfig(chosen, reveal_count=3),
        RoundType.DOUBLE_OR_NOTHING: RoundConfig(chosen, num_shots=2, reveal_count=0),
        RoundType.SPEED_ROUND: RoundConfig(chosen, timer_seconds=5.0),
        RoundType.NINAS_SPECIAL: RoundConfig(chosen, num_shots=4),
    }
    return configs[chosen]
