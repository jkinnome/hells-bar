from __future__ import annotations

import random
from typing import TYPE_CHECKING

from game.events import EventType
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


class WornCompass(Trinket):
    id = "worn_compass"
    name = "Worn Compass"
    description = "Seems to be broken."
    mechanical = "An arrow marks the glass with the lowest ABV no matter what."
    rarity = TrinketRarity.UNCOMMON

    def on_round_start(self, state, nina):
        # should find min(shot.abv) or something across all shots and then pass to a widget
        return


class TarnishedLocket(Trinket):
    id = "tarnished_locked"
    name = "Tarnished Locket"
    description = "This is not yours."
    mechanical = "When Affection is >= 0.7, all BAC gains get reduced by 5%."
    rarity = TrinketRarity.UNCOMMON

    def on_player_drink(self, shot, state, nina):
        if nina.emotion.affection >= 0.7:
            shot.abv *= 0.95


class AnotherStraw(Trinket):
    id = "another_straw"
    name = "Another Straw"
    description = "Straws have become too expensive."
    mechanical = "When any combo is activated, gain +1 Spite"
    rarity = TrinketRarity.UNCOMMON

    def on_event(self, event, state, nina):
        if event.type == EventType.REACT_COMBO_TRIGGER:
            return TrinketEffect(spite_flat=1)
        return None


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


class IronRing(Trinket):
    id = "iron_ring"
    name = "Iron Ring"
    description = "Iron doesn't work with all."
    mechanical = "Effects from Cursed drinks don't apply."
    rarity = TrinketRarity.META

    # in Effect.apply() check state.trinkets.has("iron_ring") and then effect.type == EffectType.CURSED_SECONDARY
    # return EffectResult(description="blocked by iron")


class ChippedGlass(Trinket):
    id = "chipped_glass"
    name = "Chipped Glass"
    description = "You're bringing your own glass into a bar?"
    mechanical = "Once per run you can drink from your own glass and skip your turn."

    # add a pick option to GameScreen.BINDINGS


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
    rarity = TrinketRarity.META
    max_charges = 1

    def on_bac_gain(self, gain: float, state: "GameState") -> float:
        if not self.has_charge:
            return gain
        if state.player_bac + gain >= state.max_bac:
            self.consume_charge()
            state.player_bac = state.max_bac - 0.01
            # noinspection PyTypeChecker
            return TrinketEffect(cancel_blackout=True)
            # returning TrinketEffect from on_bac_gain is a special case.
            # TrinketManager.on_player_drink() checks for this and reroutes.
        return gain


class LuckyHorseshoe(Trinket):
    id = "lucky_horseshoe"
    name = "Lucky Horseshoe"
    description = "You can hardly call this a horseshoe. More like a warped piece of metal."
    mechanical = "25% for a hidden glass you pick to be the best shot possible. Succesful once per run."
    rarity = TrinketRarity.UNCOMMON

    # Subscribe to player pick event where shot is hidden, roll random() < 0.25, then make a best_shot_for_build func


class CrowsEye(Trinket):
    id = "crows_eye"
    name = "Crow's Eye"
    description = "Where did you get this from?"
    mechanical = "Once per run a Probe Chat option will be answered with complete truth. Tension rises by +0.15"
    rarity = TrinketRarity.META
    max_charges = 1

    # In ChatSystem._resolve_probe() check if state.trinkets.has_charges("crows_eye") force the truth and consume charge


class SpiteVial(Trinket):
    id = "spite_vial"
    name = "Spite Vial"
    description = "It's dark."
    mechanical = "30% chance Spite isn't used when using an action involving Spite."
    rarity = TrinketRarity.RARE

    # in GameState.spend_spite() if random() > 0.3, use the spite.


class HouseRules(Trinket):
    id = "house_rules"
    name = "The House Rules"
    description = "A simple piece of paper."
    mechanical = "At the start of each round there's a 15% chance a House Rule activates."
    HOUSE_RULES = [  # placeholder
        "Generous Pour: All ABV gains -5% this round",
        "Last Minute: Impatience meter starts at double duration",
        "Quiet Round: Nina does not taunt you this round",
        ...
    ]

    def on_round_start(self, state, nina):
        if random.random() < 0.15:
            choice = random.choice(self.HOUSE_RULES)
            # then apply via something like GameState._active_house_rule


# --- Cursed Trinkets ---
class HeavyGlass(Trinket):
    id = "heavy_glass"
    name = "Heavy Glass"
    description = "You always pour a little extra."
    mechanical = "All BAC gains +8% and generate Spite at 1.5x rate."
    rarity = TrinketRarity.CURSED

    def on_player_drink(self, shot, state, nina):
        return TrinketEffect(bac_multiplier=1.08, spite_multiplier=1.5)


class CrackedMirror(Trinket):
    id = "cracked_mirror"
    name = "Cracked Mirror"
    description = "After all this, it's still you."
    mechanical = "Corruption display is shown 20% higher, but is actually 10% lower."
    rarity = TrinketRarity.CURSED

    # CorruptableLabel reads state.corruption * 1.2 for display. Actual corruption is multiplied by 0.9 before storing



# --- Relics ---

# --- Secret Trinkets ---
class MemoryFragment(Trinket):
    id = "memory_fragment"
    name = "Memory Fragment"
    description = "It's warm."
    mechanical = "During the Breath Phase you can recall Nina's last 3 reactions."
    rarity = TrinketRarity.SECRET

    # Expose to UI via an extra function, something like state.trinkets.get_memory_log()


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
