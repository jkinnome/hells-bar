from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.state import GameState
    from game.ninoula.ninoula import Ninoula


@dataclass
class ComboResult:
    name: str
    description: str
    effect_fn: Callable
    tags_used: list[str]


# Each combo: (frozenset of required tags, name, description, effect_fn)
COMBO_TABLE: list[tuple[frozenset, str, str, Callable]] = [
    (
        frozenset({"Sweet", "Sweet"}),
        "Sugar Rush",
        "Corruption frozen for 2 rounds. The sweetness overwhelms the burn.",
        lambda state, nina: setattr(state, '_corruption_freeze', 2)
    ),
    (
        frozenset({"Demon", "Void"}),
        "Hellmouth",
        "Nina takes 0.02 BAC regardless of who drank it.",
        lambda state, nina: setattr(nina, 'bac', min(nina.bac + 0.02, 0.50))
    ),
    (
        frozenset({"Fire", "Herbal"}),
        "Alchemist's Error",
        "Both players gain the same BAC this round.",
        lambda state, nina: None  # handled in round resolution
    ),
    (
        frozenset({"Ghost", "Pure"}),
        "Passing Through",
        "Your BAC gain is halved.",
        lambda state, nina: setattr(state, '_bac_halved_this_round', True)
    ),
    (
        frozenset({"Spite", "Spirit"}),
        "Liquid Spite",
        "+3 Spite. The brew resonates with your anger.",
        lambda state, nina: state.gain_spite(3)
    ),
    (
        frozenset({"Void", "Void"}),
        "Event Horizon",
        "All shots cannot be revealed by any means this round.",
        lambda state, nina: setattr(state, '_reveal_blocked', True)
    ),
    (
        frozenset({"Warm", "Warm"}),
        "Slow Burn",
        "BAC gains delayed 1 round for both players.",
        lambda state, nina: setattr(state, '_delay_all_bac', True)
    ),
]


def detect_combo(shots: list[dict], state: "GameState",
                 nina: "Ninoula") -> list[ComboResult]:
    """
    Checks the current table for combo triggers.
    A combo fires if any two shots on the table share required tags.
    Returns a list of all triggered combos (can be multiple).
    """
    # Cursed shots block all combos
    all_tags = [tag for shot in shots for tag in shot.get("flavor_tags", [])]
    if "Cursed" in all_tags:
        return []

    # Malebolge's Falsifier also blocks combos
    if getattr(state, '_combo_blocked', False):
        return []

    triggered = []
    tag_set = set(all_tags)

    for required_tags, name, description, effect_fn in COMBO_TABLE:
        # Check if all required tags appear in the combined tag pool
        if required_tags.issubset(tag_set):
            result = ComboResult(
                name=name,
                description=description,
                effect_fn=effect_fn,
                tags_used=list(required_tags)
            )
            triggered.append(result)

    return triggered


def apply_combos(combos: list[ComboResult], state: "GameState",
                 nina: "Ninoula") -> list[str]:
    """Applies all triggered combos. Returns list of description strings for UI."""
    messages = []
    for combo in combos:
        combo.effect_fn(state, nina)
        state.stats.combos_triggered += 1
        messages.append(f"[bold yellow]COMBO:[/bold yellow] {combo.name} -- {combo.description}")
    return messages
