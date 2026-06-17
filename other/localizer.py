"""
LOCALIZER
PART OF JK'S CUSTOM LIBRARIES

This library exists to make it simple to
add localization and multiple languages to projects.

Created by JK
Copyright 2026
"""

import json
import locale
import os
import pathlib
import random
import sys

"""edited for Hell's Bar"""


def getAppDataFilePath() -> pathlib.Path:
    cache_dir = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "Hell's_Bar"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


LANGUAGES: dict[str, str] = {
    "en": "English",
}

HOME: pathlib.Path = pathlib.Path.home() / "data" / "langs"
CACHE: pathlib.Path = getAppDataFilePath() / "lang_cache.txt"


class Language:
    def __init__(self):
        self._data: dict = {}
        self._fallback: dict = {}
        self._set_cursors: dict[str, int] = {}

    def _next_in_set(self, key_path: str, lines: list, loop: bool = True) -> str:
        idx = self._set_cursors.get(key_path, 0)
        line = lines[idx]
        if loop:
            self._set_cursors[key_path] = (idx + 1) % len(lines)
        else:
            self._set_cursors[key_path] = min(idx + 1, len(lines) - 1)
        return line

    def reset_set(self, key_path: str) -> None:
        """Reset a set's cursor back to the first line."""
        self._set_cursors.pop(key_path, None)

    @staticmethod
    def _load_lang_dir(lang_dir: pathlib.Path) -> dict:
        """
        Load all .json files from a language directory into a single namespaced dict.
        Each file is stored under its stem, e.g. dialogue.json -> data["dialogue"].
        """
        data = {}
        for json_file in sorted(lang_dir.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data[json_file.stem] = json.load(f)
        return data

    @staticmethod
    def detect_system(default_lang: str = "English") -> str | None:
        """
        Try to map the OS locale to one of your supported languages.
        Returns default_lang if no match is found.

        Expects supported_languages keys like "English", "German", "French".
        """

        LOCALE_MAP = {
            "en": "English",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "pl": "Polish",
            "ru": "Russian",
            "ja": "Japanese",
            "zh": "Chinese",
        }

        # noinspection PyBroadException
        try:
            lang_code, _ = locale.getlocale()  # e.g. "de_DE"
            if lang_code:
                prefix = lang_code.split("_")[0].lower()  # "de"
                detected = LOCALE_MAP.get(prefix)
                if detected and detected in LANGUAGES:
                    return detected
        except Exception:
            return default_lang
        return default_lang

    def load(self, lang: str, default_lang: str = "English") -> None:
        GOT_LANG: bool = False
        self._data = {}
        self._fallback = {}
        self._set_cursors = {}  # reset all cursors on every language load

        try:
            if lang not in LANGUAGES:
                lang = default_lang

            lang_dir = HOME / f"{LANGUAGES[lang]}"
            if not lang_dir.is_dir():
                raise FileNotFoundError(f"Language directory not found: {lang_dir}")

            self._data = self._load_lang_dir(lang_dir)

            if self._data:
                GOT_LANG = True
            else:
                sys.stderr.write(f"Language directory '{lang_dir}' is empty.\n")

        except FileNotFoundError:
            sys.stderr.write("File not found.\n")
        except json.decoder.JSONDecodeError:
            sys.stderr.write("lang JSON corrupted.\n")
        except Exception as e:
            sys.stderr.write(f"Error encountered. Error: {e}\n")

        if not GOT_LANG:
            if lang != default_lang:
                sys.stderr.write(f"Falling back to default language {default_lang}.\n")
                try:
                    fallback_dir = HOME / LANGUAGES[default_lang]

                    if not fallback_dir.is_dir():
                        raise FileNotFoundError(f"Fallback directory not found: {fallback_dir}")

                    self._fallback = self._load_lang_dir(fallback_dir)

                except (FileNotFoundError, json.JSONDecodeError):
                    sys.stderr.write("Fallback failed.\n")
            else:
                sys.stderr.write(
                    f"localizer: CRITICAL — default language '{default_lang}' failed to load. "
                    f"All translations will return [MISSING].\n"
                )
        sys.stderr.flush()

    def get(self, default_lang: str = "English", prompt_user: bool = True) -> None:
        if CACHE.exists():
            with open(CACHE, "r") as f:
                lang_choice = f.read().strip()
        else:
            if prompt_user:
                lang_choice = self.ask_user()
            else:
                lang_choice = default_lang

        self.load(lang=lang_choice, default_lang=default_lang)

    @staticmethod
    def ask_user() -> str:  # TODO: redo this when starting the ui
        while True:
            for lang in LANGUAGES:
                print(f"- {lang}")

            print()
            lang_choice = input("Select language: ")
            if lang_choice in LANGUAGES:
                getAppDataFilePath().mkdir(parents=True, exist_ok=True)
                with open(CACHE, "w") as f:
                    f.write(lang_choice)
                break
            else:
                sys.stderr.write(f"{lang_choice} is not a valid language.\n")
                sys.stderr.flush()
                print()
        return lang_choice

    # noinspection PyTypeChecker
    def t(self, key_path: str, nina: bool = False, loop: bool = True, **kwargs) -> str:
        """
        Get a translation, optionally interpolating named variables.
        Keys are dot seperated. e.g. t("game.player.has_died")

        Example JSON:  "greeting": "Hello, {name}! You have {count} messages."
        Usage:         t("greeting", name="Arthur", count=3)
        """
        keys = key_path.split(".")
        key_parts = set(keys)

        for source in (self._data, self._fallback):
            try:
                val = source
                for k in keys:
                    val = val[k]

                # --- list resolution ---
                if isinstance(val, list):
                    if "pools" in key_parts:
                        val = random.choice(val)
                    elif "sets" in key_parts:
                        val = self._next_in_set(key_path, val, loop=loop)
                    else:
                        return val

                # --- var interpolation ---
                if kwargs and isinstance(val, str):
                    try:
                        return val.format_map(kwargs)
                    except KeyError as e:
                        return f"[FORMAT ERROR in {key_path}: missing key {e}]"
                if nina:
                    prefix = self.t("ui.nina.full")
                    return f"{prefix}: {val}"

                return val

            except (KeyError, TypeError):
                continue
        return f"[MISSING]: {key_path}"

    def pt(self, key_path: str, n: int, **kwargs) -> str:
        """
        Get a pluralized translation.
        The key must point to a list: [singular_form, plural_form].
        """
        val = self.t(key_path)  # reuse existing lookup
        if not isinstance(val, list) or len(val) < 2:
            return f"[NOT_PLURAL]: {key_path}"
        form = val[0] if n == 1 else val[1]
        try:
            return form.format(n=n, **kwargs)
        except KeyError as e:
            return f"[FORMAT ERROR in {key_path}: missing {e}]"
