from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.state import GameState
    from game.ninoula.ninoula import Ninoula, Mood


class ChatAction(Enum):
    TALK = auto()  # get a bit of small talk or bits of lore out of her
    PROBE = auto()  # ask about a glass
    TAUNT = auto()  # taunt and annoy her
    CHARM = auto()  # build affection (can go horribly wrong)
    CHALLENGE = auto()  # dare her to pick a specific glass
    BARGAIN = auto()  # propose a trade
    CONFESS = auto()  # show vulnerability
    SILENCE = auto()  # say nothing, stare at her


@dataclass
class ChatOption:
    action: ChatAction
    label: str  # short button label (max 30chrs)
    tooltip: str  # more info


@dataclass
class ChatResult:
    nina_response: str
    affection_delta: float = 0.0
    tension_delta: float = 0.0
    info_revealed: str | None = None  # e.g. "Shot 2 is FOR SURE Bourbon bro TRUST"
    nina_mood_shifted: Mood | None = None


class ChatSystem:
    """
    Manages the player's chat interaction with Nina.
    One chat token per round. Using it runs a ChatAction.
    """

    def __init__(self):
        self.token_available: bool = True

    def reset_token(self) -> None:
        self.token_available = True

    @staticmethod
    def get_options(state: "GameState", nina: "Ninoula", window: str) -> list[ChatOption]:
        """
        Returns 3-5 chat options appropriate to the current window and state.
        windows: "during_turn" | "after_picks" | "breath_phase"
        """
        # ALL DIALOGUE OPTIONS HERE ARE PLACEHOLDERS AND ARE BOUND TO CHANGE WHEN I18N WILL BE MADE
        options: list[ChatOption] = []

        if window in ("during_turn", "breath_phase"):
            options.append(ChatOption(
                ChatAction.PROBE,
                "\"What do you think's in that one?\"",
                "Ask Nina about a glass. Accuracy depends on her sobriety."
            ))

        if nina.mood is not Mood.IRRITATED:
            options.append(ChatOption(
                ChatAction.TAUNT,
                "\"Slowing down a little, aren't you?\"",
                "Shift Nina toward Irritated. Risky if she's already tense."
            ))

        if state.affection < 0.8:
            options.append(ChatOption(
                ChatAction.CHARM,
                "\"You know, you're not what I expected.\"",
                "Build Affection. Costs nothing. Doesn't always land."
            ))

        if window == "breath_phase":
            options.append(ChatOption(
                ChatAction.BARGAIN,
                "\"I'll take the strong one if you tell me the others.\"",
                "Propose a trade. Nina accepts more when Tipsy."
            ))

        options.append(ChatOption(
            ChatAction.CONFESS,
            "\"I don't think I'm going to make it.\"",
            "Show vulnerability. Can open rare dialogue. Nina may respond."
        ))
        options.append(ChatOption(
            ChatAction.SILENCE,
            "\"...\"",
            "Say nothing. Stare back. Unsettles her in a specific way."
        ))

        options.append(ChatOption(
            ChatAction.TALK,
            "\"Nice weather we're having, right?\"",
            "Create a bit of small talk with Nina. Break the Ice, if you will."
        ))

        return options[:5]  # caps at 5

    def resolve(self, action: ChatAction, state: "GameState",
                nina: "Ninoula", targel_glass_idx: int = 0) -> ChatResult:
        """Process a chat action. Returns a result including Nina's response."""
        self.token_available = False
        state.stats.chat_actions_used += 1

        match action:
            case ChatAction.PROBE:
                return self._resolve_probe(state, nina, targel_glass_idx)
            case ChatAction.TAUNT:
                return self._resolve_taunt(nina)
            case ChatAction.CHARM:
                return self._resolve_charm(state, nina)
            case ChatAction.CONFESS:
                return self._resolve_confess(state, nina)
            case ChatAction.BARGAIN:
                return self._resolve_bargain(nina)
            case ChatAction.SILENCE:
                return self._resolve_silence()
            case ChatAction.CHALLENGE:
                return self._resolve_challenge(state, nina, targel_glass_idx)

            case _:
                raise ValueError(f"This Chat Action is not recognized: {action}")

    @staticmethod
    def _resolve_probe(state, nina, idx) -> ChatResult:
        shots = state.current_shots
        if idx >= len(shots):
            return ChatResult(nina_response="???")

        actual_shot = shots[idx]
        # accuracy degrades with Nina's sobriety
        tells_truth: bool = nina.bac > 0.18 or random.random() < 0.25
        tension_bump: float = 0.05

        if tells_truth:
            info: str = f"Shot {idx + 1} is {actual_shot.name}."
            response: str = "..."

            return ChatResult(nina_response=response, tension_delta=tension_bump, info_revealed=info)
        else:
            # She lies
            fake_names: list[str] = ["Vodka"]  # Placeholder
            fake = random.choice([name for name in fake_names if name != actual_shot.name])
            response: str = f"This is a lie. Pick {fake}."
            return ChatResult(nina_response=response, tension_delta=0.0, info_revealed=None)

    @staticmethod
    def _resolve_taunt(nina) -> ChatResult:
        tension_gain = 0.15
        affection_loss = 0.05
        mood_shift = None

        if nina.mood == Mood.SMUG:
            response: str = "Ouch."
            mood_shift = Mood.IRRITATED
        elif nina.mood == Mood.TIPSY:
            response: str = "Rude."
        elif nina.mood == Mood.MANIC:
            tension_gain += 0.10
            response = "Go fuck yourself lowkey"
        else:
            response = "..."

        return ChatResult(
            nina_response=response,
            tension_delta=tension_gain,
            affection_delta=-affection_loss,
            nina_mood_shifted=mood_shift
        )

    @staticmethod
    def _resolve_charm(state, nina) -> ChatResult:
        affection_gain = 0.12 if nina.bac > 0.15 else 0.07
        response: str = "Sure bro"
        if state.affection >= 0.7:
            # Already affectionate
            response: str = "Love you too pookie bear"
            affection_gain *= 0.5  # diminishing returns

        return ChatResult(nina_response=response, affection_delta=affection_gain)

    @staticmethod
    def _resolve_bargain(nina) -> ChatResult:
        # Acceptance probability based on mood and bac
        tension_bump: float = 0.0
        affection_bump: float = 0.0

        accept_chance: float = {
            Mood.SMUG: 0.2,
            Mood.TIPSY: 0.6,
            Mood.MANIC: 0.1,
            Mood.IRRITATED: 0.05,
            Mood.GONE: 0.8
        }.get(nina.mood, 0.3)

        if random.random() < accept_chance:
            # She accepts, reveals the other shots
            info: str = "Nina accepted the bargain."
            response: str = "yeah okay i guess"
            affection_bump += 0.05
        else:
            info: str = "Nina declined the bargain."
            response: str = "nope"
            tension_bump += 0.05

        return ChatResult(
            nina_response=response,
            tension_delta=tension_bump,
            affection_delta=affection_bump,
            info_revealed=info
        )

    @staticmethod
    def _resolve_confess(state, nina) -> ChatResult:
        affection_gain = 0.9

        response: str = "okay chud"

        if nina.mood == Mood.TIPSY and state.affection >= 0.5:
            # soft response
            response: str = "my bad chud"
            affection_gain *= 2

        return ChatResult(nina_response=response, affection_delta=affection_gain)

    @staticmethod
    def _resolve_silence() -> ChatResult:
        return ChatResult(
            nina_response="...",
            affection_delta=0.05,  # vulnerability signal reads as intimate
            tension_delta=-0.03  # de-escalates tension slightly
        )

    @staticmethod
    def _resolve_challenge(state, nina, idx) -> ChatResult:
        tension_bump: float = 0.05
        response: str = "nah bro"

        shots = state.current_shots
        if idx >= len(shots):
            return ChatResult(nina_response="?????")
        shot = shots[idx]
        # If the shot is high abv, pride forces her to pick it
        if shot.abv >= 0.4 and nina.mood in (Mood.SMUG, Mood.MANIC):
            response = "fine"
            nina._forced_pick_idx = idx
            tension_bump *= 2

        # If not, she calls your bluff
        return ChatResult(
            nina_response=response,
            tension_delta=tension_bump,
        )

    # TODO: add _resolve_talk()
