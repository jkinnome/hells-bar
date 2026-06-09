from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from game.state import GameState
    from game.ninoula.ninoula import Ninoula


class EffectTarget(Enum):
    PLAYER = auto()
    NINOULA = auto()
    BOTH = auto()
    TABLE = auto()  # affects the shot selection itself


class EffectTiming(Enum):
    IMMEDIATE = auto()  # resolves when drunk
    DELAYED = auto()  # resolves next round
    CUMULATIVE = auto()  # stacks across drinks
    ON_COMBO = auto()  # only resolves if combo triggered
    PASSIVE = auto()  # always active while "active"


@dataclass
class EffectResult:
    """Returned by Effect.apply(). Drives UI feedback."""
    description: str
    bac_delta: float = 0.0
    corruption_delta: float = 0.0
    spite_delta: int = 0
    affection_delta: float = 0.0
    tension_delta: float = 0.0
    cards_drawn: int = 0
    cards_destroyed: int = 0
    nina_mood_shift: Optional[str] = None  # e.g. "force_irritated"
    special_flag: Optional[str] = None  # e.g. "hubris_active"


class Effect:
    """Base class for all drink/card effects."""
    name: str = "Base Effect"
    timing: EffectTiming = EffectTiming.IMMEDIATE
    target: EffectTarget = EffectTarget.PLAYER
    tags: list[str] = field(default_factory=list)

    def apply(self, state: "GameState", nina: "Ninoula") -> EffectResult:
        raise NotImplementedError


# --- Concrete effect implementations ---

class NoEffect(Effect):
    name = "None"

    def apply(self, state, nina) -> EffectResult:
        return EffectResult(description="No effect.")

# --- Effect registy ---
EFFECT_REGISTRY: dict[str, Effect] = {
    "none": NoEffect(),
}


def get_effect(effect_id: str) -> Effect:
    # noinspection PyTypeChecker
    return EFFECT_REGISTRY.get(effect_id, NoEffect)
