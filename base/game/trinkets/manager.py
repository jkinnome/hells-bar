from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from base.game.eventbus import EventType, EventBus
from base.game.trinkets.base import TrinketEffect, Trinket

if TYPE_CHECKING:
    from base.game.state import GameState
    from base.game.ninoula.ninoula import Ninoula
    from base.game.shots import Alcohol

MAX_SLOTS = 2  # base, 3 after unlock


class TrinketManager:
    """
    Manages all equipped trinkets for the run.
    Hooks into the game loop at defined points.
    Subscribes to EventBus for reactive trinkets.
    """

    def __init__(self, event_bus: "EventBus", extra_slot: bool = False) -> None:
        self._bus: EventBus = event_bus
        self._equipped: list[Trinket] = []
        self._slots: int = MAX_SLOTS + (1 if extra_slot else 0)
        self._state: Optional["GameState"] = None
        self._nina: Optional["Ninoula"] = None

        # Runtime flags (trinket-specific, set by on_event handlers)
        self._borrowed_luck_debt: bool = False
        self._nina_drink_history: list[dict] = []  # last 3 shots Nina drank

        self._subscribe_to_bus()

        # --- Slot Management ---

    @property
    def slots_used(self) -> int:
        return sum(t.slot_weight.value for t in self._equipped)

    @property
    def slots_free(self) -> int:
        return self._slots - self.slots_used

    def can_equip(self, trinket: Trinket) -> bool:
        return trinket.slot_weight.value <= self.slots_free

    def equip(self, trinket: Trinket, state: "GameState", nina: "Ninoula") -> bool:
        if not self.can_equip(trinket):
            return False
        self._equipped.append(trinket)
        effect = trinket.on_equip(state, nina)
        if effect:
            self._apply_effect(effect, state, nina)
        return True

    def unequip(self, trinket_id: str) -> Optional[Trinket]:
        for i, t in enumerate(self._equipped):
            if t.id == trinket_id:
                return self._equipped.pop(i)
        return None

    def has(self, trinket_id: str) -> bool:
        return any(t.id == trinket_id for t in self._equipped)

    def has_charges(self, trinket_id: str) -> bool:
        for t in self._equipped:
            if t.id == trinket_id:
                return t.has_charge
        return False

    def get(self, trinket_id: str) -> Optional[Trinket]:
        for t in self._equipped:
            if t.id == trinket_id:
                return t
        return None

    # --- Game Loop Hooks ---

    def on_run_start(self, state: "GameState", nina: "Ninoula") -> None:
        self._state = state
        self._nina = nina
        for t in self._equipped:
            effect = t.on_run_start(state, nina)
            if effect:
                self._apply_effect(effect, state, nina)

    def on_round_start(self, state: "GameState", nina: "Ninoula") -> None:
        # Clear borrowed luck debt flag at round start
        if self._borrowed_luck_debt:
            self._disable_random_card(state)
            self._borrowed_luck_debt = False

        for t in self._equipped:
            effect = t.on_round_start(state, nina)
            if effect:
                self._apply_effect(effect, state, nina)

    def on_player_drink(self, shot: Alcohol, state: "GameState", nina: "Ninoula") -> float:
        """Returns final BAC gain after all trinket modifications."""
        gain = shot.abv * 0.005  # base gain

        # Pass through on on_bac_gain hooks
        for t in self._equipped:
            gain = t.on_bac_gain(gain, state)

        # Pass through on_bac_gain hooks
        for t in self._equipped:
            effect = t.on_player_drink(shot, state)
            if effect:
                gain *= effect.bac_multiplier
                self._apply_effect(effect, state, nina)

        return gain

    def on_spite_spend(self, amount: int, state: "GameState") -> int:
        """Pass Spite spend through all trinket hooks. Returns actual spent"""
        actual = amount
        for t in self._equipped:
            actual = t.on_spite_spend(actual, state)
        return actual

    def on_nina_drink(self, shot: Alcohol, state: "GameState", nina: "Ninoula") -> None:
        # Track Nina's drink history (for Memory Fragment)
        self._nina_drink_history.append({
            "name": shot.name,
            "abv": shot.abv,
            "effect": shot.effect
        })
        if len(self._nina_drink_history) > 3:
            self._nina_drink_history.pop(0)

        for t in self._equipped:
            effect = t.on_nina_drink(shot, state, nina)
            if effect:
                self._apply_effect(effect, state, nina)

    def get_memory_log(self) -> list[dict]:
        """For Memory Fragment trinket."""
        return list(self._nina_drink_history)

    def on_run_end(self, state: "GameState") -> None:
        for t in self._equipped:
            t.on_run_end(state)

    # --- EventBus Integration ---

    def _subscribe_to_bus(self) -> None:
        """Subscribe to all events that trinkets might react to."""
        self._bus.subscribe()
        self._bus.subscribe()
        self._bus.subscribe()  # TODO: add events
        self._bus.subscribe()

    @staticmethod
    def _apply_effect(effect: TrinketEffect, state: "GameState", nina: "Ninoula") -> None:
        if effect.spite_flat:
            state.gain_spite(effect.spite_flat)

        if effect.affection_delta:
            nina.emotion.shift_affection(effect.affection_delta)

        if effect.tension_delta:
            nina.emotion.shift_tension(effect.tension_delta)

        if effect.cancel_blackout:
            state.player_bac = state.max_bac - 0.01

        if effect.set_bac_to is not None:
            state.player_bac = effect.set_bac_to

    # --- Helpers ---

    @staticmethod
    def _disable_random_card(state: "GameState") -> None:
        """Borrowed Luck debt, disable one random card this round."""
        if state.hand:
            disabled_card = random.choice(state.hand)
            state._disabled_cards_this_round = [disabled_card]

    def to_dict(self) -> list[dict]:
        return [t.to_dict() for t in self._equipped]
