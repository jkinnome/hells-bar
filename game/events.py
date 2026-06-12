from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class EventType(Enum):
    # --- Milestone Events (once per run) ---
    MILESTONE_BAC_15 = auto()  # player hits 0.15 BAC
    MILESTONE_BAC_25 = auto()  # player hits 0.25
    MILESTONE_BAC_35 = auto()  # player hits 0.35
    MILESTONE_BAC_45 = auto()  # player hits 0.45 (pass out on normal difficulty)
    MILESTONE_ROUND_5 = auto()  # survived 5 rounds
    MILESTONE_ROUND_10 = auto()  # survived 10 rounds
    MILESTONE_SPITE_10 = auto()  # accumulated 10 spite
    MILESTONE_FIRST_COMBO = auto()  # first combo triggered
    MILESTONE_SIN_SEEN = auto()  # Sin glass on table
    MILESTONE_NINA_TIPSY = auto()  # Nina hits 0.20 BAC for first time

    # --- Atmospheric Events (random and can reoccur) ---
    ATMOS_GLASS_FALLS = auto()
    ATMOS_MUSIC_SKIPS = auto()
    ATMOS_POWER_FLICKER = auto()
    ATMOS_DISTANT_SOUND = auto()
    ATMOS_NINA_CHECKS_NAILS = auto()
    ATMOS_NINA_REFILLS = auto()
    ATMOS_NINA_YAWNS = auto()

    # --- Reactive Events (action responses/run actions) ---
    REACT_NINA_TAUNT = auto()
    REACT_PLAYER_FAST = auto()
    REACT_PLAYER_LOW_STREAK = auto()
    REACT_PLAYER_HIGH_ABV = auto()
    REACT_NINA_BLUNDER = auto()
    REACT_COMBO_TRIGGER = auto()
    REACT_SIN_GLASS_PICKER = auto()
    REACT_CARD_PLAYED = auto()
    REACT_TRICK_CAUGHT = auto()
    REACT_SILENCE_CHAT = auto()

    # --- Unique Events (once per save file) ---
    # -- First Time Events --
    FIRST_WIN = auto()
    FIRST_LOSS = auto()
    FIRST_SIN_DRINK = auto()
    FIRST_TRIPLE_COMBO = auto()  # 3 combos in one round
    FIRST_LUCID_FLASH = auto()
    FIRST_TABLE_FLIP = auto()
    # -- Secret Events --
    SECRET_CONFESSION_ROOM = auto()

    # --- Nina Events (fired by Nina herself ---


@dataclass
class GameEvent:
    type: EventType
    payload: dict  # context data (e.g. {"abv": shot.abv, "shot_name": shot.name}
