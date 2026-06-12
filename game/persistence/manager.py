import json
import os
from pathlib import Path
from game.state import GameState
from game.persistence.stats import AllTimeStats

SAVE_DIR = Path.home() / ".hells_bar"
SAVE_FILE = SAVE_DIR / "save.json"


class PersistenceManager:
    def __init__(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load_raw()

    def _load_raw(self) -> dict:
        if not SAVE_FILE.exists():
            return self._default_save()
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.decoder.JSONDecodeError, KeyError):
            # Corrupted save
            SAVE_FILE.rename(SAVE_FILE.with_suffix(".corrupted.json"))
            return self._default_save()

    @staticmethod
    def _default_save() -> dict:
        return {
            "schema_version": 1,
            "runs_played": 0,
            "all_time_stats": {},
            "active_run": None,
            "codex": {"drinks": {}, "nina_entries": []},
            "notebook": {},  # {"run_number": [{"text": ..., "corruption": ...}]}
            "unlocks": [],
            "settings": {},
        }

    def _write(self) -> None:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4, default=str)

    @property
    def runs_played(self) -> int:
        return self._data.get("runs_played", 0)

    def save_active_run(self, state: GameState) -> None:
        self._data["active_run"] = state.to_dict()
        self._write()

    def load_active_run(self) -> GameState | None:
        raw = self._data.get("active_run")
        if raw is None:
            return None
        return GameState.from_dict(raw)
