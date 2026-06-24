from textual.screen import Screen

from base.game.corruption import CorruptableLabel


class GameScreen(Screen):
    def compose(self):
        yield CorruptableLabel("BLOOD ALCOHOL CONTENT: ", id="bac-label")
        yield CorruptableLabel("Shot 1 | Shot 2 | Shot 3", id="shot-label")

    def update_corruption(self, player_bac: float):
        """As player gets drunker, increase corruption on all labels"""
        corruption = min(player_bac / 0.35, 1.0)  # max corruption at 0.35 BAC
        for label in self.query(CorruptableLabel):
            label.corruption_level = corruption
