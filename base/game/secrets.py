from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from base.game.state import GameState, RoundPhase
    from base.game.ninoula.ninoula import Ninoula
    from base.game.persistence.manager import PersistenceManager


@dataclass
class SecretEvent:
    id: str
    codex_key: str | None  # None = no codex entry
    condition: Callable  # (state, nina, persistence) -> bool
    effect: Callable  # (state, nina, persistence) -> dict | Effect (UI payload)
    once_per_run: bool = True
    once_per_save: bool = False


class SecretEventManager:
    """
    Manages all secret event conditions and firing
    Call check_all() at appropriate points in the game loop
    """

    def __init__(self, persistence_manager: PersistenceManager) -> None:
        self._persistence = persistence_manager
        self._fired_this_run: set[str] = set()
        self._events = self._build_registry()

    def reset_for_run(self) -> None:
        self._fired_this_run.clear()

    def check_all(self,
                  trigger_context: RoundPhase,
                  state: "GameState",
                  nina: "Ninoula") -> list[dict]:
        """
        Check all eligible events.
        Payloads are passed to GameScreen to render the event.
        :return: Returns list of UI payloads for events.
        """
        fired = []
        for event in self._events:
            if event.once_per_run and event.id in self._fired_this_run:
                continue
            if event.once_per_save and f"secret_{event.id}" in self._persistence._data["unlocks"]:
                continue

            try:
                if event.condition(state, nina, self._persistence):
                    payload = event.effect(state, nina, self._persistence)
                    self._fired_this_run.add(event.id)
                    if event.once_per_save:
                        self._persistence._data["unlocks"].append(f"secret_{event.id}")
                    if event.codex_key:
                        self._persistence._data["unlocks"]["nina_entries"](event.codex_key)
                    fired.append(payload)
            except Exception:
                pass  # never crash the game on a secret event

        return fired

    def _build_registry(self) -> list[SecretEvent]:
        return [
            SecretEvent(
                id="test",
                codex_key=None,
                condition=lambda s, n, p: None,
                effect=lambda s, n, p: None,
                once_per_run=True,
                once_per_save=True,
            )
        ]
