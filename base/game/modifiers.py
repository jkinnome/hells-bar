class RunModifier:
    def __init__(self, name: str, effect: None, description: str):
        self.name = name
        self.effect = effect
        self.description = description


modifier_spite: RunModifier = RunModifier(
    name="Spite Run",
    effect=None,
    description="Maximum BAC is 0.35 (lower), but Spite generates at 2x rate."
)

modifier_blind: RunModifier = RunModifier(
    name="Blind Drunk",
    effect=None,
    description="All shots are hidden for the entire run."
)

modifier_nina_night: RunModifier = RunModifier(
    name="Nina's Night",
    effect=None,
    description="Ninoula starts at 0.10 BAC (already tipsy) but tension starts at 0.4."
)

modifier_cursed: RunModifier = RunModifier(
    name="Cursed Night",
    effect=None,
    description="Cursed shots can appear from round 1."
)

modifier_clean: RunModifier = RunModifier(
    name="Clean Slate",
    effect=None,
    description="Trinkets and cards are permanently disabled for the run."
)

modifier_last: RunModifier = RunModifier(
    name="Last Orders",
    effect=None,
    description="The run ends after 7 rounds regardless. Whoever has lower BAC wins."
)

modifier_familiar: RunModifier = RunModifier(  # Note: can only appear after run 2.
    name="Familiar Face",
    effect=None,
    description="Nina's affection starts at 0.5 and tension at 0. She's glad to see you."
)

modifier_open: RunModifier = RunModifier(
    name="Open Bar",
    effect=None,
    description="All shots are always revealed."
)
