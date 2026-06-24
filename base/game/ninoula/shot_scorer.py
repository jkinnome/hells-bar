from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
import random
if TYPE_CHECKING:
    from base.game.ninoula.emotion import EmotionState
    from base.game.ninoula.mood_engine import Mood, MoodState, MoodSmug
    from base.game.ninoula.pattern_tracker import PatternTracker
    from base.game.shots import Alcohol
    import base.game.shots as glass


@dataclass
class ScoredShot:
    index: int
    score: float
    reasoning: str  # human-readable, used in TellGenerator and debug


class ShotScorer:
    """
    Scores available shots from Nina's perspective.

    Core: Nina has a strategy that degrades with BAC,
    modified by her emotional state. Introduces biases (becomes overconfident,
    misjudges hidden shots and becomes more impulsive).
    """

    SIN_GLASS_AVOIDANCE: dict[Alcohol, float] = {
        # Meanings:
        #   = -999.0: Cannot drink ever.
        #   > -999.0: Can drink if Gone.
        #   > 0     : Can drink normally, but with lower chance.
        #   >= 33.3 : Equal/above equal chance to drink.
        glass.shot_pride: -999.0,
        glass.shot_greed: -999.0,
        glass.shot_lust: -200.0,
        glass.shot_wrath: 45.0,  # bonus
        glass.shot_gluttony: 33.3,  # treated as regular shot
        glass.shot_sloth: -999.0,
        glass.shot_envy: 11.1,
        glass.shot_caina: -999.0,
        glass.shot_fraud: 33.3,
        glass.shot_treachery: -777.0,
    }

    def score_all(self,
                  shots: list[Alcohol],
                  mood: "MoodState",
                  emotion: "EmotionState",
                  pattern: "PatternTracker",
                  player_picked_idx: int | None) -> list[ScoredShot]:
        """
        Score all available (not picked) shots.

        Args:
            shots:  Full table of shots (may include player's pick)
            mood:   current mood state
            emotion: current emotion vars
            pattern: Player pattern tracker
            player_picked_idx: Index of shot player already picked (exlcude from pool)

        Returns list of ScoredShot sorted best-first.
        """
        available = [
            (i, s) for i, s in enumerate(shots)
            if i != player_picked_idx
        ]

        scored = []
        for idx, shot in available:
            score, reason = self._score_shot(
                idx, shot, mood, emotion, pattern, available
            )
            scored.append(ScoredShot(index=idx, score=score, reasoning=reason))

        # Sort best-first
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def pick(self,
             shots: list[Alcohol],
             mood: "MoodState",
             emotion: "EmotionState",
             pattern: "PatternTracker",
             player_picked_idx: int | None = None) -> ScoredShot:
        """
        Pick one shot. High scoring shots are preferred but not guaranteed
        noise increases with BAC and decreses with respect for player
        (she plays better when she thinks you're good)
        """
        scored = self.score_all(shots, mood, emotion, pattern, player_picked_idx)
        if not scored:
            # Fallback, shouldn't happen normally
            idx = 0 if player_picked_idx != 0 else 1
            return ScoredShot(index=idx, score=0.0, reasoning='fallback')

        return self._weighted_pick(scored, emotion)

    # --- Private ---

    # noinspection PyUnresolvedReferences
    def _score_shot(self,
                    idx: int,
                    shot: Alcohol,
                    mood: "MoodState",
                    emotion: "EmotionState",
                    pattern: "PatternTracker",
                    available: list[tuple], ) -> tuple[float, str]:
        """Return (score, reasoning) for one shot."""

        is_sin = shot.rarity == glass.Rarity.Sin
        is_hidden = shot.visibility == glass.Visibility.Hidden
        abv = shot.abv if not is_hidden else None
        tags = set(shot.flavor_tags)

        # Sin
        if is_sin and mood.base != Mood.GONE:
            return self.SIN_GLASS_AVOIDANCE.get(shot, -999.0), f"sin_{shot.name}"
        elif is_sin and mood.base == Mood.GONE:
            return self.SIN_GLASS_AVOIDANCE.get(shot, 25.0) + 998.0, f"gone_sin_{shot.name}"

        # Base score by mood
        base_score = 0.0
        reason = ""

        if mood.base == Mood.SMUG and mood.sub != MoodSmug.BORED:
            # Strategic: minimize own BAC
            if is_hidden:
                # unknown risk
                base_score -= 5.0
                reason = "smug_avoid_hidden"
            else:
                # Lower ABV = safe
                base_score += 50.0 - (abv * 100)
                reason = f"smug_safe(abv={abv})"

        elif mood.base == Mood.SMUG.BORED:
            # Bored, picks middle option
            if is_hidden:
                base_score += 10.0
                reason = "bored_hidden_interesting"
            else:
                # Prefer moderate ABV
                base_score += 30.0 - abs((abv * 100) - 30)
                reason = f"bored_moderate(abv={abv})"

        elif mood.base == Mood.MANIC:
            # Chaos
            if is_hidden:
                base_score += 40.0
                reason = "manic_loves_unknown"
            else:
                base_score = abv * 100  # rav abv as score
                reason = f"manic_high_abv(abv={abv})"

        elif mood.base == Mood.IRRITATED:
            # Reactive, predict what player wants and take it
            predicted_player_pick = pattern.predicted_player_pick(
                [i for i, _ in available]
            )
            if predicted_player_pick == idx:
                # Take what player wants
                base_score += 60.0
                reason = "irritated_deny_player"
            elif is_hidden:
                base_score -= 10.0
                reason = "irritated_avoid_unknown"
            else:
                base_score += 50.0 - (abv * 100)  # still strategic
                reason = f"irritated_strategic(abv={abv})"

        elif mood.base == Mood.TIPSY:
            # degraded thinking
            if is_hidden:
                base_score = 0.0
                reason = "tipsy_neutral_unknown"
            else:
                base_score = 40.0 - (abv * 100) * 0.6  # less weight on ABV
                reason = f"tipsy_degraded(abv={abv})"

        elif mood.base == Mood.GONE:
            # nearly random
            base_score += 10.0 if not is_sin else 0.0
            reason = f"gone_random"

        # Modifiers

        # Respect: high respect = plays harder
        # Applied in _weighted_pick
        # treats hidden shots differently
        if not is_hidden and emotion.respect > 0.65 and mood.base == Mood.SMUG:
            # more careful about avoiding specific shots
            if "Demon" in tags or "Cursed" in tags:
                base_score -= 20.0
                reason += "+respect_avoids_cursed"

        # Engagement: bored Nina is slightly random
        if emotion.engagement < 0.3:
            base_score += random.uniform(-8, 8)
            reason += "+boredom_noise"

        # Suspicion: avoids the glass she thinks the player is making her pick
        if emotion.suspicion > 0.6:
            predicted = pattern.predicted_player_pick([i for i, _ in available])
            if predicted is not None:
                # avoids the shot
                non_predicted = [i for i, _ in available if i != predicted]
                if non_predicted and idx in non_predicted:
                    base_score += 8.0
                    reason += "+sus"

        # Favoritism
        # Loves Hellfire and hates Bittersoul
        if not is_hidden:
            if shot == glass.shot_hellfire:
                base_score += 50.0
                reason += "+loves_hellfire"
            elif shot == glass.shot_bittersoul:
                base_score -= 50.0
                reason += "+hates_bittersoul"

        return base_score, reason

    @staticmethod
    def _weighted_pick(scored: list[ScoredShot],
                       emotion: "EmotionState") -> ScoredShot:
        """
        Select from scored shots with noise proportional
        to BAC and inverse to respect.

        Low BAC + high respect = highest score pick
        High BAC + low respect = basically random
        """
        if len(scored) == 1:
            return scored[0]

        # noise increases with drunk_factor
        # decreases with respect
        noise = emotion.drunk_factor * 0.7 - emotion.respect * 0.2
        noise = max(0.0, min(noise, 0.85))

        # deterministic: sober + respectful = best shot
        if noise < 0.08:
            return scored[0]

        # Weight shots by score
        # noise pulls toward uniform distribution
        min_score = min(s.score for s in scored)
        # shift all scores to be positive for weighting
        shifted = [s.score - min_score + 1.0 for s in scored]
        # blend with uniform (noise)
        uniform = 1.0 / len(scored)
        weights = [
            (1 - noise) * (s / sum(shifted)) + noise * uniform
            for s in shifted
        ]

        # weighted random.choice
        pick = random.choices(scored, weights=weights, k=1)[0]
        return pick
