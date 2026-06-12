from __future__ import annotations

from typing import TYPE_CHECKING

from game.events import GameEvent
from game.trinkets.base import Trinket, TrinketEffect, TrinketRarity

...

if TYPE_CHECKING:
    from game.state import GameState


# Passive Trinkets
class IronLiver(Trinket):
    id = "iron_liver"
    name = "Iron Liver"
    description = "Built up a tolerance."
    mechanical = "All BAC gains reduced by 10%."
    rarity = TrinketRarity.COMMON

    def on_bac_gain(self, gain: float, state: "GameState") -> float:
        return gain * 0.9


class HollowLeg(Trinket):
    id = "hollow_leg"
    name = "Hollow Leg"
    description = "There's more room than there should be."
    mechanical = "Max BAC threshold increased to 0.45."
    rarity = TrinketRarity.COMMON

    def on_equip(self, state, nina):
        state.max_bax = 0.45
        return None

    def on_run_start(self, state, nina):
        state.max_bax = 0.45  # reapply
        return None


class CrackedCoaster(Trinket):
    id = "cracked_coaster"
    name = "Cracked Coaster"
    description = "Don't worry, she isn't missing this."
    mechanical = "Start each run with +2 Spite."
    rarity = TrinketRarity.COMMON

    def on_run_start(self, state, nina):
        return TrinketEffect(spite_flat=2)


class SilverTongue(Trinket):
    id = "silver_tongue"
    name = "Silver Tongue"
    description = "You keep it between your teeth when you talk."
    mechanical = "+0.12 to all Affection gains from Chat actions."
    rarity = TrinketRarity.UNCOMMON

    # Applied in ChatSystem. Checked via TrinketManager.has("silver_tongue")
    # ChatSystem adds +0.12 to affection_delta if this is equipped.


class DemonsReceipt(Trinket):
    id = "demons_receipt"
    name = "Demon's Receipt"
    description = "For services rendered. The date is illegible."
    mechanical = "All Tension gains reduced by 20%."
    rarity = TrinketRarity.UNCOMMON

    def on_event(self, event, state, nina):
        # Tension reduction is applied in NinolaDecision and ChatSystem
        # by checking TrinketManager.has("demons_receipt").
        # No hook needed here for the reduction itself.
        # But: fire a one-time Nina reaction on first equip.
        return None  # handled externally


class StaticCoat(Trinket):
    id = "static_coat"
    name = "Static Coat"
    description = "It crackles when you walk."
    mechanical = ("+0.05 Tension at run start. Nina's SMUG_BORED sub-state "
                  "never activates. Her minimum engagement is 0.40.")
    rarity = TrinketRarity.UNCOMMON

    def on_run_start(self, state, nina):
        return TrinketEffect(tension_delta=0.05)
        # MoodEngine._compute_sub() checks TrinketManager.has("static_coat")
        # and suppresses SMUG.BORED if found


# Reactive Trinkets

class GrudgeStone(Trinket):
    id = "grudge_stone"
    name = "Grudge Stone"
    description = "You've been rubbing it since she caught you."
    mechanical = "When a Trick card is caught, gain +3 Spite instead of penalty."
    rarity = TrinketRarity.UNCOMMON

    def on_event(self, event, state, nina):
        if event.type == EventType.REACT_TRICK_CAUGHT:
            return TrinketEffect(spite_flat=3)
        return None


class PainkillerTin(Trinket):
    id = "painkiller_tin"
    name = "Painkiller Tin"
    description = "You've been saving this."
    mechanical = "Once per run: survive a blackout-level drink at BAC max-0.01."
    rarity = TrinketRarity.UNCOMMON
    max_charges = 1

    def on_bac_gain(self, gain: float, state: "GameState") -> float:
        if not self.has_charge:
            return gain
        if state.player_bac + gain >= state.max_bac:
            self.consume_charge()
            # noinspection PyTypeChecker
            return TrinketEffect(cancel_blackout=True)
            # returning TrinketEffect from on_bac_gain is a special case.
            # TrinketManager.on_player_drink() checks for this and reroutes.
        return gain


...

# --- Cursed Trinkets ---

# --- Relics ---

# --- Secret Trinkets ---

# --- Registry ---

ALL_TRINKETS: dict[str, type[Trinket]] = {
    cls.id: cls for cls in [
        IronLiver, HollowLeg, CrackedCoaster, SilverTongue, DemonsReceipt,
        StaticCoat, GrudgeStone, PainkillerTin,
    ]
}


def create_trinket(trinket_id: str) -> Trinket:
    cls = ALL_TRINKETS.get(trinket_id)
    if cls is None:
        raise ValueError(f"Unknown trinket: {trinket_id}")
    return cls()
