import random
from enum import Enum, auto


class MoodSmug(Enum):
    WINNING = auto()  # normal
    IMPRESSED = auto()  # engaged, player doing well
    BORED = auto()  # player too cautious, time to liven things up


class MoodManic(Enum):
    JOYFUL = auto()  # drunk and delighted
    DESTRUCTIVE = auto()  # high tension, drunk and angry


class MoodTipsy(Enum):
    SOFT = auto()  # vulnerable
    SLOPPY = auto()  # drunk, slurring, bad picks


class MoodGone(Enum):
    STUBBORN = auto()  # still fighting, won't lose
    SURRENDERED = auto()  # almost over, rare quiet lines, close to the ending


class Mood(Enum):
    SMUG = MoodSmug  # default , she's winning
    MANIC = MoodManic  # she got a bad shot, or is very drunk
    IRRITATED = auto()  # player pulled a trick on her
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


class Ninoula:
    def __init__(self):
        self.name: str = "Ninoula"
        self.mood = Mood.SMUG.WINNING
        self.suspicion: float = 0.0  # how much she suspects player of cheating
        self.affection: float = 0.5  # how much she "likes" the player right now
        self.bac: float = 0.0
        self._turn_count: int = 0

    def drink(self, abv: float) -> str:
        """Process Ninoula drinking. Returns her reaction dialogue"""
        bac_gained = abv * 0.004
        self.bac = min(self.bac + bac_gained, 0.50)
        self._turn_count += 1
        self._update_mood()
        return self._reaction_to_drink(abv)

    def _update_mood(self):  # WILL PROBABLY CHANGE
        if self.bac >= 0.35:
            self.mood = Mood.GONE
        elif self.bac > 0.22:
            self.mood = Mood.TIPSY if random.random() > 0.3 else Mood.MANIC
        elif self.suspicion > 0.7:
            self.mood = Mood.IRRITATED
        elif self.affection > 0.7:
            self.mood = Mood.MANIC
        else:
            self.mood = Mood.SMUG

    def _reaction_to_drink(self, abv: float) -> str:
        ...
        # TODO: update this when all dialogue is added in the JSON file
