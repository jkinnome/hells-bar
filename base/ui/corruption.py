import random

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

"𐀶𐃯𐄘𐄪𐄹☘☊☋☟"
GLITCH_CHARS: str = (
    "█▓▒░▄▀■□▇▁▪◆◇※@#$€¥£§%&?!°_†ƒŒ‡‰•š™œžŸ¢¡¤¦©®¬±×+-*÷~µ¶ÆÇØþ⁇⁂‖⁜∑⊠╳✪"
    "☙☟☺☻♥♡♠♣♦⛶⛤⛧▯⯑⍰︙⸮★⦀☾⚝✟✶☉ᛜ✠🝍🜅🜆🜋☲🜂⚘⸎〄ꝏℌℜ℣⌘𐀶𐃯𐄘𐄪𐄹☊☋ꙮ"
)
GLITCH_CHARS_T1: str = GLITCH_CHARS[:int(1 / 4 * len(GLITCH_CHARS))]  # 25% per tier
GLITCH_CHARS_T2: str = GLITCH_CHARS[:int(2 / 4 * len(GLITCH_CHARS))]
GLITCH_CHARS_T3: str = GLITCH_CHARS[:int(3 / 4 * len(GLITCH_CHARS))]
GLITCH_CHARS_T4: str = GLITCH_CHARS  # All characters


def charleen() -> str:
    """random bullshit one of my friends wanted"""
    text: str = ""
    chrs: str = "♥★☻♡☾"
    for _ in range(100):
        text += random.choice(chrs)
    return text


def repeat_char(chrs: str) -> None:
    """Used for debugging. Checks if there is a repeating character in a string."""
    already_checked: str = ""
    for spot, char in enumerate(chrs):
        if char in already_checked:
            raise ValueError(f"{char!r} is a repeat! (at index {spot})")
        already_checked += char


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
        self._flicker_timer = None

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
        """Called automatically when corruption level changes"""
        if self._flicker_timer is not None:
            self._flicker_timer.stop()
            self._flicker_timer = None
        if new_level > 0.6:
            self._flicker_timer = self.set_interval(0.15, self.refresh)


if __name__ == '__main__':
    print(charleen())
    repeat_char(GLITCH_CHARS)
    print(len(GLITCH_CHARS))
    print(GLITCH_CHARS_T1)
    print(GLITCH_CHARS_T2)
    print(GLITCH_CHARS_T3)
    print(GLITCH_CHARS_T4)
    input("Press enter to exit...")
