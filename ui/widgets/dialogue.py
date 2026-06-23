"""
DIALOGUE WIDGET
PART OF HELL'S BAR — TEXTUAL UI

A Textual widget that typewriters dialogue text character by character,
powered by AsyncTextEngine.  Supports Rich markup, inline commands, and
game hooks (sfx, mood, glitch).

Usage
-----
    class MyApp(App):
        def compose(self) -> ComposeResult:
            yield TypewriterDialogue(id="dialogue")

        def on_mount(self) -> None:
            dialogue = self.query_one(TypewriterDialogue)
            dialogue.set_sfx_hook(audio_manager.play_sfx)
            dialogue.set_mood_hook(ninoula.mood_engine.transition)
            dialogue.set_glitch_hook(corrupted_label.trigger_corruption)
            dialogue.say("Hello,/(^0.8) [bold red]welcome[/] to Hell's Bar.")
"""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from game.textengine import AsyncTextEngine, pauses


class TypewriterDialogue(Widget):
    """
    Dialogue box that types text one character at a time using AsyncTextEngine.

    Key features
    ------------
    • say(text)              — animate text (clears box first by default)
    • say_async(text)        — awaitable version for chaining dialogue
    • append(text)           — animate text, keeping what's already there
    • skip()                 — cancel animation, show full text immediately
    • clear()                — empty the dialogue box
    • set_*_hook(fn)         — wire audio / mood / glitch callbacks

    Rich markup in text is passed through atomically (not typewritten
    char by char), so [bold], [red], [/] etc. work as expected.

    The /(clk) command pauses the animation until the user presses any key
    via Textual's key handling (bound to the widget's on_key method).

    CSS variables used
    ------------------
    Inherits from your app theme.  Override DEFAULT_CSS or set inline styles.
    """

    DEFAULT_CSS = """
    TypewriterDialogue {
        height: auto;
        min-height: 5;
        padding: 1 2;
        border: solid $accent;
        background: $surface;
    }
    TypewriterDialogue #_tw_text {
        width: 100%;
    }
    """

    # The full text currently displayed in the box.
    _displayed: reactive[str] = reactive("", layout=True)

    def __init__(
            self,
            speed: float = 0.025,
            pause_on: dict[str, float] | None = None,
            **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._engine = AsyncTextEngine(
            speed=speed,
            pause_on=pause_on if pause_on is not None else pauses,
            write_fn=self._on_engine_write,
        )
        # Override the engine's async key-wait to use Textual events
        self._engine._do_wait_key_async = self._wait_for_key_event  # type: ignore[method-assign]

        self._buffer: list[str] = []  # character accumulation buffer
        self._full_text: str = ""  # original text for skip()
        self._key_event: asyncio.Event = asyncio.Event()

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("", id="_tw_text", markup=True)

    # ------------------------------------------------------------------
    # Reactive watcher — pushes buffer changes to the Static widget
    # ------------------------------------------------------------------

    def watch__displayed(self, value: str) -> None:
        self.query_one("#_tw_text", Static).update(value)

    # ------------------------------------------------------------------
    # Engine write callback
    # ------------------------------------------------------------------

    def _on_engine_write(self, text: str) -> None:
        """
        Called by AsyncTextEngine for every character or markup token.
        Runs inside an async Textual worker (main event loop), so reactive
        attribute updates are safe here.
        """
        self._buffer.append(text)
        self._displayed = "".join(self._buffer)

    # ------------------------------------------------------------------
    # Keypress handling for /(clk)
    # ------------------------------------------------------------------

    async def _wait_for_key_event(self) -> None:
        """
        Pauses the typewriter until the user presses any key.
        This replaces AsyncTextEngine's default _do_wait_key_async.
        """
        self._key_event.clear()
        await self._key_event.wait()

    def on_key(self) -> None:
        """Any keypress inside the widget unblocks a waiting /(clk)."""
        self._key_event.set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def say(
            self,
            text: str,
            speed: float | None = None,
            clear: bool = True,
    ) -> None:
        """
        Start typewriting *text* into the dialogue box.
        If clear=True (default) the box is emptied first.
        Safe to call from synchronous on_mount or event handlers.
        Any currently-running animation is canceled before starting.
        """
        self._full_text = text
        if clear:
            self._buffer.clear()
            self._displayed = ""
        self.run_worker(
            self._engine.typewrite_async(text, speed=speed, add_newline=False),
            exclusive=True,
            name="typewriter",
            group="typewriter",
        )

    async def say_async(
            self,
            text: str,
            speed: float | None = None,
            clear: bool = True,
    ) -> None:
        """
        Awaitable version of say().  Use this to chain lines of dialogue
        sequentially inside an async worker:

            async def ninoula_intro(self) -> None:
                d = self.query_one(TypewriterDialogue)
                await d.say_async("What'll it be, stranger?/(^0.5)")
                await d.say_async("We've got everything from Limbo Lager...")
                await d.say_async("...to the Pride Special./(sfx:thunder)")
        """
        self._full_text = text
        if clear:
            self._buffer.clear()
            self._displayed = ""
        await self._engine.typewrite_async(text, speed=speed, add_newline=False)

    def append(self, text: str, speed: float | None = None) -> None:
        """
        Typewrite *text* without clearing the existing content.
        Useful for continuing a sentence after a game event.
        """
        self.say(text, speed=speed, clear=False)

    def skip(self) -> None:
        """
        Cancel the running animation and display the full text immediately.
        The text is stripped of /(command) tokens but keeps Rich markup.
        """
        import re
        self.workers.cancel_group(self, "typewriter")
        clean = re.sub(r'/\([^)]*\)', '', self._full_text)
        self._buffer = [clean]
        self._displayed = clean

    def clear(self) -> None:
        """Empty the dialogue box and cancel any running animation."""
        self.workers.cancel_group(self, "typewriter")
        self._buffer.clear()
        self._displayed = ""

    # ------------------------------------------------------------------
    # Hook delegation — pass-through to the engine
    # ------------------------------------------------------------------

    def set_sfx_hook(self, fn) -> None:
        """Wire AudioManager: engine.set_sfx_hook(audio_manager.play_sfx)"""
        self._engine.set_sfx_hook(fn)

    def set_mood_hook(self, fn) -> None:
        """Wire MoodEngine: engine.set_mood_hook(ninoula.mood_engine.transition)"""
        self._engine.set_mood_hook(fn)

    def set_glitch_hook(self, fn) -> None:
        """Wire CorruptableLabel: engine.set_glitch_hook(label.trigger_corruption)"""
        self._engine.set_glitch_hook(fn)

    def set_clear_hook(self, fn) -> None:
        """Wire a clear callback: engine.set_clear_hook(self.clear)"""
        self._engine.set_clear_hook(fn)

    def register_command(self, body_pattern: str, factory) -> None:
        """Pass-through to AsyncTextEngine.register_command()."""
        self._engine.register_command(body_pattern, factory)
