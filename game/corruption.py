import random

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

GLITCH_CHARS: str = ("█▓▒░▄▀■□◆◇※@#$€¥£§%&?!°_†ƒŒ‡‰•š™œžŸ¢¡¤¦©®¬±×+-*÷~µ¶ÆÇØþ⁇⁂‖⁜∑⊠╳✪☂"
                     "☘☠☢☣☝☺☻♥♡♾⛶⛤⛧⸎〄𐀶𐃯𐄂𐄘𐄪𐄹▯⯑⍰︙⸮★✝▇▁▪⦀✴❤☾⚝")
GLITCH_TIER_1: str = GLITCH_CHARS[:int(1 / 4 * 100)]  # 25 per tier
GLITCH_TIER_2: str = GLITCH_CHARS[:int(2 / 4 * 100)]
GLITCH_TIER_3: str = GLITCH_CHARS[:int(3 / 4 * 100)]
GLITCH_TIER_4: str = GLITCH_CHARS  # All characters, 100


def charleen() -> str:
    text: str = ""
    chrs: list[str] = ["♥", "★", "☻", "❤", "☾"]
    for _ in range(100):
        text += random.choice(chrs)
    return text


def repeat_char(chrs: str) -> None:
    """Used for debugging. Checks if there is a repeating character in a string."""
    valid_chars: str = ""
    for spot, char in enumerate(chrs):
        if char not in valid_chars:
            valid_chars += char
        else:
            raise ValueError(f"{char} is a repeat! (at {spot})")


GLITCH_COLORS = ["red", "bright_red", "dark_red", "magenta"]


class CorruptableLabel(Widget):
    """
    A label that visually degrades as corruption_level increases.

    corruption_level:

    0.0 = perfectly clear
    0.3 = occasional glitched characters
    0.6 = heavy corruption, color bleeding
    1.0 = total chaos
    """

    corruption_level: reactive[float] = reactive(0.0)
    text_content: reactive[str] = reactive("")

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text_content = text

    def render(self) -> Text:
        result = Text()
        c = self.corruption_level
        for char in self.text_content:
            roll = random.random()
            if char == " ":
                # Spaces occasionally become glitch chars at high corruption
                if c > 0.7 and roll < (c - 0.7):
                    result.append(random.choice(GLITCH_CHARS), style="dim red")
                else:
                    result.append(" ")
            elif roll < c * 0.5:
                # Character replaced by glitch
                result.append(random.choice(GLITCH_CHARS), style=random.choice(GLITCH_COLORS))
            elif roll < c * 0.7:
                # Character kept but color bleeding
                result.append(char, style=random.choice(GLITCH_COLORS))
            elif c > 0.4 and roll < c * 0.9:
                # Character dimmed / faded
                result.append(char, style=f"dim")
            else:
                result.append(char)

        return result

    def watch_corruption_level(self, new_level: float) -> None:
        """Called automatically when corruption_level changes."""
        # At high corruption, start flickering via a timer
        if new_level > 0.6:
            self.set_interval(0.15, self.refresh)  # Force re-render frequently


if __name__ == '__main__':
    print(charleen())
    repeat_char(GLITCH_CHARS)
    print(len(GLITCH_CHARS))
    print(GLITCH_TIER_1)
    print(GLITCH_TIER_2)
    print(GLITCH_TIER_3)
    print(GLITCH_TIER_4)
