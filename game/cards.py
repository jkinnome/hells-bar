from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game.effects import Effect


class CardType(Enum):
    ACTION = auto()  # One time use on player's turn
    TRICK = auto()  # Require conditions for optimal play / Risk and Reward
    REACTION = auto()  # Passive, trigger on conditions
    UNIQUE = auto()  # You can only get one per run


class Card:
    def __init__(self,
                 name: str,
                 desc: str,
                 card_type: CardType,
                 effect: Effect,
                 detectability: Optional[float] = None):
        """
        A card class for all card objects. It requires a name and a description
        as well as a CardType. Namely one from the four available above. Every card also has an effect given to it.
        Detectable is used for trick cards to see how easily Nina can see through your trap.
        These are not used for other card types.
        """
        self.name = name
        self.desc = desc
        self.card_type = card_type
        self.effect = effect
        self.passive = False

        if self.card_type == CardType.TRICK:
            self.detectability = detectability
        elif self.card_type == CardType.REACTION:
            self.passive = True


# CARD OBJECTS
# ACTION CARDS

card_water_chaser: Card = Card(
    name="Water Chaser",
    desc="Skip BAC gain from your shot this round. The glass still counts as drunk.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_glass_peek: Card = Card(
    name="Glass Peek",
    desc="Look at one hidden shot before choosing. Nina may know you looked.",
    card_type=CardType.ACTION,
    effect=Effect(),
    detectability=0.1
)

card_breathalyzer: Card = Card(
    name="Breathalyzer",
    desc="See Nina's exact BAC number regardless of UI corruption.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_coffee_shot: Card = Card(
    name="Coffee Shot",
    desc="Reduce your corruption by 20% this round. Next round, corruption comes back +10% harder.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_force_feed: Card = Card(
    name="Force Feed",
    desc="Nina must drink an additional shot this round (from the unchosen glasses).",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_ice_bucket: Card = Card(
    name="Ice Bucket",
    desc="Permanently reduce BAC by 0.02. Cards are disabled for the turn afterwards.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_distraction: Card = Card(
    name="Distraction",
    desc="Nina's pick this round is randomized regardless of her mood.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_sneak_sip: Card = Card(
    name="Sneak Sip",
    desc="Take only half a shot. BAC gain is 50%. Nina might notice depending on her sobriety.",
    card_type=CardType.ACTION,
    effect=Effect(),
    detectability=0.2
)

card_second_wind: Card = Card(
    name="Second Wind",
    desc="Immediately reduce BAC by 0.03 and clear one corruption tier.",
    card_type=CardType.ACTION,
    effect=Effect(),
)

card_interrogate: Card = Card(
    name="Interrogate",
    desc="Ask Nina one yes/no question she must answer truthfully. Works better when she's tipsy.",
    card_type=CardType.ACTION,
    effect=Effect(),
    detectability=0.35
)

card_intimidate: Card = Card(
    name="Intimidate",
    desc="Force Nina's mood to shift toward Irritated. She makes suboptimal picks when irritated.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_read_room: Card = Card(
    name="Read the Room",
    desc="Reveal which shot Nina is currently planning to pick (not final, changes if she detects you).",
    card_type=CardType.ACTION,
    effect=Effect(),
    detectability=0.3
)

card_stall: Card = Card(
    name="Stall",
    desc="Skip your turn entirely. No shot, no BAC. Nina picks anyway. Costs 2 Spite.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_spite_spike: Card = Card(
    name="Spite Spike",
    desc="Convert 3 Spite into 0.03 BAC reduction.",
    card_type=CardType.ACTION,
    effect=Effect()
)

card_double_down: Card = Card(
    name="Double Down",
    desc="Pick two shots instead of one. BAC doubles, but so does card draw this round.",
    card_type=CardType.ACTION,
    effect=Effect()
)

# TRICK CARDS

card_palmed_switch: Card = Card(
    name="Palmed Switch",
    desc="After Nina picks, swap your glass with hers secretly.",
    card_type=CardType.TRICK,
    effect=Effect(),
    detectability=0.3
    # Nina must be TIPSY or GONE or else she catches you and you drink both
)

card_cup_shuffle: Card = Card(
    name="Cup Shuffle",
    desc="Both you and Nina re-pick from shuffled unknown glasses.",
    card_type=CardType.TRICK,
    effect=Effect()
)

card_doctored_glass: Card = Card(
    name="Doctored Glass",
    desc="Pre-load one glass as water. It shows 0% ABV if revealed.",
    card_type=CardType.TRICK,
    effect=Effect(),
    detectability=0.33
)

card_sleight_hand: Card = Card(
    name="Sleight of Hand",
    desc="Swap two glasses on the table without Nina noticing. Success based on corruption level.",
    card_type=CardType.TRICK,
    effect=Effect()
    # If corruption is over 40% automatically fails
)

card_blame_bartender: Card = Card(
    name="Blame the Bartender",
    desc="Declare one glass 'contaminated' and remove it from play.",
    card_type=CardType.TRICK,
    effect=Effect(),
    detectability=0.5
)

card_table_flip: Card = Card(
    name="Table Flip",
    desc="Scatter all glasses. Round resets with 3 new random shots. BAC stays.",
    card_type=CardType.TRICK,
    effect=Effect()
    # Must be at BAC > 0.25 and uses 4 spite
)

card_call_out: Card = Card(
    name="Call It Out",
    desc="Accuse Nina of cheating. If correct: she drinks a penalty shot. If wrong: you do.",
    card_type=CardType.TRICK,
    effect=Effect()
)

card_reverse_uno: Card = Card(
    name="Reverse Uno",
    desc="Whatever shot Nina was going to give you, she drinks instead. She will HATE this.",
    card_type=CardType.TRICK,
    effect=Effect()
    # Nina has to be manic, and it will reduce affection by a lot
)

# REACTION CARDS

card_rock_bottom: Card = Card(
    name="Rock Bottom",
    desc="All shot contents are revealed immediately.",
    card_type=CardType.REACTION,
    effect=Effect()
    # BAC hits 0.35
)

card_spite_surge: Card = Card(
    name="Spite Surge",
    desc="+2 Spite and your next pick costs no Spite abilities.",
    card_type=CardType.REACTION,
    effect=Effect()
    # Nina taunts you during your turn
)

card_liquid_courage: Card = Card(
    name="Liquid Courage",
    desc="Draw 1 Action card immediately. The alcohol loosens something.",
    card_type=CardType.REACTION,
    effect=Effect()
    # BAC crosses 0.2
)

card_ghost_protocol: Card = Card(
    name="Ghost Protocol",
    desc="20% chance the shot is Ectoplasm Fizz regardless of what it was.",
    card_type=CardType.REACTION,
    effect=Effect()
    # Player picks a Hidden shot
)

card_dead_sip: Card = Card(
    name="Dead Man's Sip",
    desc="Sets the next turn modifier to Nina's First.",
    card_type=CardType.REACTION,
    effect=Effect()
    # You're the last one to have drunk and Nina is Tipsy/Gone
)

card_spite_armor: Card = Card(
    name="Spite Armor",
    desc="Immune to the next negative effect from any shot. Spite physically protecting you.",
    card_type=CardType.REACTION,
    effect=Effect()
    # Spite reaches 8
)

# UNIQUE CARDS

card_ninas_recipe: Card = Card(
    name="Nina's Recipe",
    desc="Add a Hellfire Hooch to the next round's table, except you can see it, Nina can't.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)

card_lucid_flash: Card = Card(
    name="Lucid Flash",
    desc="Corruption fully clears for one turn.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)

card_spite_bomb: Card = Card(
    name="Spite Bomb",
    desc="Spend ALL your Spite at once. For each Spite spent, Nina's BAC increases by 0.005.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)

card_blackout_dagger: Card = Card(
    name="Blackout Dagger",
    desc="Choose to pass out on purpose with Nina. A draw.",
    card_type=CardType.UNIQUE,
    effect=Effect()
    # Triggers a special ending, only way to get a draw
)

card_contract: Card = Card(
    name="The Contract",
    desc="Challenge Nina to a side bet: name the next shot correctly. Win: she drinks a penalty. Lose: you drink two.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)

card_survival_instinct: Card = Card(
    name="Survival Instinct",
    desc="Reduce the next hit by 40% if you would reach blackout from this shot.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)

card_fake_out: Card = Card(
    name="Fake Out",
    desc="Commit to picking one glass, then switch to another after Nina has mentally committed to her choice.",
    card_type=CardType.UNIQUE,
    effect=Effect()
)
