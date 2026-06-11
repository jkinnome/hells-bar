from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel


class BACMeter(Widget):
    """Blood Alcohol Content meter for player and Ninoula."""

    player_bac: reactive[float] = reactive(0.0)
    ninoula_bac: reactive[float] = reactive(0.0)

    MAX_BAC = 0.45

    def render(self) -> Panel:
        def make_bar(bac: float, label: str) -> str:
            pct = min(bac / self.MAX_BAC, 1.0)
            filled = int(pct * 18)
            bar = "█" * filled + "░" * (18 - filled)

            if pct < 0.4:
                color = "green"
            elif pct < 0.7:
                color = "yellow"
            else:
                color = "red"

            return f"{label:10} [{color}]{bar}[/{color}] {bac:.3f}"

        content = (
                make_bar(self.player_bac, "You") + "\n" +
                make_bar(self.ninoula_bac, "Ninoula")
        )
        return Panel(content, title="BAC", border_style="bright_cyan")

    def drink(self, who: str, abv: float) -> None:
        """Called when someone drinks. Triggers re-render automatically."""
        if who == "player":
            self.player_bac = min(self.player_bac + abv * 0.005, self.MAX_BAC)
        else:
            self.ninoula_bac = min(self.ninoula_bac + abv * 0.005, self.MAX_BAC)
