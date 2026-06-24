# game/persistence/stats.py
from __future__ import annotations

from dataclasses import dataclass, field

from base.game.state import RunStats, RunOutcome


@dataclass
class AllTimeStats:
    """Persists across all runs. Updated at end of each run."""
    total_runs: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_draws: int = 0
    total_abandoned: int = 0

    total_shots_drunk: int = 0
    total_bac_consumed: float = 0.0
    total_spite_generated: int = 0
    total_rounds: int = 0
    total_combos: int = 0

    highest_bac_reached: float = 0.0
    highest_abv_survived: float = 0.0
    highest_abv_name: str = ""
    longest_run_rounds: int = 0

    favorite_drink: str = ""  # most frequently chosen drink
    drink_counts: dict = field(default_factory=dict)

    times_nina_manic_at_loss: int = 0
    times_nina_gone_at_loss: int = 0
    times_tricked_successfully: int = 0
    times_caught_cheating: int = 0

    # Nina tracking
    times_nina_used_name: int = 0  # tracked per-run, accumulated
    nina_final_moods: dict = field(default_factory=dict)

    # Codex completion
    drinks_discovered: set = field(default_factory=set)  # set of drink names
    codex_nina_entries: int = 0

    @property
    def win_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.total_wins / self.total_runs

    def record_run(self, stats: RunStats, outcome: RunOutcome) -> None:
        self.total_runs += 1
        self.total_rounds += stats.rounds_survived
        self.total_shots_drunk += stats.shots_drunk
        self.total_bac_consumed += stats.total_bac_consumed
        self.total_spite_generated += stats.spite_generated
        self.total_combos += stats.combos_triggered

        if outcome == RunOutcome.PLAYER_WIN:
            self.total_wins += 1
        elif outcome == RunOutcome.PLAYER_LOSS:
            self.total_losses += 1
        elif outcome == RunOutcome.MUTUAL_DRAW:
            self.total_draws += 1
        elif outcome == RunOutcome.ABANDONED:
            self.total_abandoned += 1

        if stats.highest_abv_drunk > self.highest_abv_survived:
            self.highest_abv_survived = stats.highest_abv_drunk
            self.highest_abv_name = stats.highest_abv_name

        self.longest_run_rounds = max(self.longest_run_rounds, stats.rounds_survived)

        mood = stats.nina_final_mood
        self.nina_final_moods[mood] = self.nina_final_moods.get(mood, 0) + 1
