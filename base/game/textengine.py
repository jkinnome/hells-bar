"""
TEXT ENGINE
PART OF JK'S CUSTOM LIBRARIES

Typewriter-style text engine with inline command support.
Supports sync (CLI/testing) and async (Textual) execution.

Created by JK
Copyright 2026
"""

from __future__ import annotations

import asyncio
import random
import re
import sys
import time
from collections.abc import Generator, Iterable
from typing import Callable

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

WriteFn = Callable[[str], None]
Action = tuple[str, object]  # e.g. ('write', '\n') or ('sleep', 0.5)


# ---------------------------------------------------------------------------
# TextEngine
# ---------------------------------------------------------------------------

# noinspection PyStringConversionWithoutDunderMethod,PyInvalidEscapeSequence,PyAttributeOutsideInit,dh
class TextEngine:
    """
    A typewriter-style text engine with inline command support.

    Architecture
    ------------
    Text is parsed into an abstract stream of *actions* by _iter_actions().
    The sync typewrite() method executes those actions with time.sleep().
    The async typewrite_async() method (on AsyncTextEngine) executes them
    with asyncio.sleep() — everything else is shared.

    Commands (embedded in strings with /(...) syntax)
    -------------------------------------------------
    Basic:
        /(^N)           — pause for N seconds
        /(spd:N)        — set typing speed to N seconds per character
        /(rst)          — reset speed to the instance default
        /(n)            — newline
        /(br)           — blank line  (double newline)
        /(t)            — tab
        /(clr)          — clear the dialogue / output  (via hook)

    Interaction / pacing:
        /(clk)          — wait for any keypress before continuing

    Audio / game hooks (wired up via set_*_hook):
        /(sfx:NAME)     — fire AudioManager sound effect
        /(mood:NAME)    — signal a Ninoula mood/MoodEngine transition
        /(glitch:N)     — trigger N corruption ticks on a CorruptableLabel

    Character effects:
        /(drunk:N)      — drunk typing for the next N characters
                          (random slurring: doubled chars, swapped case)
        /(hicc)         — hiccup  (stutter pause + optional sfx)
        /(slw)          — slow down speed by 50 %
        /(fst)          — speed up by 50 %

    Compound commands (left to right, separated by +):
        /(spd:0.01+^1)  — set speed then pause 1 s
        /(sfx:clink+^0.3+mood:happy)  — sound, pause, mood shift

    Rich markup (pass-through, written atomically):
        [bold], [red], [/], etc. are written instantly without typewriting
        them character by character.  The output target must support Rich
        markup (e.g. a Textual Static widget with markup=True).

    Custom commands
    ---------------
    Call register_command() with the inner body pattern (the part inside
    the /( ) brackets) and a factory that returns a list of Action tuples:

        engine.register_command(
            r'shake:(\d+)',
            lambda m: [('sfx', 'shake'), ('glitch', int(m.group(1)))]
        )

    Example
    -------
        engine = TextEngine(speed=0.03, pause_on={'.': 0.5, '?': 0.5})
        engine.typewrite("Hello,/(^1) [bold]World[/]!/(sfx:chime)")
    """

    # Splits on /(command) tokens AND [Rich markup] tags.
    _SPLIT_RE = re.compile(r'(/\([^)]*\)|\[[^\[\]]*])')

    class TextEngine:
        __slots__ = (
            'speed', 'pause_on', '_write_fn',
            '_current_speed', '_drunk_remaining',
            '_custom_commands',
            # Hook overrides (set via set_*_hook):
            '_on_sfx', '_on_mood', '_on_glitch', '_on_clear',
        )

    def __init__(
            self,
            speed: float = 0.025,
            pause_on: dict[str, float] | None = None,
            write_fn: WriteFn | None = None,
    ) -> None:
        self.speed = speed
        # noinspection PyUnresolvedReferences
        self.pause_on = (
                            sorted(pause_on.items(), key=lambda kv: len(kv[0]), reverse=True)
                        ) or {}
        self._write_fn = write_fn  # None → sys.stdout

        # Runtime state (reset per typewrite call)
        self._current_speed: float = speed
        self._drunk_remaining: int = 0

        # User-registered custom command parsers
        self._custom_commands: list[tuple[re.Pattern, Callable[[re.Match], list[Action]]]] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def _write(self, text: str) -> None:
        """Write text to the configured output (stdout or write_fn)."""
        if self._write_fn:
            self._write_fn(text)
        else:
            sys.stdout.write(text)
            sys.stdout.flush()

    def _write_char(self, ch: str, drunk_remaining: bool = False) -> None:
        """
        Write one character, applying the drunk effect when active.
        The drunk effect either doubles the character (slur) or swaps its
        case (stumble) at low random probability.
        """
        if drunk_remaining:
            self._drunk_remaining -= 1
            r = random.random()
            if r < 0.15:
                # Slur: write the character twice. The caller's sleep still
                # fires after this returns. slurred chars render slightly
                # slower than normal as a result.
                return
            if r < 0.25 and ch.isalpha():
                # Stumble: wrong case
                ch = ch.swapcase()
        self._write(ch)

    # ------------------------------------------------------------------
    # Command parsing → actions
    # ------------------------------------------------------------------

    def _parse_command(self, token: str) -> list[Action] | None:
        """
        Parse a /(…) token into a list of Action tuples.
        Returns None if the token is not a command.
        Handles compound commands like /(a+b+c) by splitting on '+'.
        """
        m = re.fullmatch(r'/\((.+)\)', token)
        if not m:
            return None

        inner = m.group(1)
        parts = inner.split('+') if '+' in inner else [inner]

        actions: list[Action] = []
        for part in parts:
            actions.extend(self._parse_single_command(part))
        return actions  # may be empty list if all parts were unknown

    def _parse_single_command(self, part: str) -> list[Action]:
        """
        Parse one command body (no '+') into a list of Action tuples.
        Unknown commands are silently ignored (empty list returned).
        Override this method in a subclass to add project-specific commands.
        """
        m: re.Match | None

        # /(^N) — pause
        if m := re.fullmatch(r'\^([\d.]+)', part):
            return [('sleep', float(m.group(1)))]

        # /(spd:N) — absolute speed
        if m := re.fullmatch(r'spd:([\d.]+)', part):
            return [('set_speed', float(m.group(1)))]

        # /(rst) — reset speed
        if part == 'rst':
            return [('set_speed', self.speed)]

        # /(slw) / /(fst) — relative speed
        if part == 'slw':
            return [('set_speed_rel', 1.5)]
        if part == 'fst':
            return [('set_speed_rel', 0.5)]

        # /(n) — newline
        if part == 'n':
            return [('write', '\n')]

        # /(br) — blank line
        if part == 'br':
            return [('write', '\n\n')]

        # /(t) — tab
        if part == 't':
            return [('write', '\t')]

        # /(clk) — wait for keypress
        if part == 'clk':
            return [('wait_key', None)]

        # /(clr) — clear output
        if part == 'clr':
            return [('clear', None)]

        # /(sfx:NAME)
        if m := re.fullmatch(r'sfx:(.+)', part):
            return [('sfx', m.group(1))]

        # /(mood:NAME)
        if m := re.fullmatch(r'mood:(.+)', part):
            return [('mood', m.group(1))]

        # /(glitch:N)
        if m := re.fullmatch(r'glitch:(\d+)', part):
            return [('glitch', int(m.group(1)))]

        # /(drunk:N)
        if m := re.fullmatch(r'drunk:(\d+)', part):
            return [('set_drunk', int(m.group(1)))]

        # /(hicc) — hiccup
        if part == 'hicc':
            return [('hicc', None)]

        # User-registered custom commands
        for pattern, factory in self._custom_commands:
            cm = pattern.fullmatch(part)
            if cm:
                return factory(cm)

        return []  # Unknown — silently skip

    # ------------------------------------------------------------------
    # Core generator — text → action stream
    # ------------------------------------------------------------------

    # noinspection PyTypeChecker,PyRedundantParentheses
    def _iter_actions(
            self,
            text: str,
            speed: float | None,
            pause_on: dict[str, float] | None,
    ) -> Generator[Action, None, None]:
        """
        Parse *text* and yield (action_type, value) pairs.
        The caller decides whether to execute them synchronously or with await.

        State-mutating actions (set_speed, set_drunk) are applied immediately
        inside this generator so that subsequent character yields reflect the
        updated state.
        """
        # noinspection PyTypeChecker
        current_speed: float = speed if speed is not None else self.speed
        drunk_remaining: int = 0
        active_pauses = pause_on if pause_on is not None else self.pause_on

        for token in self._SPLIT_RE.split(text):
            if not token:
                continue

            # Rich markup → emit atomically, do not typewrite char by char
            if re.fullmatch(r'\[[^\[\]]*]', token):
                yield ('write', token)
                continue

            # Command token
            actions = self._parse_command(token)
            if actions is not None:
                for a_type, a_val in actions:
                    if a_type == 'set_speed':
                        current_speed = float(a_val)
                    elif a_type == 'set_speed_rel':
                        current_speed *= float(a_val)
                    elif a_type == 'set_drunk':
                        drunk_remaining = int(a_val)
                    else:
                        yield (a_type, a_val)
                continue

            # Regular text — character by character, with pause_on support
            i = 0
            while i < len(token):
                paused = False
                # noinspection PyUnresolvedReferences
                for trigger, duration in active_pauses.items():
                    end = i + len(trigger)
                    if token[i:end] == trigger:
                        # Write the trigger as an atomic unit, then pause
                        yield ('write', trigger)  # doesn't decrement drunk remaining
                        yield ('sleep', duration)
                        i = end
                        paused = True
                        break
                if not paused:
                    yield ('write_char', token[i], drunk_remaining > 0)
                    if current_speed:
                        yield ('sleep', current_speed)
                    i += 1

    # ------------------------------------------------------------------
    # Sync action execution
    # ------------------------------------------------------------------

    def _execute_action(self, a_type: str, a_val: object) -> None:
        """Execute a single action synchronously."""
        if a_type == 'write':
            self._write(str(a_val))
        elif a_type == 'write_char':
            self._write_char(str(a_val), self._drunk_remaining > 0)
        elif a_type == 'sleep':
            d = float(a_val)  # type: ignore[arg-type]
            if d > 0:
                time.sleep(d)
        elif a_type == 'wait_key':
            self._do_wait_key()
        elif a_type == 'sfx':
            self._on_sfx(str(a_val))
        elif a_type == 'mood':
            self._on_mood(str(a_val))
        elif a_type == 'glitch':
            self._on_glitch(int(a_val))  # type: ignore[arg-type]
        elif a_type == 'hicc':
            self._do_hicc_sync()
        elif a_type == 'clear':
            self._on_clear()
        # Unknown action types are silently ignored.

    # ------------------------------------------------------------------
    # Built-in side effects
    # ------------------------------------------------------------------

    @staticmethod
    def _do_wait_key() -> None:
        """Block until any key is pressed. Cross-platform."""
        try:
            import msvcrt
            msvcrt.getch()
        except ImportError:
            import termios, tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _do_hicc_sync(self) -> None:
        """Hiccup: stutter pause, dash, recover pause, optional sfx."""
        time.sleep(0.15)
        self._write('- ')
        time.sleep(0.30)
        self._on_sfx('hiccup')

    # ------------------------------------------------------------------
    # Hooks — override or wire up via set_*_hook()
    # ------------------------------------------------------------------

    def _on_sfx(self, name: str) -> None:
        ...  # noqa: E701

    def _on_mood(self, name: str) -> None:
        ...  # noqa: E701

    def _on_glitch(self, n: int) -> None:
        ...  # noqa: E701

    def _on_clear(self) -> None:
        ...  # noqa: E701

    def set_sfx_hook(self, fn: Callable[[str], None]) -> None:
        """
        Wire AudioManager into /(sfx:NAME) and /(hicc) commands.

            engine.set_sfx_hook(audio_manager.play_sfx)
        """
        self._on_sfx = fn  # type: ignore[method-assign]

    def set_mood_hook(self, fn: Callable[[str], None]) -> None:
        """
        Wire MoodEngine into /(mood:NAME) commands.

            engine.set_mood_hook(ninoula.mood_engine.transition)
        """
        self._on_mood = fn  # type: ignore[method-assign]

    def set_glitch_hook(self, fn: Callable[[int], None]) -> None:
        """
        Wire a CorruptableLabel into /(glitch:N) commands.

            engine.set_glitch_hook(label.trigger_corruption)
        """
        self._on_glitch = fn  # type: ignore[method-assign]

    def set_clear_hook(self, fn: Callable[[], None]) -> None:
        """
        Wire a clear callback into /(clr) commands.

            engine.set_clear_hook(dialogue_box.clear)
        """
        self._on_clear = fn  # type: ignore[method-assign]

    # ------------------------------------------------------------------
    # Extension
    # ------------------------------------------------------------------

    def register_command(
            self,
            body_pattern: str,
            factory: Callable[[re.Match], list[Action]],
    ) -> None:
        """
        Register a custom command parser.

        body_pattern : regex for the command body (the text inside /(…))
        factory      : callable(match) → list of (action_type, value) pairs

        Supported action types you can yield:
            ('write',  str)    — write text atomically
            ('sleep',  float)  — pause N seconds
            ('sfx',    str)    — fire sfx hook
            ('mood',   str)    — fire mood hook
            ('glitch', int)    — fire glitch hook
            ('clear',  None)   — fire clear hook

        Example — /(shake:3) triggers 3 glitch ticks and plays a sound:
            engine.register_command(
                r'shake:(\d+)',
                lambda m: [('sfx', 'shake'), ('glitch', int(m.group(1)))]
            )
        """
        self._custom_commands.append((re.compile(body_pattern), factory))

    # ------------------------------------------------------------------
    # Public API (sync)
    # ------------------------------------------------------------------

    def typewrite(
            self,
            text: str,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
            add_newline: bool = True,
    ) -> None:
        """
        Print *text* character-by-character with inline command support.
        speed and pause_on fall back to instance defaults if not given.
        """
        for a_type, a_val in self._iter_actions(text, speed, pause_on):
            self._execute_action(a_type, a_val)
        if add_newline:
            self._write('\n')

    def typewrite_lines(
            self,
            lines: Iterable[str],
            gap: float = 0.4,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
    ) -> None:
        """Print a sequence of lines with a brief pause between each."""
        for line in lines:
            self.typewrite(line, speed=speed, pause_on=pause_on)
            time.sleep(gap)

    def prompt(
            self,
            text: str = '',
            speed: float | None = None,
            add_newline: bool = False,
    ) -> str:
        """Typewrite a prompt, then return the user's input via input()."""
        if text:
            self.typewrite(text, speed=speed, add_newline=add_newline)
        return input()


# ---------------------------------------------------------------------------
# AsyncTextEngine — for Textual / asyncio contexts
# ---------------------------------------------------------------------------

class AsyncTextEngine(TextEngine):
    """
    Async variant of TextEngine.

    Identical to TextEngine except:
    • typewrite_async() uses asyncio.sleep() instead of time.sleep()
    • _do_wait_key() is async (stub — override in your Textual widget to
      await a real key event)
    • _do_hicc_async() awaits instead of blocking

    Usage in Textual
    ----------------
    Wire write_fn to a widget callback, then run typewrite_async() inside a
    Textual worker.  See dialogue_widget.py for a ready-made widget.

        engine = AsyncTextEngine(speed=0.025, write_fn=my_widget.append_char)
        engine.set_sfx_hook(audio_manager.play_sfx)

        # Inside a Textual async worker:
        await engine.typewrite_async("Hello,/(^0.5) World!")
    """
    __slots__ = ()

    # ------------------------------------------------------------------
    # Async execution
    # ------------------------------------------------------------------

    async def _execute_action_async(self, a_type: str, a_val: object) -> None:
        """
        Execute a single action.  sleep and wait_key use asyncio so the
        Textual event loop is never blocked.  All other actions are sync-safe.
        """
        if a_type == 'sleep':
            d = float(a_val)  # type: ignore[arg-type]
            if d > 0:
                await asyncio.sleep(d)
        elif a_type == 'wait_key':
            await self._do_wait_key_async()
        elif a_type == 'hicc':
            await self._do_hicc_async()
        else:
            self._execute_action(a_type, a_val)

    @staticmethod
    async def _do_wait_key_async() -> None:
        """
        stub, gets overriden in ui
        """
        raise NotImplementedError("STUB")

    async def _do_hicc_async(self) -> None:
        """Async hiccup — non-blocking pauses."""
        await asyncio.sleep(0.15)
        self._write('— ')
        await asyncio.sleep(0.30)
        self._on_sfx('hiccup')

    # ------------------------------------------------------------------
    # Public API (async)
    # ------------------------------------------------------------------

    async def typewrite_async(
            self,
            text: str,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
            add_newline: bool = True,
    ) -> None:
        """
        Async version of typewrite().  Use this inside Textual workers or
        any asyncio context.  Never blocks the event loop.
        """
        for a_type, a_val in self._iter_actions(text, speed, pause_on):
            await self._execute_action_async(a_type, a_val)
        if add_newline:
            self._write('\n')

    async def typewrite_lines_async(
            self,
            lines: Iterable[str],
            gap: float = 0.4,
            speed: float | None = None,
            pause_on: dict[str, float] | None = None,
    ) -> None:
        """Async version of typewrite_lines()."""
        for line in lines:
            await self.typewrite_async(line, speed=speed, pause_on=pause_on)
            await asyncio.sleep(gap)


# ---------------------------------------------------------------------------
# Default pause table for Hell's Bar
# ---------------------------------------------------------------------------

pauses: dict[str, float] = {
    ',': 0.2,
    '!': 0.5,
    '.': 0.5,
    '?': 0.5,
    "'": 0.1,
}
