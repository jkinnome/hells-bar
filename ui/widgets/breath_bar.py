from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
import time


class BreathPhaseBar(Widget):
    """
    A countdown bar shown during the Breath Phase.
    Changes appearance based on game state.
    """
    DEFAULT_CSS = """
    BreathPhaseBar {
        height: 1;
        width: 100%;
        background: $surface-darken-1;
    }
    BreathPhaseBar.last-call {
        background: $error-darken-2;
    }
    """

    time_remaining: reactive[float] = reactive(15.0)
    total_time: reactive[float] = reactive(15.0)
    is_last_call: reactive[bool] = reactive(False)

    def render(self) -> Text:
        if self.total_time <= 0:
            return Text("")

        fraction = max(self.time_remaining / self.total_time, 0.0)
        width = self.size.width - 4
        filled = int(fraction * width)
        empty = width - filled

        if self.is_last_call:
            color = "bright_red"
            label = " LAST CALL "
        elif fraction > 0.5:
            color = "green"
            label = f" {self.time_remaining:.1f}s "
        elif fraction > 0.25:
            color = "yellow"
            label = f" {self.time_remaining:.1f}s "
        else:
            color = "red"
            label = f" {self.time_remaining:.1f}s "

        bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
        return Text.from_markup(f"{bar}{label}")
