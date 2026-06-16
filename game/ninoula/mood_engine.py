from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from game.state import GameState
from game.trinkets.manager import TrinketManager

if TYPE_CHECKING:
    from game.ninoula.emotion import EmotionState


class MoodSmug(Enum):
    IMPRESSED = auto()  # engaged, player doing well
    BORED = auto()  # player too cautious, time to liven things up


class MoodManic(Enum):
    JOYFUL = auto()  # drunk and delighted
    DESTRUCTIVE = auto()  # high tension, drunk and angry


class MoodIrritated(Enum):
    PISSED = auto()  # genuinely mad
    POUTY = auto()  # playfully mad


class MoodTipsy(Enum):
    SOFT = auto()  # vulnerable
    SLOPPY = auto()  # drunk, slurring, bad picks


class MoodGone(Enum):
    STUBBORN = auto()  # still fighting, won't lose
    SURRENDERED = auto()  # almost over, rare quiet lines, close to the ending


class Mood(Enum):
    SMUG = MoodSmug  # default , she's winning
    MANIC = MoodManic  # she got a bad shot, or is very drunk
    IRRITATED = MoodIrritated  # player pulled a trick on her
    TIPSY = MoodTipsy  # moderately drunk, loosening up
    GONE = MoodGone  # blackout drunk, she barely functions

    # noinspection PyStringConversionWithoutDunderMethod
    def __getattr__(self, name: str):
        if name.startswith("_"):  # guard against infinite recursion
            raise AttributeError(name)
        value = self.__dict__.get("_value_")
        if isinstance(value, type) and issubclass(value, Enum):
            try:
                return value[name]  # e.g. MoodSmug["BORED"]
            except KeyError:
                raise AttributeError(f"{self!r} has no attribute {name!r}")
        raise AttributeError(f"{self!r} has no attribute {name!r}")


@dataclass
class MoodState:
    base: Mood
    changed: bool
    sub: MoodGone | MoodManic | MoodTipsy | MoodSmug | MoodIrritated | None = None


class MoodEngine:
    """
    Gets Nina's mood from her EmotionState

    Uses emotional resistance so that moods don't flicker.
    A mood change requires a forced event or for the resistance to wear down (enough time passed in the new mood)
    """
    RESISTANCE_TURNS: int = 2  # turns to wait before natural mood transition

    def __init__(self):
        self._current: MoodState = MoodState(Mood.SMUG, changed=False)
        self._target: Mood = Mood.SMUG
        self._turns_at_target: int = 0
        self._trinket_mgr: TrinketManager = GameState.trinkets

    @property
    def current(self) -> MoodState:
        return self._current

    def evaluate(self, e: "EmotionState", force: bool = False) -> MoodState:
        """
        Evaluate and possibly update Nina's mood.

        Args:
            e: current EmotionState
            force: If True, override resistance and change immediately.
                   Only used for major events.

        Returns: the current MoodState after evaluation.
        """
        new_target = self._compute_target(e)

        if new_target != self._target:
            self._target = new_target
            self._turns_at_target = 0
        else:
            self._turns_at_target += 1

        should_transition: bool = (
                force
                or self._current.base != self._target
                and (
                        self._turns_at_target >= self.RESISTANCE_TURNS
                        or e.drunk_factor > 0.6  # drunk, less control
                        or e.mask_strength < 0.25  # mask is slipping
                )
        )

        if should_transition and self._current.base != self._target:
            new_sub = self._compute_sub(self._target, e)
            self._current = MoodState(
                base=self._current.base, sub=new_sub, changed=True
            )
        else:
            # Still re-evaluate substate
            new_sub = self._compute_sub(self._current.base, e)
            changed: bool = new_sub != self._current.sub
            self._current = MoodState(
                base=self._current.base, sub=new_sub, changed=changed
            )

        return self._current

    def force_mood(self, e: "EmotionState") -> MoodState:
        """Force an immediate mood transition (from card effect, etc.)."""
        return self.evaluate(e, force=True)

    # Private stuff

    @staticmethod
    def _compute_target(e: "EmotionState") -> Mood:
        """
        Priority-ordered mood target selection.
        First matching condition wins.
        """

        # Critical BAC thresholds — these override everything
        if e.bac >= 0.40:
            return Mood.GONE

        if e.bac >= 0.30 and e.tension > 0.60:
            return Mood.MANIC  # drunk + hostile = explosive

        if e.bac >= 0.30:
            return Mood.TIPSY

        # Engagement-driven mania: genuinely excited + moderately drunk
        if e.bac >= 0.18 and e.engagement > 0.80:
            return Mood.MANIC

        if e.bac >= 0.18:
            return Mood.TIPSY

        # Hostile/suspicious when sober
        if e.suspicion > 0.75 or e.tension > 0.72:
            return Mood.IRRITATED

        # Sober and engaged = SMUG (various substates)
        return Mood.SMUG

    def _compute_sub(self, base: Mood, e: "EmotionState") -> (MoodGone | MoodManic | MoodTipsy |
                                                              MoodSmug | MoodIrritated | None):
        """Compute substate from base mood and emotion variables."""
        match base:
            case Mood.SMUG:
                if e.engagement < 0.25 and not self._trinket_mgr.has("static_coat"):
                    return MoodSmug.BORED
                if e.respect > 0.65 and e.engagement > 0.50:
                    return MoodSmug.IMPRESSED
                return None

            case Mood.MANIC:
                if e.tension > 0.60:
                    return MoodManic.DESTRUCTIVE
                return MoodManic.JOYFUL

            case Mood.TIPSY:
                if e.affection > 0.2 and e.mask_strength < 0.50:
                    return MoodTipsy.SOFT  # mask down, affection present, she's genuine
                elif e.bac > 0.2:
                    return MoodTipsy.SLOPPY
                return None

            case Mood.GONE:
                if e.tension > 0.40:
                    return MoodGone.STUBBORN
                return MoodGone.SURRENDERED

            case Mood.IRRITATED:
                if e.affection > 0.65:
                    return MoodIrritated.POUTY  # a bit more cute and pouty if she likes you
                return MoodIrritated.PISSED

            case _:
                raise ValueError(f"This Mood does not exist: {base}")
