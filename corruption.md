# Corruption

---

Corruption is a mechanic used in Hell's Bar to signify intoxication. It replaces characters in labels that support
corruption with "glitch characters" to obstruct information. Comes up as CorruptableLabel Widget with textual.

There are four tiers of corruption that increase with player bac and unlock more characters to use.
> The formula is GLITCH_CHARS[:int(TIER_AMOUNT / 4 * len(GLITCHCHARS))]

---

All characters used for corruption: █▓▒░▄▀■□▇▁▪◆◇※@#$€¥£§%&?!°_†ƒŒ‡‰•š™œžŸ¢¡¤¦©®¬±×+-*÷~
µ¶ÆÇØþ⁇⁂‖⁜∑⊠╳✪☙☟☺☻♥♡♠♣♦⛶⛤⛧▯⯑⍰︙⸮★⦀☾⚝✟✶☉ᛜ✠🝍🜅🜆🜋☲🜂⚘⸎〄ꝏℌℜ℣⌘𐀶𐃯𐄘𐄪𐄹☊☋ꙮ

---

Glitch characters can also take one of these four colors: dim, red, bright red, dark red and magenta.

## Corruption behavior

When a label is supposed to get corrupted, the string gets split up into characters. For the length of the string and
the corruption amount "corruption tokens" are created. These are used to create the corruption disposition. In a
corrupted string there are patches of corruption (from high to low)

There are 5 corruption types:

0: No corruption

1: Flicker. Every rerender of the label (approximatelly once every 0.1 seconds), there is a 15% chance the character
gets corrupted for the render.

2: Partial. Every rerender there is a 50% chance the character gets corrupted.

3: Static. The character gets permanently replaced with ONE glitch character.

4: Cycle. The character always gets shown with a different glitch character.

A corrupted string could look like this with the types:

"This is a test string to show corruption."

"00132100000123432100000023440000110342200" = 49 corruption tokens used.

(Glitches bunch up together)

> Spaces can get corrupted too at high corruption.

---

When a character gets glitched, one of the following things can happen, depending on the roll:

1. The character stays but gets dimmed
2. Character gets replaced with a glitch character without bleeding color
3. Character gets replaced with a glitch character and bleeds color

Every 0.1 seconds the label gets rerendered with new characters (if their type supports it) and the contents and type
disposition stays as is. The type disposition does get rerolled though when the label changes or when corruption level
changes.

Depending on the corruption level, that's how much of the label is allowed to be corrupted. At 0% corruption, the label
isn't corrupted at all. At 100% corruption, the label can get corrupted at about 75% maximum. Corruption should actually
start getting rendered at about 25% corruption.