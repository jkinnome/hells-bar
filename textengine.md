# Textengine

---

## Commands

Basic:

- /(^N) - pause for N seconds
- /(spd:N) - typing speed (N seconds per character)
- /(rst) - reset all typewriter changes (speed, etc.)
- /(n) - newline
- /(br) - blank line (double newline)
- /(t) - tab
- /(clr) - clear

Interaction:

- /(clk) - wait for keypress

Game hooks / audio:

- /(sfx:NAME) - fire audiomanager sound effect
- /(wsfx:NAME) - fire sound and wait for it to stop before continuing
- /(mood:NAME) - signal a MoodEngine transition
- /(glitch:N) - trigger N corruption ticks on a CorruptableLabel. see corruption.md for more on Corruption.
- /(glitch) - trigger corruption for the rest of the string. Can be reset via /(rst)

Character effects:

- /(drunk:N) - drunk typing for the next N characters (random slurring: doubled chars, swapped case)
- /(hicc) - hiccup (stutter pause + optional sfx)
- /(slw) - slow down speed by 50%
- /(fst) - speed up by 50%