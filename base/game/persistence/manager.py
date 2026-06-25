import json
from datetime import datetime
import shutil
from platformdirs import user_documents_path

from base.game.state import GameState
from base.other.dirs import dirs

SAVE_FILE = dirs.user_data_path / "save.json"
CHECKER_FILE = user_documents_path() / ".hb" / "deleteifgay.json"


# secret thing that checks any remote changes on startup
# exists to notice cheating


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
        """Checks if save file has been tampered with."""
        if self._data == self._default_save():
            return True
        if not CHECKER_FILE.exists():
            return False
        else:
            try:
                with open(CHECKER_FILE, "r", encoding="utf-8") as f:
                    checker_data = json.load(f)
            except (json.decoder.JSONDecodeError, KeyError):
                CHECKER_FILE.rename(CHECKER_FILE.with_suffix(".corrupted.json"))
                return False

        if checker_data == self._default_save():
            return True
        return False

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

    def load_active_run(self) -> GameState | None:
        raw = self._data.get("active_run")
        if raw is None:
            return None
        # noinspection PyTypeChecker
        return GameState.from_dict(raw)

    @staticmethod
    def _copy_slot() -> None:
        """copies save file to checker file"""
        if SAVE_FILE.exists():
            shutil.copy2(SAVE_FILE, CHECKER_FILE)
