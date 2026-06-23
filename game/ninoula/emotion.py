"""
Base Moods          Sub-States
──────────          ──────────
SMUG           ->   SMUG            (normal)
               ->   SMUG.IMPRESSED  (respect > 0.6, engagement > 0.5)
               ->   SMUG.BORED      (engagement < 0.25)

MANIC          ->   MANIC             (normal)
               ->   MANIC.JOYFUL      (affection > 0.4 or engagement > 0.7)
               ->   MANIC.DESTRUCTIVE (tension > 0.6)

TIPSY          ->   TIPSY           (normal)
               ->   TIPSY.SOFT      (affection > 0.5, bac 0.20–0.30)
               ->   TIPSY.SLOPPY    (bac > 0.30)

IRRITATED      ->   IRRITATED        (normal)
               ->   IRRITATED.PISSED (ADD HERE)
               ->   IRRITATED.POUTY  (ADD HERE)

GONE           ->   GONE             (normal)
               ->   GONE.STUBBORN    (tension > 0.4)
               ->   GONE.SURRENDERED (tension <= 0.4)
"""

# game/ninoula/emotion.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmotionState:
    """
    All of Nina's emotional / physiological variables.
    Kept separate from Ninoula so it can be serialized cleanly.

    All float fields are clamped to [0, 1] except bac [0, 0.5].
    Use the provided helpers rather than setting values directly.
    """

    # Core
    bac: float = 0.0  # Blood alcohol content [0, 0.5]

    # Persistent cross-run relationship state
    adoration: float = 0.0  # <- affection
    grudge: float = 0.0  # <- tension
    fascination: float = 0.0  # <- engagement
    admiration: float = 0.0  # <- respect
    wariness: float = 0.0  # <- suspicion (clean slate every run, but she still watches out for you)

    # Relationship axes
    affection: float = 0.10  # Slight baseline warmth to start
    tension: float = 0.05  # Very slight baseline wariness

    # Run-state axes
    engagement: float = 0.50  # Neutral to start, rises quickly if run is interesting
    respect: float = 0.20  # Slight baseline disrespect (you're a mortal, after all)
    suspicion: float = 0.00  # Clean slate every run

    # Internal tracking (not serialized as emotion variables)
    last_abv: float = 0.0  # ABV of the last shot Nina drank
    turns_in_current_mood: int = 0  # How many turns at this mood (resistance tracking)

    # --- Helpers ---
    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))

    def shift_affection(self, delta: float) -> None:
        self.affection = self._clamp(self.affection + delta)

    def shift_tension(self, delta: float) -> None:
        self.tension = self._clamp(self.tension + delta)

    def shift_engagement(self, delta: float) -> None:
        self.engagement = self._clamp(self.engagement + delta)

    def shift_respect(self, delta: float) -> None:
        self.respect = self._clamp(self.respect + delta)

    def shift_suspicion(self, delta: float) -> None:
        self.suspicion = self._clamp(self.suspicion + delta)

    def drink(self, abv: float) -> None:
        """Process Nina drinking. Updates BAC and shifts engagement."""
        bac_gain = abv * 0.004
        self.bac = self._clamp(self.bac + bac_gain, lo=0.0, hi=0.50)
        self.last_abv = abv

        # Interesting drinks raise engagement; weak ones lower it
        if abv >= 0.5:
            self.shift_engagement(+0.08)
        elif abv >= 0.3:
            self.shift_engagement(+0.03)
        elif abv < 0.1:
            self.shift_engagement(-0.06)

    @property
    def drunk_factor(self) -> float:
        """0 = sober, 1 = maximum drunk. Used for noise scaling."""
        return self._clamp(self.bac / 0.40)

    @property
    def mask_strength(self) -> float:
        """
        How well Nina can maintain her composed performance.
        High when tense + sober. Low when drunk + high affection.
        """
        sobriety = 1.0 - self.drunk_factor
        guarded = self.tension * 0.4
        openness = self.affection * 0.3
        return self._clamp(sobriety + guarded - openness)

    def to_dict(self) -> dict:
        return {
            "bac": self.bac, "affection": self.affection,
            "tension": self.tension, "engagement": self.engagement,
            "respect": self.respect, "suspicion": self.suspicion,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EmotionState":
        return cls(**{k: v for k, v in d.items()
                      if k in cls.__dataclass_fields__})
