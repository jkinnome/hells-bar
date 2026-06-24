from __future__ import annotations
import time
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from base.game.ninoula.emotion import EmotionState
from base.game.ninoula.mood_engine import MoodEngine, MoodState, SubMood, Mood
from base.game.ninoula.pattern_tracker import PatternTracker
from base.game.ninoula.shot_scorer import ShotScorer, ScoredShot
from base.game.ninoula.tell_generator import TellGenerator, ActiveTell

if TYPE_CHECKING:
    from base.game.state import GameState
    from base.game.eventbus import EventBus
    from base.game.shots import Alcohol


@dataclass
class NinaDecision:
    """
    The full output of Nina's decision for one turn.
    Contains everything the UI layer needs to know.
    """
    chosen_idx: int  # which glass she picks
    active_tells: list[ActiveTell]  # tells firing this turn (ui reads)
    reasoning: str  # internal debug/codex entry
    reaction_key: str  # key into dialogue pool
    forced_pick: bool = False  # True if an external effect forced


class Ninoula:
    """
    Nina AI

    Publick interface for game loop:
        decide() -> NinaDecision
        react_to_player() -> str (dialogue key)
        process_drink() -> str (dialogue key)
        update_emotion() -> None
        get_taunt() -> str
        get_milestone -> str | None
    """

    def __init__(self, runs_played: int = 0):
        self.emotion = EmotionState()
        self._mood_eng = MoodEngine()
        self._pattern = PatternTracker()
        self._scorer = ShotScorer()
        self._tells = TellGenerator()
        self._runs_played = runs_played

        # Internal flags read by TellGenerator
        self._already_decided: bool = False
        self._is_lying_this_turn: bool = False
        self._prediction_correct: bool = True
        self._avoiding_glass_idx: int | None = None
        self._forced_pick_idx: int | None = None  # set by challenge card

        # per turn tracking
        self._last_scored: list[ScoredShot] = []
        self._decision_start_time: float = 0.0

    # --- Core Properties ---

    @property
    def mood(self) -> MoodState:
        return self._mood_eng.current

    @property
    def mood_name(self) -> SubMood:
        return self._mood_eng.current.sub

    @property
    def bac(self) -> float:
        return self.emotion.bac

    # --- Decision Making ---

    def begin_decision(self, shots: list[Alcohol]) -> None:
        """
        Call at the start of Nina's thinking phase.
        Pre-computes scores so tells can during the animation.
        """
        self._decision_start_time = time.monotonic()
        self._already_decided = False
        self._is_lying_this_turn = False
        self._prediction_correct = True
        self._avoiding_glass_idx = None

        # Score all shots ahead of time
        self._last_scored = self._scorer.score_all(
            shots, self.mood, self.emotion, self._pattern, None
        )

        # Decide immediately in some moods (table tap tell)
        immediate_moods: set[Mood] = {Mood.SMUG, Mood.SMUG.IMPRESSED, Mood.IRRITATED}
        if self.mood in immediate_moods and self.emotion.drunk_factor < 0.4:
            self._already_decided = True

        # Set glass avoidance flag (generates "look away" tell)
        if self._last_scored and len(self._last_scored) > 1:
            worst_for_her = self._last_scored[-1]  # lowest score = avoids this
            if self._last_scored[0].score - worst_for_her.score > 20:
                self._avoiding_glass_idx = worst_for_her.index

    ...
