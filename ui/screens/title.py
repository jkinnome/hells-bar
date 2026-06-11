from textual.screen import Screen
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.events import Key


class TitleScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static(id="bar-art")  # ASCII art reveal
        yield Static(id="nina-line")  # "Heya, welcome!/...oh. You again."
        yield Static(id="title-text")  # HELL'S BAR
        yield Static(id="press-any")  # [ press any key ]

    def on_mount(self) -> None:
        # Chain the animations with timers
        self.set_timer(0.1, self._start_art_reveal)

    async def _start_art_reveal(self) -> None:
        # Render the bar art character by character using Live or
        # a timed refresh loop with a growing substring
        ...

    async def on_key(self, event: Key) -> None:
        # Skip remaining animation, go to main menu
        # self.app.switch_screen(MainMenuScreen())
        pass
