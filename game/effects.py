from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

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
    DOUBLE_DELAYED = auto()  # resolves in two rounds
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


class WarmthEffect(Effect):
    """Bourbon: +1 Spite next round"""
    name = "Warmth"
    timing = EffectTiming.DELAYED

    def apply(self, state, nina) -> EffectResult:
        state.gain_spite(1)
        return EffectResult(
            description="The warmth settles in your chest...",
            spite_delta=1
        )


class ClarityEffect(Effect):
    """Gin: reduce corruption by 5%"""
    name = "Clarity"

    def apply(self, state, nina) -> EffectResult:
        delta = min(0.05, state.corruption)
        state.corruption -= delta
        return EffectResult(
            description="The gin cuts through the haze.",
            corruption_delta=delta
        )


class SlowBurnEffect(Effect):
    """Red Wine: BAC gain delayed 1 round."""
    name = "Slow Burn"
    timing = EffectTiming.DELAYED

    def apply(self, state, nina) -> EffectResult:
        # The BAC from this shot is stored as pending and applied next round
        # GameState handles the pending_bac_delay list separately
        return EffectResult(
            description="The wine slows the burn.",
            special_flag="delay_bac"
        )


# --- Effect registy ---
EFFECT_REGISTRY: dict[str, Effect] = {
    "none": NoEffect(),
    "warmth": WarmthEffect(),
    "clarity": ClarityEffect(),
    "slow_burn": SlowBurnEffect(),
}


def get_effect(effect_id: str) -> Effect:
    # noinspection PyTypeChecker
    return EFFECT_REGISTRY.get(effect_id, NoEffect)
