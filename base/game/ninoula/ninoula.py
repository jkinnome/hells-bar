from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from base.game.ninoula.emotion import EmotionState
from base.game.ninoula.mood_engine import MoodEngine, MoodState, SubMood, Mood, MoodTipsy
from base.game.ninoula.pattern_tracker import PatternTracker, TurnRecord
from base.game.ninoula.shot_scorer import ShotScorer, ScoredShot
from base.game.ninoula.tell_generator import TellGenerator, ActiveTell

if TYPE_CHECKING:
    from base.game.state import GameState
    from base.game.shots import Alcohol, Rarity, Visibility


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
        self._mood_eng = MoodEngine(GameState.trinkets)
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
        immediate_moods: set[Mood] = {Mood.SMUG, Mood.IRRITATED}
        if self.mood.base in immediate_moods and self.emotion.drunk_factor < 0.4:
            self._already_decided = True

        # Set glass avoidance flag (generates "look away" tell)
        if self._last_scored and len(self._last_scored) > 1:
            worst_for_her = self._last_scored[-1]  # lowest score = avoids this
            if self._last_scored[0].score - worst_for_her.score > 20:
                self._avoiding_glass_idx = worst_for_her.index

    def decide(self,
               shots: list[Alcohol],
               player_picked_idx: int | None = None) -> NinaDecision:
        """
        Make Nina's final pick decision for the turn
        Call after begin_decision() and after the player has picked
        """
        # Forced pick from card effect (Challenge)
        if self._forced_pick_idx is not None:
            idx = self._forced_pick_idx
            self._forced_pick_idx = None
            tell = self._tells.generate(self)
            return NinaDecision(
                chosen_idx=idx,
                active_tells=tell,
                reasoning="forced_by_challenge_card",
                reaction_key="nina_accepts_challenge",
                forced_pick=True,
            )

        # Normal scoring pick (excluding player's glass)
        chosen = self._scorer.pick(
            shots, self.mood, self.emotion, self._pattern, player_picked_idx
        )

        # Check if prediction was right
        predicted = self._pattern.predict_player_pick(
            [i for i in range(len(shots)) if i != player_picked_idx]
        )
        self._prediction_correct = (
                predicted is None or predicted != player_picked_idx
        )

        # Determine reaction key from context
        reaction_key = self._classify_reaction(chosen, shots)

        # Generate tells
        tells = self._tells.generate(self)

        return NinaDecision(
            chosen_idx=chosen.index,
            active_tells=tells,
            reasoning=chosen.reasoning,
            reaction_key=reaction_key
        )

    @staticmethod
    def _classify_reaction(chosen: ScoredShot, shots: list[Alcohol]) -> str:
        """Classify what reaction line key to use after Nina picks."""
        shot = shots[chosen.index]
        abv = shot.abv
        hidden = True if shot.visibility == Visibility.Hidden else False

        if shot.rarity == Rarity.Sin:
            return "nina_picks_sin"
        if hidden:
            return "nina_picks_hidden"
        if abv >= 0.6:
            return "nina_picks_high_abv"
        if abv <= 0.14:
            return "nina_picks_low_abv"
        return "nina_picks_normal"

    # --- Player Turn Reactions ---

    def react_to_player_pick(
            self,
            shot: Alcohol,
            decision_ms: int,
            cards_played: list[str],
            round_number: int) -> str:
        """
        Process the player's pick. Updates Nina's emotion variables.
        Returns a reaction_key for the dialogue system.

        Before Nina's turn after player's turn.
        """
        abv = shot.abv
        hidden = True if shot.visibility == Visibility.Hidden else False

        # Record turn in pattern tracker
        position = 1  # TODO: add actual position tracking
        self._pattern.record_turn(TurnRecord(
            round_number=round_number,
            glass_position=position,
            decision_ms=decision_ms,
            alcohol_chosen=shot,
            was_hidden=hidden,
            cards_played=cards_played
        ))

        # Emotion variable updates from player choice
        reaction_key = "player_picks_normal"

        # Brave pick (high abv)
        if abv >= 0.55 and not hidden:
            self.emotion.shift_respect(0.06)
            self.emotion.shift_engagement(0.08)
            reaction_key = "player_picks_high_abv"

        # Cautious pick (low abv, third in a row)
        elif abv < 0.15 and self._pattern.current_low_streak >= 3:
            self.emotion.shift_engagement(-0.06)
            reaction_key = "low_streak"

        # Fast pick
        if decision_ms < 2000:
            self.emotion.shift_respect(0.03)
            reaction_key = reaction_key if reaction_key != "player_pick_normal" \
                else "fast_pick"

        # Sin glass
        if shot.rarity == Rarity.Sin:
            ...  # TODO: build sin dict

        # Trick cards
        trick_ids = {"palmed_switch", "cup_shuffle", "sleight_of_hand",
                     "doctored_glass", "fake_out"}
        if any(c in trick_ids for c in cards_played):
            self.emotion.shift_suspicion(0.12)
            self.emotion.shift_tension(0.08)

        # re-evalute mood after emotion update
        self._mood_eng.evaluate(self.emotion)

        return reaction_key

    def observe_trick_caught(self) -> str:
        """Call when a trick card is caught. Returns reaction key."""
        self.emotion.shift_suspicion(0.2)
        self.emotion.shift_tension(0.15)
        self.emotion.shift_affection(-0.05)
        self.emotion.shift_engagement(0.05)
        self.emotion.shift_respect(-0.05)
        self._mood_eng.evaluate(self.emotion, force=True)
        return "trick_caught"

    def observe_trick_succeeded(self) -> str:
        """Call when a trick card succeeds without detection."""
        # doesn't know but suspicion rises slightly
        self.emotion.shift_suspicion(0.02)
        return "trick_unnoticed"

    # --- Drinking ---

    def process_drink(self, shot: Alcohol) -> str:
        """
        Nina drinks a shot.
        Returns a reaction_key for the dialogue system.
        """
        self.emotion.drink(abv=shot.abv)

        force = shot.abv > 0.7
        sin = True if shot.rarity == Rarity.Sin else False
        self._mood_eng.evaluate(self.emotion, force=force or sin)

        # classify reaction
        if shot.abv >= 0.7:
            return "nina_drinks_very_high"
        if shot.abv >= 0.4:
            return "nina_drinks_high"
        if shot.abv >= 0.2:
            return "nina_drinks_medium"
        return "nina_drinks_low"

    # --- Chat System Hooks ---

    def apply_charm(self) -> float:
        """Player uses Charm. Returns affection delta applied"""
        # Diminishing returns at high affection
        base = 0.12 if self.emotion.bac > 0.15 else 0.07
        mult = 0.5 if self.emotion.affection >= 0.7 else 1.0
        # Silver Tongue modifier
        bonus = 0.12 if GameState.trinkets.has("silver_tongue") else 0.0
        delta = base * mult + bonus
        self.emotion.shift_affection(delta)
        self._mood_eng.evaluate(self.emotion)
        return delta

    def apply_taunt(self) -> tuple[str, float]:
        """
        Player taunts Nina.
        :return: (reaction_key, tension_delta)
        """
        if self.mood.base == Mood.SMUG:
            if self.emotion.tension < 0.4:
                self.emotion.shift_tension(0.12)
                self.emotion.shift_engagement(0.05)
                self._mood_eng.evaluate(self.emotion)
                return "taunt_lands_smug", 0.12
            else:
                # Already tense pushes to irritated
                self.emotion.shift_tension(0.18)
                self._mood_eng.evaluate(self.emotion, force=True)
                return "taunt_pushes_to_irritated", 0.18

        elif self.mood.base == Mood.MANIC:
            # Dangerous, pushes to MANIC.DESTRUCTIVE
            self.emotion.shift_tension(0.15)
            self._mood_eng.evaluate(self.emotion, force=True)
            return "taunt_manic_backfire", 0.15

        elif self.mood.base == Mood.TIPSY:
            self.emotion.shift_tension(0.08)
            self._mood_eng.evaluate(self.emotion)
            return "taunt_lands_tipsy", 0.08

        return "taunt_ignored", 0.0

    def apply_confess(self) -> tuple[str, float]:
        """
                Player confesses vulnerability.
                Returns (reaction_key, affection_delta).
                Rare soft response when Tipsy_Soft + high affection.
                """
        if (self.mood.base == Mood.TIPSY
                and self.mood.sub == MoodTipsy.SOFT
                and self.emotion.affection > 0.50
                and self.emotion.mask_strength < 0.45):
            delta = 0.18
            self.emotion.shift_affection(delta)
            return "confess_soft_response", delta

        delta = 0.08
        self.emotion.shift_affection(delta)
        return "confess_normal", delta

    def apply_silence(self) -> tuple[str, float, float]:
        """
        Player says nothing.
        :return: (reaction_key, affection_delta, tension_delta)
        """
        # Silence is intimate. Slightly raises affection, lowers tension
        self.emotion.shift_affection(0.05)
        self.emotion.shift_engagement(0.03)
        self.emotion.shift_tension(-0.04)
        self._mood_eng.evaluate(self.emotion)
        return "chat_silence", 0.05, -0.04

    # --- Dialogue Helpers ---

    def get_taunt(self, intensity: int = 1) -> str:
        """
        The key is passed to the dialogue system which selects the actual line.
        :return: a dialogue key for an impatience taunt
        """
        # Key format: "taunt_{mood_sug}_{intensity}"
        # Intensity: 1 = first taunt, 2 = second, 3+ = escalating
        return f"taunt_{self.mood.base}_{intensity}"

    def get_milestone_key(self, event_type: str) -> str:
        """Return dialogue key for a milestone event."""
        return f"milestone_{event_type}_{self.mood.base}"

    def describe_self(self) -> str:
        """Debug helper: human-readable summary of Nina's current state."""
        e = self.emotion
        return (
            f"Nina @ round mood={self.mood_name} "
            f"bac={e.bac:.3f} "
            f"aff={e.affection:.2f} ten={e.tension:.2f} "
            f"eng={e.engagement:.2f} res={e.respect:.2f} "
            f"sus={e.suspicion:.2f}"
        )

    # --- Serialisation ---

    def to_dict(self) -> dict:
        return {"emotion": self.emotion.to_dict()}

    @classmethod
    def from_dict(cls, d: dict, runs_played: int = 0) -> "Ninoula":
        nina = cls(runs_played=runs_played)
        if "emotion" in d:
            nina.emotion = EmotionState.from_dict(d["emotion"])
        return nina

    ...
