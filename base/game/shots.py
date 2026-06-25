from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base.game.effects import Effect

real_flavor_tags: list[str] = ["Clean", "Spirit", "Warm", "Agave", "Floral", "Sweet", "Grape", "Bubbly",
                               "Rice", "Subtle", "Fruit", "Anise", "Void", "Herbal", "Grain", "Pure", "Rough", "Light"]
fictive_flavor_tags: list[str] = ["Demon", "Fire", "Ghost", "Cursed", "Spite", "Clarity", "Wild"]
sin_flavor_tags: list[str] = ["Pride", "Lust", "Wrath", "Envy", "Sloth", "Greed", "Gluttony", "Fraud", "Treachery"]
all_flavor_tags: list[str] = real_flavor_tags + fictive_flavor_tags + sin_flavor_tags


class Rarity(Enum):
    Common = auto()
    Uncommon = auto()
    Rare = auto()
    Cursed = auto()
    Sin = auto()
    Special = auto()  # Reserved for shots that can't come up naturally in a standard round


class Visibility(Enum):
    Revealed = auto()
    Hidden = auto()
    Partial = auto()


class EffectTrigger(Enum):
    Immediate = auto()
    Delayed = auto()
    Cumulative = auto()
    OnCombo = auto()


class Alcohol:
    def __init__(self,
                 id: str,
                 name: str,
                 abv: float,
                 rarity: Rarity,
                 effect: Effect | None,  # TODO: add effects
                 flavor_tags: list[str],
                 nina_reaction: dict[str, list[str]] | None = None,  # All nones are placeholders for the moment
                 visibility: Visibility | None = None,
                 effect_trigger: EffectTrigger | None = None):
        self.name = name
        self.abv = abv
        self.rarity = rarity
        self.visibility = visibility
        self.effect = effect
        self.effect_trigger = effect_trigger
        self.flavor_tags = flavor_tags
        self.nina_reaction = nina_reaction


# ---- WATER ----------------------------
"""Water: Not an alcohol, still counts as a shot."""
shot_water: Alcohol = Alcohol(
    id="water",
    name="Water",
    abv=0.0,
    rarity=Rarity.Special,
    effect=None,
    flavor_tags=[]  # Water has no flavor
)

# ---- REAL ALCOHOLS --------------------
"""Vodka: The base alcohol. No effect."""
shot_vodka: Alcohol = Alcohol(
    id="vodka",
    name="Vodka",
    abv=0.4,
    rarity=Rarity.Common,
    effect=None,
    flavor_tags=["Clean", "Spirit"],
)

"""Bourbon: Slight spite generation."""
shot_bourbon: Alcohol = Alcohol(
    id="bourbon",
    name="Bourbon",
    abv=0.45,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Warmth", +1 Spite the next round
    flavor_tags=["Warm", "Spirit"],
)

"""Whiskey: No effect."""
shot_whiskey: Alcohol = Alcohol(
    id="whiskey",
    name="Whiskey",
    abv=0.50,
    rarity=Rarity.Common,
    effect=None,
    flavor_tags=["Rough", "Herbal"],
)

"""Brandy: No effect."""
shot_brandy: Alcohol = Alcohol(
    id="brandy",
    name="Brandy",
    abv=0.40,
    rarity=Rarity.Common,
    effect=None,
    flavor_tags=["Fruit", "Warm"],
)

"""Ale: No effect."""
shot_ale: Alcohol = Alcohol(
    id="ale",
    name="Ale",
    abv=0.12,
    rarity=Rarity.Common,
    effect=None,
    flavor_tags=["Rough", "Floral"],
)

"""Tequila: Gives courage."""
shot_tequila: Alcohol = Alcohol(
    id="tequila",
    name="Tequila",
    abv=0.38,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Bold", next card costs 0 Spite
    flavor_tags=["Agave", "Spirit"],
)

"""Gin: Sharpens senses slightly."""
shot_gin: Alcohol = Alcohol(
    id="gin",
    name="Gin",
    abv=0.42,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Clarity", reduces corruption by 5% for the turn
    flavor_tags=["Floral", "Spirit"],
)

"""Red Wine: Delayed BAC gain."""
shot_red_wine: Alcohol = Alcohol(
    id="wine",
    name="Red Wine",
    abv=0.14,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Slow Burn", BAC gain gets delayed by one round
    flavor_tags=["Sweet", "Grape"],
)

"""Champagne: Gives a small BAC reduction."""
shot_champagne: Alcohol = Alcohol(
    id="champagne",
    name="Champagne",
    abv=0.12,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Fizz", reduces BAC by 0.01
    flavor_tags=["Sweet", "Bubbly"],
)

"""Rum: Standard. No effect."""
shot_rum: Alcohol = Alcohol(
    id="rum",
    name="Rum",
    abv=0.40,
    rarity=Rarity.Common,
    effect=None,
    flavor_tags=["Warm", "Spirit"],
)

"""Sake: Low ABV but increases the next source of alcohol"""
shot_sake: Alcohol = Alcohol(
    id="sake",
    name="Sake",
    abv=0.17,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Creep", +30% BAC from next source
    flavor_tags=["Rice", "Subtle"],
)

"""Schnapps: Extremely sweet."""
shot_schnapps: Alcohol = Alcohol(
    id="schnapps",
    name="Schnapps",
    abv=0.2,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Sweet Tooth", immediately triggers sugar combo
    flavor_tags=["Sweet", "Fruit"],
)

"""Absinthe: High ABV and corrupts the UI. Nina loves it."""
shot_absinthe: Alcohol = Alcohol(
    id="absinthe",
    name="Absinthe",
    abv=0.68,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Hallucinate", corruption +15%, one glass label randomizes
    flavor_tags=["Anise", "Void"],
)

"""Jägermeister: Neutralizes combos."""
shot_jaegermeister: Alcohol = Alcohol(
    id="jaegermeister",
    name="Jägermeister",
    abv=0.35,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Herbal", immunity to next combo
    flavor_tags=["Sweet", "Herbal"],
)

"""Soju: No effect."""
shot_soju: Alcohol = Alcohol(
    id="soju",
    name="Soju",
    abv=0.25,
    rarity=Rarity.Uncommon,
    effect=None,
    flavor_tags=["Clean", "Grain"],
)

"""Everclear: Extremely high ABV. Increases spite and corruption. Impresses Nina."""
shot_everclear: Alcohol = Alcohol(
    id="everclear",
    name="Everclear",
    abv=0.95,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Burnout", corruption +25%, +1 Spite
    flavor_tags=["Spirit", "Pure"],
)

"""Moonshine: Blacks out an UI element for a turn."""
shot_moonshine: Alcohol = Alcohol(
    id="moonshine",
    name="Moonshine",
    abv=0.6,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Blind", One UI Element gets blacked out for a turn
    flavor_tags=["Grain", "Rough"],
)

"""Beer: Weak, reduces BAC gain."""
shot_beer: Alcohol = Alcohol(
    id="beer",
    name="Beer",
    abv=0.05,
    rarity=Rarity.Common,
    effect=None,  # TODO: Effect: name="Filling", reduces BAC gain from next shot
    flavor_tags=["Light", "Grain"],
)

# ---- FICTIVE ALCOHOLS -----------------
"""All alcohol names here are a WIP, they are not final."""

"""Hellfire: Corrupts an UI element permanently and deals double BAC. Nina's favourite."""
shot_hellfire: Alcohol = Alcohol(
    id="hellfire",
    name="Hellfire",
    abv=0.85,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Sear", doubles BAC and permacorrupts
    flavor_tags=["Demon", "Fire"],
)

"""Shadowmead: Reverses passive charm/item for the round"""
shot_shadowmead: Alcohol = Alcohol(
    id="shadowmead",
    name="Shadowmead",
    abv=0.3,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Invert", active item's effect is reversed for the round
    flavor_tags=["Void", "Sweet"]
)

"""Ectofizz: Double or nothing."""
shot_ectofizz: Alcohol = Alcohol(
    id="ectofizz",
    name="Ectofizz",
    abv=0.2,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Phase", 50% chance to not gain any BAC and 50% chance it doubles
    flavor_tags=["Ghost", "Bubbly"],
)

"""Sip o' Styx: Curse. The next shots will always be hidden."""
shot_styx: Alcohol = Alcohol(
    id="styx",
    name="Sip o' Styx",
    abv=0.0,
    rarity=Rarity.Cursed,
    effect=None,  # TODO: Effect: name="Curse", The next shots on the table will always be hidden
    flavor_tags=["Void", "Cursed"],
)

"""Blooddemon: Shares BAC. Nina doesn't like this one."""
shot_blooddemon: Alcohol = Alcohol(
    id="blooddemon",
    name="Blooddemon",
    abv=0.6,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Shared Pain", everyone gains 80% BAC
    flavor_tags=["Demon", "Warm"],
)

"""Spritepara: Scales ABV with Spite"""
shot_sprite: Alcohol = Alcohol(
    id="spritepara",
    name="Spritepara",
    abv=0.1,  # TODO: Placeholder. Formula is ((10 + (Spite * 10)) / 100)
    rarity=Rarity.Rare,
    effect=None,
    flavor_tags=["Spirit", "Spite"],
)

"""Memoria: Reveals all shots next round for all"""
shot_memoria: Alcohol = Alcohol(
    id="memoria",
    name="Memoria",
    abv=0.15,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Reveal", reveals all shots next round for all players
    flavor_tags=["Herbal", "Clarity"],
)

"""Miss Echo: Rewards picking the same spot"""
shot_echo: Alcohol = Alcohol(
    id="echo",
    name="Miss Echo",
    abv=0.45,
    rarity=Rarity.Uncommon,
    effect=None,
    flavor_tags=["Spirit", "Void"],
)

"""Light Starna: Corruption clears but comes back at double rate"""
shot_starna: Alcohol = Alcohol(
    id="starna",
    name="Light Starna",
    abv=0.25,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Lucid Flash", clears corruption for one turn, then comes back at x2
    flavor_tags=["Light", "Pure"],
)

"""Bittersoul: Nina absolutely hates this."""
shot_bittersoul: Alcohol = Alcohol(
    id="bittersoul",
    name="Bittersoul",
    abv=0.5,
    rarity=Rarity.Uncommon,
    effect=None,  # TODO: Effect: name="Sour", if Nina drinks this, her mood shifts negatively (Irritated)
    flavor_tags=["Demon", "Herbal"],
)

"""Void Dram: Erases one shot if the next round is a standard round, reducing the shot count to 2."""
shot_void: Alcohol = Alcohol(
    id="void",
    name="Void",
    abv=0.35,
    rarity=Rarity.Cursed,
    effect=None,  # TODO: Effect: name="Erase", reduces the shot count to 2, if the next round is a standard round.
    flavor_tags=["Void", "Cursed"]
)

"""Idunnol Lite: Divine drink."""
shot_idunn: Alcohol = Alcohol(
    id="idunn",
    name="Idunnol Lite",
    abv=0.22,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Divine", immunity to corruption this round + 1 Card
    flavor_tags=["Pure", "Light"],
)

"""Zeusarinha: Fries the drinker's brain for a turn."""
shot_zeus: Alcohol = Alcohol(
    id="zeus",
    name="Zeusarinha",
    abv=0.55,
    rarity=Rarity.Rare,
    effect=None,  # TODO: Effect: name="Shock", either disables Nina's AI for a turn or randomizes your next shot pick
    flavor_tags=["Spirit", "Wild"],
)

"""Siopi: Mute the person who drinks."""
shot_siopi: Alcohol = Alcohol(
    id="siopi",
    name="Siopi",
    abv=0.0,
    rarity=Rarity.Cursed,
    effect=None,
    # TODO: Effect: name="Mute", chat is disabled, locks one card. Atleast Nina can't taunt you if she drinks it.
    flavor_tags=["Void", "Cursed"],
)

"""Grandmother's Recipe: Corruption doesn't increace, Nina gains atleast 0.01 BAC no matter what."""
shot_grandmother: Alcohol = Alcohol(
    id="grandmother",
    name="Grandmother's Recipe",
    abv=0.7,
    rarity=Rarity.Rare,
    effect=None,
    # TODO: Effect: name="Nostalgic", corruption level doesn't increase, Nina gains 0.01 BAC no matter what.
    #  Can trigger special lines.
    flavor_tags=["Warm", "Pure"],
)

# ---- SIN ALCOHOLS ---------------------
"""SUPERBIA Aureola: The Wine of the Proud."""
shot_pride: Alcohol = Alcohol(
    id="pride",
    name="Aureola",
    abv=0.38,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Hubris", for 2 rounds after drinking your BAC meter displays 20% lower than it truly is.
    #  Your corruption percentage reads 15% lower. All stats seem to be in the players favor.
    #  When the effect expires 3 rounds later, all true numbers get shown.
    #  If your BAC is >= 0.35, corruption increases by 25%. If you survive without hitting blackout, gain 2 Spite.
    flavor_tags=["Pride", "Light", "Warm", "Spirit"],
)

"""AVARITIA L'Usuraio: The Usurer's Draught"""
shot_greed: Alcohol = Alcohol(
    id="greed",
    name="L'Usuraio",
    abv=0.15,  # Increases by 5% per shot you drank this run ((shots_drank * 5) / 100). Caps at 75%.
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Accumulate", if Nina's BAC exceeds yours, steal 0.02 BAC from her. Else get 3 Spite.
    flavor_tags=["Greed", "Spirit", "Wild"],
)

"""LUXURIA Tempasta Rosata: The Pink Tempest"""
shot_lust: Alcohol = Alcohol(
    id="lust",
    name="Tempasta Rosata",
    abv=0.45,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Blown", 1. Nina's affection increases by 0.3. 2. Nina's tension increases by 0.2.
    #  3. A random card gets destroyed. If affection is >= 0.7, draw one instead. Nina can drink this if Manic or Gone.
    #  Tension/Corruption drops by 0.15 then.
    flavor_tags=["Lust", "Sweet", "Demon", "Bubbly"],
)

"""IRA Sangue dello Stige: Blood of the Styx"""
shot_wrath: Alcohol = Alcohol(
    id="wrath",
    name="Sangue dello Stige",
    abv=0.6,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Fury", 1. Gain 6 Spite. 2. Disable impatience timer for the next turn.
    #  Nina's taunts come out as "...!".
    #  3. Nina's mood shifts to (SMUG -> IRRITATED, TIPSY -> MANIC, MANIC -> MANIC.DESTRUCTIVE). Starts breaking rules.
    #  Nina can drink this. If she selects this (usually while manic), she slams it down and her mood worsens too. Pity.
    flavor_tags=["Wrath", "Demon", "Spite", "Fire"]
)

"""GULA Il Pantano: The Mire"""
shot_gluttony: Alcohol = Alcohol(
    id="gluttony",
    name="Il Pantano",
    abv=0.3,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Cerberus Clause", immediately be forced to drink another shot of choice.
    #  Cannot skip this. Special: The Mire's Mercy.
    #  If the second shot is a common shot with ABV <= 20%, Gluttony BAC is halved.
    #  Nina can pick this and will have the same logic.
    flavor_tags=["Gluttony", "Grain", "Rough", "Cursed"],
)

"""ACCIDIA Acque Nere: The Black Waters"""
shot_sloth: Alcohol = Alcohol(
    id="sloth",
    name="Acque Nere",
    abv=0.2,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Stagnation", Next turn skipped entirely, no BAC gains, no Corruption gains, no effects.
    #  Special: The Sullen's Irony. If you use Sloth while ahead, the effect applies to Nina instead.
    flavor_tags=["Sloth", "Void", "Subtle"],
)

"""INVIDIA Occhio Verde: The Green Eye"""
shot_envy: Alcohol = Alcohol(
    id="envy",
    name="Occhio Verde",
    abv=0.1,  # Mirrors the last shot the other person took (minimum 10%)
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Mirror",
    flavor_tags=["Envy", "Void", "Spirit"],
)

# GEOGRAPHICAL SINS, EVEN RARER ------------------------------

"""COCYTUS Ghiaccio di Caina: Ice of Caina"""
shot_caina: Alcohol = Alcohol(
    id="caina",
    name="Ghiaccio di Caina",
    abv=0.0,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Suspended", All game effects are frozen for 2 turns. Nothing moves.
    #  Then everything returns to normal. Special: Traitor's Lake.
    #  If tension >= 0.7, the suspension is broken after one round
    flavor_tags=["Void", "Cursed", "Clean"],
)

"""MALEBOLGE Frode Imbottigliata: Bottled Fraud"""
shot_fraud: Alcohol = Alcohol(
    id="fraud",
    name="Frode Imbottigliata",
    abv=0.5,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Falsifier", All shot labels are randomized including those you have already peeked.
    #  The contents still stay the same. Nina also picks based on the label. If smug, she detects the fraud.
    flavor_tags=["Fraud", "Cursed", "Void"]
)

# THE RAREST DRINK - TREACHERY
"""PRODITIO Il Terzo Morso: The Third Bite"""
shot_treachery: Alcohol = Alcohol(
    id="treachery",
    name="Il Terzo Morso",
    abv=0.8,
    rarity=Rarity.Sin,
    effect=None,
    # TODO: Effect: name="Traitor", 1. The next trick card played is successful no matter what.
    #  2. Tension is set to 1 permanently. AI plays optimally for the rest of the round. She gets serious.
    #  If Nina drinks this (only possible if it's Nina's Night/She's Gone)
    #  corruption resets, her affection and tension values get reset (affection stays at 0 tho) and she goes quiet.
    flavor_tags=["Treachery", "Void", "Cursed", "Anise"],
)

all_alcohols: list[Alcohol] = [shot_vodka, shot_bourbon, shot_tequila, shot_gin, shot_red_wine, shot_champagne,
                               shot_rum,
                               shot_schnapps, shot_beer, shot_ale, shot_brandy, shot_whiskey, shot_sake,
                               shot_jaegermeister,
                               shot_soju, shot_moonshine, shot_shadowmead, shot_ectofizz, shot_memoria, shot_echo,
                               shot_bittersoul,
                               shot_absinthe, shot_everclear, shot_hellfire, shot_blooddemon, shot_sprite, shot_starna,
                               shot_idunn,
                               shot_zeus, shot_grandmother, shot_styx, shot_void, shot_siopi, shot_pride, shot_greed,
                               shot_lust,
                               shot_gluttony, shot_sloth, shot_fraud, shot_envy, shot_wrath, shot_caina, shot_treachery,
                               shot_water]


def build_alcohol_list(r: Rarity) -> list[Alcohol]:
    return [s for s in all_alcohols if s.rarity == r]


all_common_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Common)
all_uncommon_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Uncommon)
all_rare_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Rare)
all_cursed_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Cursed)
all_sin_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Sin)
all_special_alcohols: list[Alcohol] = build_alcohol_list(Rarity.Special)


def flavor_tag_exists(alcohol_list: list[Alcohol]) -> None:
    """Checks all alcohols to see if the flavor tags match with what's available. If not, raises a ValueError."""
    all_alcohol_flavor_tag_lists: list[list[str]] = [tag.flavor_tags for tag in alcohol_list]
    all_alcohol_flavor_tags: list[str] = [tag for tag_list in all_alcohol_flavor_tag_lists for tag in tag_list]
    for flavor_tag in all_alcohol_flavor_tags:
        if flavor_tag not in all_flavor_tags:
            raise ValueError(f"Flavor tag {flavor_tag} not available")


if __name__ == "__main__":
    flavor_tag_exists(all_alcohols)
