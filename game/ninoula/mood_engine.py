from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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
                return value[name]  # e.g. MoodSmug["WINNING"]
            except KeyError:
                raise AttributeError(f"{self!r} has no attribute {name!r}")
        raise AttributeError(f"{self!r} has no attribute {name!r}")


@dataclass
class MoodState:
    base: Mood
    sub: MoodGone | MoodManic | MoodTipsy | MoodSmug | MoodIrritated
    changed: bool
