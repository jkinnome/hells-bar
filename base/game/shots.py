from enum import Enum, auto
from typing import TYPE_CHECKING
from dataclasses import dataclass
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


@dataclass
class Alcohol:
    def __init__(self,
                 identifier: str,
                 name: str,
                 abv: float,
                 rarity: Rarity,
                 effect: Effect | None,  # TODO: add effects
                 flavor_tags: list[str],
                 nina_reaction: dict[str, list[str]] | None = None,  # All nones are placeholders for the moment
                 visibility: Visibility | None = None,
                 table_pos: int | None = None,
                 effect_trigger: EffectTrigger | None = None):
        self.id = identifier
        self.name = name
        self.abv = abv
        self.rarity = rarity
        self.visibility = visibility
        self.effect = effect
        self.effect_trigger = effect_trigger
        self.flavor_tags = flavor_tags
        self.nina_reaction = nina_reaction
        self.table_pos = table_pos


# ---- WATER ----------------------------
"""Water: Not an alcohol, still counts as a shot."""
shot_water: Alcohol = Alcohol(identifier="water", name="Water", abv=0.0, rarity=Rarity.Special, effect=None,
                              flavor_tags=[])

# ---- REAL ALCOHOLS --------------------
"""Vodka: The base alcohol. No effect."""
shot_vodka: Alcohol = Alcohol(identifier="vodka", name="Vodka", abv=0.4, rarity=Rarity.Common, effect=None,
                              flavor_tags=["Clean", "Spirit"])

"""Bourbon: Slight spite generation."""
shot_bourbon: Alcohol = Alcohol(identifier="bourbon", name="Bourbon", abv=0.45, rarity=Rarity.Common, effect=None,
                                flavor_tags=["Warm", "Spirit"])

"""Whiskey: No effect."""
shot_whiskey: Alcohol = Alcohol(identifier="whiskey", name="Whiskey", abv=0.50, rarity=Rarity.Common, effect=None,
                                flavor_tags=["Rough", "Herbal"])

"""Brandy: No effect."""
shot_brandy: Alcohol = Alcohol(identifier="brandy", name="Brandy", abv=0.40, rarity=Rarity.Common, effect=None,
                               flavor_tags=["Fruit", "Warm"])

"""Ale: No effect."""
shot_ale: Alcohol = Alcohol(identifier="ale", name="Ale", abv=0.12, rarity=Rarity.Common, effect=None,
                            flavor_tags=["Rough", "Floral"])

"""Tequila: Gives courage."""
shot_tequila: Alcohol = Alcohol(identifier="tequila", name="Tequila", abv=0.38, rarity=Rarity.Common, effect=None,
                                flavor_tags=["Agave", "Spirit"])

"""Gin: Sharpens senses slightly."""
shot_gin: Alcohol = Alcohol(identifier="gin", name="Gin", abv=0.42, rarity=Rarity.Common, effect=None,
                            flavor_tags=["Floral", "Spirit"])

"""Red Wine: Delayed BAC gain."""
shot_red_wine: Alcohol = Alcohol(identifier="wine", name="Red Wine", abv=0.14, rarity=Rarity.Common, effect=None,
                                 flavor_tags=["Sweet", "Grape"])

"""Champagne: Gives a small BAC reduction."""
shot_champagne: Alcohol = Alcohol(identifier="champagne", name="Champagne", abv=0.12, rarity=Rarity.Common, effect=None,
                                  flavor_tags=["Sweet", "Bubbly"])

"""Rum: Standard. No effect."""
shot_rum: Alcohol = Alcohol(identifier="rum", name="Rum", abv=0.40, rarity=Rarity.Common, effect=None,
                            flavor_tags=["Warm", "Spirit"])

"""Sake: Low ABV but increases the next source of alcohol"""
shot_sake: Alcohol = Alcohol(identifier="sake", name="Sake", abv=0.17, rarity=Rarity.Uncommon, effect=None,
                             flavor_tags=["Rice", "Subtle"])

"""Schnapps: Extremely sweet."""
shot_schnapps: Alcohol = Alcohol(identifier="schnapps", name="Schnapps", abv=0.2, rarity=Rarity.Common, effect=None,
                                 flavor_tags=["Sweet", "Fruit"])

"""Absinthe: High ABV and corrupts the UI. Nina loves it."""
shot_absinthe: Alcohol = Alcohol(identifier="absinthe", name="Absinthe", abv=0.68, rarity=Rarity.Rare, effect=None,
                                 flavor_tags=["Anise", "Void"])

"""Jägermeister: Neutralizes combos."""
shot_jaegermeister: Alcohol = Alcohol(identifier="jaegermeister", name="Jägermeister", abv=0.35, rarity=Rarity.Uncommon,
                                      effect=None, flavor_tags=["Sweet", "Herbal"])

"""Soju: No effect."""
shot_soju: Alcohol = Alcohol(identifier="soju", name="Soju", abv=0.25, rarity=Rarity.Uncommon, effect=None,
                             flavor_tags=["Clean", "Grain"])

"""Everclear: Extremely high ABV. Increases spite and corruption. Impresses Nina."""
shot_everclear: Alcohol = Alcohol(identifier="everclear", name="Everclear", abv=0.95, rarity=Rarity.Rare, effect=None,
                                  flavor_tags=["Spirit", "Pure"])

"""Moonshine: Blacks out an UI element for a turn."""
shot_moonshine: Alcohol = Alcohol(identifier="moonshine", name="Moonshine", abv=0.6, rarity=Rarity.Uncommon,
                                  effect=None, flavor_tags=["Grain", "Rough"])

"""Beer: Weak, reduces BAC gain."""
shot_beer: Alcohol = Alcohol(identifier="beer", name="Beer", abv=0.05, rarity=Rarity.Common, effect=None,
                             flavor_tags=["Light", "Grain"])

# ---- FICTIVE ALCOHOLS -----------------
"""All alcohol names here are a WIP, they are not final."""

"""Hellfire: Corrupts an UI element permanently and deals double BAC. Nina's favourite."""
shot_hellfire: Alcohol = Alcohol(identifier="hellfire", name="Hellfire", abv=0.85, rarity=Rarity.Rare, effect=None,
                                 flavor_tags=["Demon", "Fire"])

"""Shadowmead: Reverses passive charm/item for the round"""
shot_shadowmead: Alcohol = Alcohol(identifier="shadowmead", name="Shadowmead", abv=0.3, rarity=Rarity.Uncommon,
                                   effect=None, flavor_tags=["Void", "Sweet"])

"""Ectofizz: Double or nothing."""
shot_ectofizz: Alcohol = Alcohol(identifier="ectofizz", name="Ectofizz", abv=0.2, rarity=Rarity.Uncommon, effect=None,
                                 flavor_tags=["Ghost", "Bubbly"])

"""Sip o' Styx: Curse. The next shots will always be hidden."""
shot_styx: Alcohol = Alcohol(identifier="styx", name="Sip o' Styx", abv=0.0, rarity=Rarity.Cursed, effect=None,
                             flavor_tags=["Void", "Cursed"])

"""Blooddemon: Shares BAC. Nina doesn't like this one."""
shot_blooddemon: Alcohol = Alcohol(identifier="blooddemon", name="Blooddemon", abv=0.6, rarity=Rarity.Rare, effect=None,
                                   flavor_tags=["Demon", "Warm"])

"""Spritepara: Scales ABV with Spite"""
shot_sprite: Alcohol = Alcohol(identifier="spritepara", name="Spritepara", abv=0.1, rarity=Rarity.Rare, effect=None,
                               flavor_tags=["Spirit", "Spite"])

"""Memoria: Reveals all shots next round for all"""
shot_memoria: Alcohol = Alcohol(identifier="memoria", name="Memoria", abv=0.15, rarity=Rarity.Uncommon, effect=None,
                                flavor_tags=["Herbal", "Clarity"])

"""Miss Echo: Rewards picking the same spot"""
shot_echo: Alcohol = Alcohol(identifier="echo", name="Miss Echo", abv=0.45, rarity=Rarity.Uncommon, effect=None,
                             flavor_tags=["Spirit", "Void"])

"""Light Starna: Corruption clears but comes back at double rate"""
shot_starna: Alcohol = Alcohol(identifier="starna", name="Light Starna", abv=0.25, rarity=Rarity.Rare, effect=None,
                               flavor_tags=["Light", "Pure"])

"""Bittersoul: Nina absolutely hates this."""
shot_bittersoul: Alcohol = Alcohol(identifier="bittersoul", name="Bittersoul", abv=0.5, rarity=Rarity.Uncommon,
                                   effect=None, flavor_tags=["Demon", "Herbal"])

"""Void Dram: Erases one shot if the next round is a standard round, reducing the shot count to 2."""
shot_void: Alcohol = Alcohol(identifier="void", name="Void", abv=0.35, rarity=Rarity.Cursed, effect=None,
                             flavor_tags=["Void", "Cursed"])

"""Idunnol Lite: Divine drink."""
shot_idunn: Alcohol = Alcohol(identifier="idunn", name="Idunnol Lite", abv=0.22, rarity=Rarity.Rare, effect=None,
                              flavor_tags=["Pure", "Light"])

"""Zeusarinha: Fries the drinker's brain for a turn."""
shot_zeus: Alcohol = Alcohol(identifier="zeus", name="Zeusarinha", abv=0.55, rarity=Rarity.Rare, effect=None,
                             flavor_tags=["Spirit", "Wild"])

"""Siopi: Mute the person who drinks."""
shot_siopi: Alcohol = Alcohol(identifier="siopi", name="Siopi", abv=0.0, rarity=Rarity.Cursed, effect=None,
                              flavor_tags=["Void", "Cursed"])

"""Grandmother's Recipe: Corruption doesn't increace, Nina gains atleast 0.01 BAC no matter what."""
shot_grandmother: Alcohol = Alcohol(identifier="grandmother", name="Grandmother's Recipe", abv=0.7, rarity=Rarity.Rare,
                                    effect=None, flavor_tags=["Warm", "Pure"])

# ---- SIN ALCOHOLS ---------------------
"""SUPERBIA Aureola: The Wine of the Proud."""
shot_pride: Alcohol = Alcohol(identifier="pride", name="Aureola", abv=0.38, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Pride", "Light", "Warm", "Spirit"])

"""AVARITIA L'Usuraio: The Usurer's Draught"""
shot_greed: Alcohol = Alcohol(identifier="greed", name="L'Usuraio", abv=0.15, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Greed", "Spirit", "Wild"])

"""LUXURIA Tempasta Rosata: The Pink Tempest"""
shot_lust: Alcohol = Alcohol(identifier="lust", name="Tempasta Rosata", abv=0.45, rarity=Rarity.Sin, effect=None,
                             flavor_tags=["Lust", "Sweet", "Demon", "Bubbly"])

"""IRA Sangue dello Stige: Blood of the Styx"""
shot_wrath: Alcohol = Alcohol(identifier="wrath", name="Sangue dello Stige", abv=0.6, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Wrath", "Demon", "Spite", "Fire"])

"""GULA Il Pantano: The Mire"""
shot_gluttony: Alcohol = Alcohol(identifier="gluttony", name="Il Pantano", abv=0.3, rarity=Rarity.Sin, effect=None,
                                 flavor_tags=["Gluttony", "Grain", "Rough", "Cursed"])

"""ACCIDIA Acque Nere: The Black Waters"""
shot_sloth: Alcohol = Alcohol(identifier="sloth", name="Acque Nere", abv=0.2, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Sloth", "Void", "Subtle"])

"""INVIDIA Occhio Verde: The Green Eye"""
shot_envy: Alcohol = Alcohol(identifier="envy", name="Occhio Verde", abv=0.1, rarity=Rarity.Sin, effect=None,
                             flavor_tags=["Envy", "Void", "Spirit"])

# GEOGRAPHICAL SINS, EVEN RARER ------------------------------

"""COCYTUS Ghiaccio di Caina: Ice of Caina"""
shot_caina: Alcohol = Alcohol(identifier="caina", name="Ghiaccio di Caina", abv=0.0, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Void", "Cursed", "Clean"])

"""MALEBOLGE Frode Imbottigliata: Bottled Fraud"""
shot_fraud: Alcohol = Alcohol(identifier="fraud", name="Frode Imbottigliata", abv=0.5, rarity=Rarity.Sin, effect=None,
                              flavor_tags=["Fraud", "Cursed", "Void"])

# THE RAREST DRINK - TREACHERY
"""PRODITIO Il Terzo Morso: The Third Bite"""
shot_treachery: Alcohol = Alcohol(identifier="treachery", name="Il Terzo Morso", abv=0.8, rarity=Rarity.Sin,
                                  effect=None, flavor_tags=["Treachery", "Void", "Cursed", "Anise"])

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
