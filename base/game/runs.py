from enum import Enum, auto
from dataclasses import dataclass


class RunMemory(Enum):
    """
    If the run records data to Nina's permanent memory.
    Runs with no memory get a fresh Nina instead
    """
    MEMORY = True
    NO_MEMORY = False


class RunType(Enum):
    STANDARD = auto()
    EVENT = auto()
    CHALLENGE = auto()
