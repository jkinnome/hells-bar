"""
CONFIGMANAGER
PART OF JK'S CUSTOM LIBRARIES

This library exists to easily allow devs to create config files.

Created by JK
Copyright 2026
"""
import base.game.config.configs as c
import json
import pathlib
import sys

from base.other.dirs import dirs
from base.other.log import log

_MISSING = object()  # module-level sentinel


class ConfigManager:
    """
    JSON-backed config with defaults and dot-access.

    Usage:
        config = ConfigManager("settings.json", defaults={"volume": 1.0})
        config.get("volume")        # 1.0
        config.set("volume", 0.5)
        config.save()
    """

    def __init__(
            self,
            path: str | pathlib.Path,
            defaults: dict | None = None,
            auto_save: bool = True,
    ) -> None:
        self._path = pathlib.Path(path)
        self._defaults = defaults or {}
        self._data: dict = {}
        self.auto_save = auto_save
        self.load()

    def load(self) -> None:
        """Load config from disk. Falls back to defaults if file missing or corrupt."""
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except json.JSONDecodeError:
                log.warning(f"'{self._path}' is corrupt, falling back to defaults.")
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        """Write current config to disk."""
        self._path.write_text(json.dumps(self._data, indent=2))
        log.info("saved config")

    def get(self, key_path: str, fallback=_MISSING):
        """Get a value. Priority: saved data → defaults → fallback."""
        keys = key_path.split(".")
        data = self._data
        try:
            for k in keys:
                data = data[k]
            return data
        except (KeyError, TypeError):
            try:
                val = self._defaults
                for k in keys:
                    val = val[k]
                return val
            except (KeyError, TypeError):
                if fallback is not _MISSING:
                    return fallback

                return None

    def _set_nested(self, data: dict, keys: list[str], value) -> dict:
        """Recursively drill into nested dicts, creating levels as needed."""
        if len(keys) == 1:
            data[keys[0]] = value
            return data
        if keys[0] not in data or not isinstance(data[keys[0]], dict):
            data[keys[0]] = {}
        self._set_nested(data[keys[0]], keys[1:], value)
        return data

    def set(self, key_path: str, value) -> None:
        """Set a value by dot-path. Creates intermediate dicts as needed.
        If autosave is disabled, you'll need to manually save again."""
        keys = key_path.split(".")
        log.info(f"{key_path} -> {value}")
        self._set_nested(self._data, keys, value)
        if self.auto_save:
            self.save()

    def reset(self, key: str) -> None:
        """Remove a key from saved data, reverting to default."""
        self._data.pop(key, None)
        log.info(f"{key} -> {self._defaults.get(key, None)} (default)")
        if self.auto_save: self.save()

    def reset_all(self) -> None:
        """Wipe all saved data, reverting everything to defaults."""
        self._data = {}
        log.info(f"reset all saved data")
        if self.auto_save: self.save()

    def as_dict(self) -> dict:
        """Returns merged view of defaults and saved data."""
        return {**self._defaults, **self._data}

    def has(self, key: str) -> bool:
        """Returns True if the key exists in saved data or defaults."""
        return key in self._data or key in self._defaults

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(result.get(k), dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result
