from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

if TYPE_CHECKING:
    from game.shots import Alcohol


class ShotGlass(Widget):
    revealed: reactive[bool] = reactive(False)

    def __init__(self, shot: Alcohol, **kwargs):
        super().__init__(**kwargs)
        self.shot = shot

    def render(self) -> Text:
        ...


# SIN GLASS
SIN_BORDER_CHARS = ["╔", "█", "▓", "░", "╗", "║", "╚", "╝"]


class SinGlass(ShotGlass):
    """
    A Sin-rarity shot glass.
    Flickers between its real border and solid blocks.
    Label always reads [SIN] until revealed on drink.
    """
    DEFAULT_CSS = """
    SinGlass {
        border: heavy $error;
        color: $error;
        background: $surface-darken-3;
    }
    """

    def on_mount(self) -> None:
        # Flicker timer — alternates border style rapidly
        self.set_interval(0.4, self._flicker)

    def _flicker(self) -> None:
        self.toggle_class("sin-flicker")

    def render(self) -> Text:
        if not self.revealed:
            return Text.from_markup("[bold red][ SIN ][/bold red]\n[dim]█████████[/dim]")
        # reveal on drink — normal render
        return super().render()
