"""
SAVEMANAGER
PART OF JK'S CUSTOM LIBRARIES

This library exists to allow to easily create save files.
Created by JK
Copyright 2026
"""

import json
import pathlib
import shutil
import sys
from datetime import datetime

"""Edited for Hell's Bar"""

class SaveManager:
    def __init__(self, save_dir: str | pathlib.Path = "saves") -> None:
        self.save_dir = pathlib.Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _slot_path(self, slot: int) -> pathlib.Path:
        return self.save_dir / f"save_{slot:02}.json"

    def save(self, slot: int, data: dict, name: str = '', playtime: int = 0) -> None:
        payload = {
            "_meta": {
                "slot": slot,
                "name": name,  # can be area name, file name or whatever your heart desires
                "saved_at": datetime.now().isoformat(),
                "playtime_seconds": playtime
            },
            "data": data
        }
        self._slot_path(slot).write_text(json.dumps(payload, indent=2))

    def load(self, slot: int) -> dict | None:
        path = self._slot_path(slot)
        if not path.exists():
            sys.stderr.write(f"{path} does not exist.\n")
            return None
        try:
            payload = json.loads(path.read_text())
        except json.decoder.JSONDecodeError:
            sys.stderr.write(f"{path} is corrupt.\n")
            return None
        return payload["data"]

    def get_meta(self, slot: int) -> dict | None:
        path = self._slot_path(slot)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text()).get("_meta")
        except json.JSONDecodeError:
            return None

    def delete(self, slot: int) -> None:
        path = self._slot_path(slot)
        if path.exists():
            path.unlink()

    def list_slots(self) -> list[int]:
        """returns a list of all files that are savefiles"""
        slots = []
        for p in self.save_dir.glob("save_*.json"):
            parts = p.stem.split('_')
            if len(parts) == 2 and parts[1].isdigit():
                slots.append(int(parts[1]))
        return sorted(slots)

    def autosave(self, data: dict, playtime: int = 0) -> None:
        self.save(0, data, name='Autosave', playtime=playtime)

    def exists(self, slot: int) -> bool:
        return self._slot_path(slot).exists()

    def copy_slot(self, from_slot: int, to_slot: int) -> None:
        src = self._slot_path(from_slot)
        if src.exists():
            shutil.copy2(src, self._slot_path(to_slot))
