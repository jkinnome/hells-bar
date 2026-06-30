"""
CORRUPTION
PART OF JK'S CUSTOM LIBRARIES

CorruptableLabel — a Textual widget that visually degrades text to signify
intoxication. See corruption.md for the full design spec this implements.

Created by JK
Copyright 2026
"""

from __future__ import annotations

import random

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

# ---------------------------------------------------------------------------
# Glitch character pool & tiers
# ---------------------------------------------------------------------------

GLITCH_CHARS: str = (
    "█▓▒░▄▀■□▇▁▪◆◇※@#$€¥£§%&?!°_†ƒŒ‡‰•š™œžŸ¢¡¤¦©®¬±×+-*÷~µ¶ÆÇØþ⁇⁂‖⁜∑⊠╳✪"
    "☙☟☺☻♥♡♠♣♦⛶⛤⛧▯⯑⍰︙⸮★⦀☾⚝✟✶☉ᛜ✠🝍🜅🜆🜋☲🜂⚘⸎〄ꝏℌℜ℣⌘𐀶𐃯𐄘𐄪𐄹☊☋ꙮ"
)

# Tier N unlocks GLITCH_CHARS[:N/4 * len(GLITCH_CHARS)] — higher BAC/corruption
# unlocks a larger, "weirder" slice of the character pool.
GLITCH_CHARS_T1: str = GLITCH_CHARS[:int(1 / 4 * len(GLITCH_CHARS))]
GLITCH_CHARS_T2: str = GLITCH_CHARS[:int(2 / 4 * len(GLITCH_CHARS))]
GLITCH_CHARS_T3: str = GLITCH_CHARS[:int(3 / 4 * len(GLITCH_CHARS))]
GLITCH_CHARS_T4: str = GLITCH_CHARS  # all characters

_TIER_CHARS: dict[int, str] = {
    1: GLITCH_CHARS_T1,
    2: GLITCH_CHARS_T2,
    3: GLITCH_CHARS_T3,
    4: GLITCH_CHARS_T4,
}

GLITCH_COLORS: list[str] = ["dim", "red", "bright_red", "dark_red", "magenta"]

# ---------------------------------------------------------------------------
# Corruption types (per-character)
# ---------------------------------------------------------------------------

NONE_ = 0  # not corrupted
FLICKER = 1  # 15% chance per render to show corrupted
PARTIAL = 2  # 50% chance per render to show corrupted
STATIC = 3  # permanently replaced with one fixed glitch character
CYCLE = 4  # always corrupted, re-rolls its glitch character every render

_FLICKER_CHANCE = 0.15
_PARTIAL_CHANCE = 0.50
_RENDER_INTERVAL = 0.1  # seconds, matches the ~0.1s rerender cadence in the spec

# Roll thresholds for *how* a corrupted character is displayed, per spec:
#   1. stays but dimmed
#   2. replaced with a glitch char, no color bleed
#   3. replaced with a glitch char, color bleeds
_DIM_THRESHOLD = 1 / 3
_PLAIN_GLITCH_THRESHOLD = 2 / 3


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def tier_for_level(corruption_level: float) -> int:
    """Map a 0.0-1.0 corruption level to a tier (0-4) unlocking glitch chars."""
    level = _clamp(corruption_level)
    if level <= 0:
        return 0
    return min(4, int(level * 4) + 1)


def glitch_chars_for_level(corruption_level: float) -> str:
    """The pool of glitch characters available at the given corruption level."""
    tier = tier_for_level(corruption_level)
    return _TIER_CHARS.get(tier, GLITCH_CHARS_T1)


def corrupted_fraction(corruption_level: float) -> float:
    """
    How much of the string is *eligible* to be corrupted at this level.

    Per spec: corruption doesn't start rendering until ~25% level, and even
    at 100% level only about 75% of the string can be touched.
    """
    level = _clamp(corruption_level)
    if level < 0.25:
        return 0.0
    return min(1.0, (level - 0.25) / 0.75) * 0.75


def _max_type_for_level(corruption_level: float) -> int:
    """The harshest corruption type patches are allowed to peak at."""
    level = _clamp(corruption_level)
    if level < 0.4:
        return PARTIAL
    if level < 0.7:
        return STATIC
    return CYCLE


def build_disposition(length: int, corruption_level: float) -> list[int]:
    """
    Build a per-character corruption-type array of the given length.

    Corruption is applied in clustered "patches" (corruption tokens) rather
    than scattered uniformly — each patch has a peak type and tapers off
    toward its edges, which is what produces the bunched-together look
    described in corruption.md (e.g. "00132100000123432100000023440000...").
    """
    disposition = [NONE_] * length
    if length == 0:
        return disposition

    fraction = corrupted_fraction(corruption_level)
    target = round(length * fraction)
    if target <= 0:
        return disposition

    max_type = _max_type_for_level(corruption_level)
    covered = 0
    attempts = 0
    # Lay down patches until we've roughly covered the target fraction, or
    # we give up after a generous number of attempts (short strings / high
    # fractions can't always hit the target exactly).
    while covered < target and attempts < length * 3:
        attempts += 1
        center = random.randrange(length)
        peak = random.randint(1, max_type)
        width = random.randint(1, 2 + peak)  # harsher peaks spread a bit wider

        for offset in range(-width, width + 1):
            idx = center + offset
            if not (0 <= idx < length):
                continue
            falloff = peak - abs(offset)
            if falloff <= 0:
                continue
            if falloff > disposition[idx]:
                if disposition[idx] == NONE_:
                    covered += 1
                disposition[idx] = falloff

    return disposition


# ---------------------------------------------------------------------------
# Debug helpers (kept from the original module)
# ---------------------------------------------------------------------------

def charleen() -> str:
    """random bullshit one of my friends wanted"""
    chrs: str = "♥★☻♡☾"
    return "".join(random.choice(chrs) for _ in range(100))


def repeat_char(chrs: str) -> None:
    """Used for debugging. Checks if there is a repeating character in a string."""
    already_checked: str = ""
    for spot, char in enumerate(chrs):
        if char in already_checked:
            raise ValueError(f"{char!r} is a repeat! (at index {spot})")
        already_checked += char


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class CorruptableLabel(Widget):
    """
    A label that visually degrades as corruption_level increases.

    corruption_level:
        0.0  = perfectly clear
        0.25 = corruption starts to become visible
        0.6  = heavy corruption, color bleeding, static/cycle patches
        1.0  = total chaos (still caps out around ~75% of characters touched)

    Two ways to drive corruption from TextEngine:
        trigger_corruption(n)     — a brief burst (e.g. /(glitch:N))
        start_persistent(level)   — sustained corruption until stopped
        stop_corruption()         — clears it (e.g. /(rst))
    """

    corruption_level: reactive[float] = reactive(0.0)
    text_content: reactive[str] = reactive("")

    def __init__(self, text: str = "", corruption_level: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self._disposition: list[int] = []
        self._static_chars: dict[int, str] = {}
        self._flicker_timer = None
        self._burst_timer = None
        self._persistent: bool = False

        # Set via reactive assignment so watchers fire and build the
        # disposition for the initial content/level.
        self.text_content = text
        self.corruption_level = corruption_level

    # ------------------------------------------------------------------
    # Disposition (re)building
    # ------------------------------------------------------------------

    def _rebuild_disposition(self) -> None:
        self._disposition = build_disposition(len(self.text_content), self.corruption_level)
        pool = glitch_chars_for_level(self.corruption_level)
        self._static_chars = {
            i: random.choice(pool)
            for i, ctype in enumerate(self._disposition)
            if ctype == STATIC
        }

    def _restart_flicker_timer(self) -> None:
        if self._flicker_timer is not None:
            self._flicker_timer.stop()
            self._flicker_timer = None
        # Anything above NONE_ benefits from a rerender tick — flicker/partial
        # need it to re-roll, cycle needs it to pick a new glitch char.
        if self.corruption_level > 0 and any(self._disposition):
            self._flicker_timer = self.set_interval(_RENDER_INTERVAL, self.refresh)

    # ------------------------------------------------------------------
    # Reactive watchers
    # ------------------------------------------------------------------

    def watch_text_content(self, _old: str, _new: str) -> None:
        self._rebuild_disposition()
        self._restart_flicker_timer()
        self.refresh()

    def watch_corruption_level(self, _old: float, new: float) -> None:
        self._rebuild_disposition()
        self._restart_flicker_timer()
        self.refresh()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> Text:
        result = Text()
        pool = glitch_chars_for_level(self.corruption_level)

        for i, char in enumerate(self.text_content):
            ctype = self._disposition[i] if i < len(self._disposition) else NONE_
            display_char, style = self._render_char(char, ctype, i, pool)
            result.append(display_char, style=style)

        return result

    def _render_char(self, char: str, ctype: int, idx: int, pool: str) -> tuple[str, str]:
        if ctype == NONE_:
            return char, ""

        if ctype == FLICKER:
            show = random.random() < _FLICKER_CHANCE
        elif ctype == PARTIAL:
            show = random.random() < _PARTIAL_CHANCE
        else:  # STATIC or CYCLE are always shown corrupted
            show = True

        if not show:
            return char, ""

        roll = random.random()
        if roll < _DIM_THRESHOLD:
            # 1. character stays, but dimmed
            return char, "dim"

        glitch_char = (
            self._static_chars.get(idx, char) if ctype == STATIC
            else random.choice(pool)
        )

        if roll < _PLAIN_GLITCH_THRESHOLD:
            # 2. glitch char, no color bleed
            return glitch_char, "dim"

        # 3. glitch char, color bleeds
        return glitch_char, random.choice(GLITCH_COLORS)

    # ------------------------------------------------------------------
    # Public API — driven by TextEngine's glitch hooks
    # ------------------------------------------------------------------

    def trigger_corruption(self, ticks: int) -> None:
        """
        A brief corruption burst, e.g. from /(glitch:N).

        Bumps corruption_level up for roughly `ticks` rerender cycles, then
        relaxes back down — unless persistent corruption is already active,
        in which case the burst just layers on top temporarily.
        """
        if ticks <= 0:
            return

        if self._burst_timer is not None:
            self._burst_timer.stop()
            self._burst_timer = None

        baseline = self.corruption_level if self._persistent else 0.0
        burst_level = _clamp(baseline + 0.15 * ticks)
        self.corruption_level = burst_level

        def _relax() -> None:
            self.corruption_level = baseline
            self._burst_timer = None

        self._burst_timer = self.set_timer(_RENDER_INTERVAL * max(ticks, 3), _relax)

    def start_persistent(self, level: float = 0.6) -> None:
        """Sustained corruption until stop_corruption() is called — /(glitch)."""
        self._persistent = True
        self.corruption_level = _clamp(level)

    def stop_corruption(self) -> None:
        """Clears any persistent or in-progress corruption — /(rst)."""
        self._persistent = False
        if self._burst_timer is not None:
            self._burst_timer.stop()
            self._burst_timer = None
        self.corruption_level = 0.0


if __name__ == '__main__':
    print(charleen())
    repeat_char(GLITCH_CHARS)
    print(len(GLITCH_CHARS))
    print(GLITCH_CHARS_T1)
    print(GLITCH_CHARS_T2)
    print(GLITCH_CHARS_T3)
    print(GLITCH_CHARS_T4)

    # Quick sanity check of the disposition generator without a Textual app
    sample = "This is a test string to show corruption."
    for lvl in (0.0, 0.3, 0.6, 1.0):
        d = build_disposition(len(sample), lvl)
        print(f"level={lvl:.2f}  ", "".join(str(t) for t in d))

    input("Press enter to exit...")
