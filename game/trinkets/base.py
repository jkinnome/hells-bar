from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game.state import GameState
    from game.ninoula.ninoula import Ninoula
    from game.eventbus import GameEvent


class TrinketRarity(Enum):
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    CURSED = auto()
    RELIC = auto()
    SECRET = auto()


class SlotWeight(Enum):
    NORMAL = 1
    HEAVY = 2  # occupies both slots


@dataclass
class TrinketEffect:
    """
    Returned by trinket hooks to signal side effects.
    The TrinketManager applies these to GameState / Ninoula.
    """
    bac_multiplier: float = 1.0  # multiplicative BAC modifier
    spite_multiplier: float = 1.0  # multiplicative Spite modifier
    spite_flat: int = 0  # flat Spite addition
    affection_delta: float = 0.0
    tension_delta: float = 0.0
    corruption_multiplier: float = 1.0
    cancel_blackout: bool = False  # Painkiller Tin
    set_bac_to: Optional[float] = None
    ui_message: Optional[str] = None  # shown in dialogue panel
    nina_reaction_key: Optional[str] = None


# noinspection PyUnusedLocal,PyMethodMayBeStatic
class Trinket(ABC):
    """
    Base class for all trinkets.
    """
    id: str
    name: str
    description: str
    mechanical: str  # plain description of the mechanic
    rarity: TrinketRarity
    slot_weight: SlotWeight = SlotWeight.NORMAL

    # Charge system (None = unlimited / passive)
    max_charges: Optional[int] = None
    _charges: int = 0

    def __post_init__(self):
        if self.max_charges is not None:
            self._charges = self.max_charges

    @property
    def has_charge(self) -> bool:
        if self.max_charges is None:
            return True
        return self._charges > 0

    def consume_charge(self) -> bool:
        """Returns True if charge is consumed."""
        if self.max_charges is None:
            return True
        if self._charges > 0:
            self._charges -= 1
            return True
        return False

    # --- ABSTRACT HOOKS ---

    def on_equip(self, state: "GameState",
                 nina: "Ninoula") -> Optional[TrinketEffect]:
        return None

    def on_run_start(self, state: "GameState",
                     nina: "Ninoula") -> Optional[TrinketEffect]:
        return None

    def on_round_start(self, state: "GameState",
                       nina: "Ninoula") -> Optional[TrinketEffect]:
        return None

    def on_player_drink(self, abv: float, shot: dict,
                        state: "GameState") -> Optional[TrinketEffect]:
        return None

    def on_nina_drink(self, abv: float, shot: dict,
                      state: "GameState",
                      nina: "Ninoula") -> Optional[TrinketEffect]:
        return None

    def on_spite_spend(self, amount: int,
                       state: "GameState") -> int:
        """Return the actual amount of Spite to spend (for Vial refund)."""
        return amount

    def on_bac_gain(self, gain: float,
                    state: "GameState") -> float:
        """Return the modified BAC gain."""
        return gain

    def on_event(self, event: "GameEvent",
                 state: "GameState",
                 nina: "Ninoula") -> Optional[TrinketEffect]:
        return None

    def on_run_end(self, state: "GameState") -> None:
        """Called when run ends. Relics override this to burn themselves."""
        pass

    def to_dict(self) -> dict:
        return {"id": self.id, "charges": self._charges}

    @classmethod
    def from_dict(cls, d: dict) -> "Trinket":
        t = cls()
        if "charges" in d and t.max_charges is not None:
            t._charges = d["charges"]
        return t
