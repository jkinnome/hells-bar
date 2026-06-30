from textual.screen import Screen
from base.game.ninoula.ninoula import Ninoula
from base.game.eventbus import EventBus
from base.ui.widgets.corruption import CorruptableLabel


class GameScreen(Screen):
    def on_mount(self) -> None:
        self.nina = Ninoula(runs_played=self.app.persistence.runs_played)
        self.bus = EventBus()

    def compose(self):
        yield CorruptableLabel("BLOOD ALCOHOL CONTENT: ", id="bac-label")
        yield CorruptableLabel("Shot 1 | Shot 2 | Shot 3", id="shot-label")

    def update_corruption(self, player_bac: float):
        """As player gets drunker, increase corruption on all labels"""
        corruption = min(player_bac / 0.35, 1.0)  # max corruption at 0.35 BAC
        for label in self.query(CorruptableLabel):
            label.corruption_level = corruption
