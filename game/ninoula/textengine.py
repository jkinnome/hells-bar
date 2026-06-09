"""
TEXT ENGINE
PART OF JK'S CUSTOM LIBRARIES

This library exists to make a simple text engine, that can typewrite and use commands.

Created by JK
Copyright 2026
"""

import re
import sys
import time
from collections.abc import Iterable
from typing import Callable


# removed all references to colorizer

class TextEngine:
    """
    A typewriter-style text engine with inline command support.

    Commands (embedded in strings):
        /(^N)      — pause for N seconds
        /(spd:N)   — change typing speed to N seconds per character
        /(rst)     — reset all styling and speed
        /(n)       — newline
        /(t)       — tabulator

    Example:
        engine = TextEngine(speed=0.03, pause_on={'.': 0.5, '...': 0.8})
        engine.typewrite("Hello,/(^1) World!")
    """

    def __init__(
            self,
            speed: float = 0.025,
            pause_on: dict[str, float] | None = None,
    ) -> None:
        self.speed = speed
        self.pause_on = pause_on or {}
        self._current_speed = speed
        self._commands = self._build_commands()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write(text: str) -> None:
        """Write to stdout and flush immediately."""
        sys.stdout.write(text)
        sys.stdout.flush()

    def _set_speed(self, new_speed: float) -> None:
        self._current_speed = new_speed

    def _build_commands(self):
        """
        Returns a list of (regex_pattern, handler) pairs.
        Add new commands here, typewrite() needs no changes.
        """
        return [
            (
                r'/\(\^([\d.]+)\)',  # Looks like: /(^N)
                lambda m: time.sleep(float(m.group(1)))
            ),
            (
                r'/\(spd:([\d.]+)\)',  # Looks like: /(spd:N)
                lambda m: self._set_speed(float(m.group(1)))
            ),
            (
                r'/\(rst\)',  # Looks like: /(rst)
                lambda m: self._set_speed(float(self.speed))
            ),
            (
                r'/\(n\)',  # Looks like: /(n)
                lambda m: self._write('\n')
            ),
            (
                r'/\(t\)',  # Looks like: /(t)
                lambda m: self._write('\t')
            ),
        ]

    def _handle_token(self, token: str) -> bool:
        """
        Try to match a token against all commands.
        Returns True if a command matched and was handled.
        """
        for pattern, handler in self._commands:
            m = re.fullmatch(pattern, token)
            if m:
                handler(m)
                return True
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # noinspection D
    def typewrite(
            self,
            text: str,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
            add_newline: bool = True
    ) -> None:
        """
        Print text character-by-character with inline command support.
        speed and pause_on fall back to instance defaults if not given.
        """
        self._current_speed = speed if speed is not None else self.speed
        active_pauses = pause_on if pause_on is not None else self.pause_on

        tokens = re.split(r'(/\([^)]+\))', text)

        for token in tokens:
            if self._handle_token(token):
                continue

            i = 0
            while i < len(token):
                paused = False
                for trigger, duration in active_pauses.items():
                    if token[i:i + len(trigger)] == trigger:
                        self._write(trigger)
                        time.sleep(duration)
                        i += len(trigger)
                        paused = True
                        break
                if not paused:
                    self._write(token[i])
                    if self._current_speed:
                        time.sleep(self._current_speed)
                    i += 1

        if add_newline:
            print()  # always exactly one newline

    def typewrite_lines(
            self,
            lines: Iterable[str],
            gap: float = 0.4,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
    ) -> None:
        """Print a list of lines with a pause between each."""
        for line in lines:
            self.typewrite(line, speed=speed, pause_on=pause_on)
            time.sleep(gap)

    def register_command(self, pattern: str, handler: Callable) -> None:
        """
        Register a custom inline command.
        pattern: regex string matching the full /(command) token
        handler: callable taking a re.Match object

        Example:
            engine.register_command(r'/\\(beep\\)', lambda m: print('\a', end=''))
        """
        self._commands.append((pattern, handler))

    def prompt(self, text: str = '', speed: float | None = None, add_newline: bool = False) -> str:
        """Typewrite a prompt, then return the user's input."""
        if text:
            self.typewrite(text, speed=speed, add_newline=add_newline)
        return input()


# --- Signs ---
pauses = {
    ',': 0.2,
    '!': 0.5,
    ".": 0.5,
    "?": 0.5,
    "'": 0.1
}
