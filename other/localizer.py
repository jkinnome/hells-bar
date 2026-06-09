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
import pathlib
import sys


class Language:
    def __init__(self):
        self._lang: dict = {}
        self._fallback: dict = {}

    @staticmethod
    def detect_system(supported_languages: dict[str, str],
                      default_lang: str = "English") -> str | None:
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
                if detected and detected in supported_languages:
                    return detected
        except Exception:
            return default_lang
        return default_lang

    def load(self, lang: str,
             home_lang_file_directory: pathlib.Path,
             supported_languages: dict[str, str],
             default_lang: str = "English") -> None:
        GOT_LANG: bool = False
        self._lang = {}
        self._fallback = {}

        try:
            if lang not in supported_languages:
                lang = default_lang

            lang_path = home_lang_file_directory / f"{supported_languages[lang]}.json"
            with open(lang_path, "r", encoding="utf-8") as f:
                self._lang = json.load(f)
                GOT_LANG = True
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
                    fallback_path = home_lang_file_directory / f"{supported_languages[default_lang]}.json"
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        self._fallback = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    sys.stderr.write("Fallback failed.\n")
            else:
                sys.stderr.write(
                    f"localizer: CRITICAL — default language '{default_lang}' failed to load. "
                    f"All translations will return [MISSING].\n"
                )
        sys.stderr.flush()

    def get(self, home_lang_file_directory: pathlib.Path,
            cache_lang_file_directory: pathlib.Path,
            supported_languages: dict[str, str],
            default_lang: str = "English", prompt_user: bool = True) -> None:
        lang_path = cache_lang_file_directory / "lang.txt"

        if lang_path.exists():
            with open(lang_path, "r") as f:
                lang_choice = f.read().strip()
        else:
            if prompt_user:
                lang_choice = self.ask_user(cache_lang_file_directory, supported_languages)
            else:
                lang_choice = default_lang

        self.load(lang=lang_choice, home_lang_file_directory=home_lang_file_directory,
                  supported_languages=supported_languages, default_lang=default_lang)

    @staticmethod
    def ask_user(cache_lang_file_directory: pathlib.Path, supported_languages: dict[str, str], ) -> str:
        lang_path = cache_lang_file_directory / "lang.txt"

        while True:
            for lang in supported_languages:
                print(f"- {lang}")

            print()
            lang_choice = input("Select language: ")
            if lang_choice in supported_languages:
                cache_lang_file_directory.mkdir(parents=True, exist_ok=True)
                with open(lang_path, "w") as f:
                    f.write(lang_choice)
                break
            else:
                sys.stderr.write(f"{lang_choice} is not a valid language.\n")
                sys.stderr.flush()
                print()
        return lang_choice

    def t(self, key_path: str, **kwargs) -> str:
        """
        Get a translation, optionally interpolating named variables.
        Keys are dot seperated. e.g. t("game.player.has_died")

        Example JSON:  "greeting": "Hello, {name}! You have {count} messages."
        Usage:         t("greeting", name="Arthur", count=3)
        """
        keys = key_path.split(".")

        for source in (self._lang, self._fallback):
            try:
                val = source
                for k in keys:
                    val = val[k]
                if kwargs and isinstance(val, str):
                    try:
                        return val.format_map(kwargs)
                    except KeyError as e:
                        return f"[FORMAT ERROR in {key_path}: missing key {e}]"
                # noinspection PyTypeChecker
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
