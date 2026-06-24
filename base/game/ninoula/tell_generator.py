from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.ninoula.ninoula import Ninoula


@dataclass
class ActiveTell:
    """A tell currently visible in UI"""
    tell_id: str  # tell ids for codex unlock
    ui_text: str  # what appears in dialogue
    is_known: bool  # False = fire but invisible until codex entry unlocked


class TellGenerator:
    """
    Generates tells from Nina's current state flags.
    Called at the end of begin_decision() and decide().
    """

    def generate(self, nina: "Ninoula") -> list[ActiveTell]:
        """Return all tells currently active."""
        tells = []

        # table tap: she's already decided
        if nina._already_decided:
            tells.append(ActiveTell(
                tell_id="table_tap",
                ui_text="*taps the table twice*",
                is_known=False,  # unknown until codex unlocked
            ))
        ...

        return tells
