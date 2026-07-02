import json
from datetime import datetime
import shutil
from hashlib import sha256
from base.game.state import GameState
from base.other.dirs import dirs

SAVE_FILE = dirs.user_data_path / "save.json"
HASH_FILE = dirs.site_cache_path / "save.hash"


class PersistenceManager:
    def __init__(self):
        self._data = self._load_raw()
        is_changed = not self._check_save()

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

    def _check_save(self) -> bool:
        """Checks if save file has NOT been tampered with."""
        if self._data == self._default_save():
            return True
        if not HASH_FILE.exists():
            return False
        else:
            try:
                with open(HASH_FILE, "r", encoding="utf-8") as f:
                    hash_given = f.read()
                if sha256(bytes(self._data)).hexdigest() == hash_given:
                    return True
            except (FileNotFoundError, KeyError):
                return True
        return True

    @staticmethod
    def _default_save() -> dict:
        return {
            "schema_version": 1,
            "runs_played": datetime.now().isoformat(),
            "last_played": "",
            "all_time_stats": {},
            "active_run": None,
            "codex": {"drinks": {}, "nina_entries": {}},
            "notebook": {},  # {"run_number": [{"text": ..., "corruption": ...}]}
            "unlocks": [],
        }

    def _write(self) -> None:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4, default=str)
        self._copy_slot()

    @property
    def runs_played(self) -> int:
        return self._data.get("runs_played", 0)

    def save_active_run(self, state: GameState) -> None:
        self._data["active_run"] = state.to_dict()
        self._write()

    def load_active_run(self, state: "GameState") -> GameState | None:
        raw = self._data.get("active_run")
        if raw is None:
            return None
        # noinspection PyTypeChecker
        return state.from_dict(raw)
