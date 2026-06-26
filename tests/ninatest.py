# tests/test_ninoula.py
import pytest
from base.game.ninoula.ninoula import Ninoula
from base.game.ninoula.mood_engine import Mood


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_nina():
    return Ninoula(runs_played=0)


@pytest.fixture
def drunk_nina():
    n = Ninoula()
    n.emotion.bac = 0.28
    n.emotion.engagement = 0.7
    n._mood_eng.evaluate(n.emotion, force=True)
    return n


SHOTS_MIXED = [
    {"name": "Red Wine", "abv": 14, "hidden": False, "type": "normal",
     "flavor_tags": ["Sweet", "Grape"], "_table_position": 0},
    {"name": "Absinthe", "abv": 68, "hidden": False, "type": "normal",
     "flavor_tags": ["Anise", "Void"], "_table_position": 1},
    {"name": "Unknown", "abv": 40, "hidden": True, "type": "normal",
     "flavor_tags": [], "_table_position": 2},
]

SHOTS_WITH_SIN = [
    {"name": "Bourbon", "abv": 40, "hidden": False, "type": "normal", "_table_position": 0},
    {"name": "???", "abv": 0, "hidden": True, "type": "normal", "_table_position": 1},
    {"name": "", "abv": 0, "hidden": True, "type": "sin", "_table_position": 2},
]


# ── Mood Tests ─────────────────────────────────────────────────────────────────

class TestMoodTransitions:
    def test_fresh_nina_is_smug(self, fresh_nina):
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion)
        assert fresh_nina.mood.base == Mood.SMUG

    def test_high_bac_makes_tipsy(self, fresh_nina):
        fresh_nina.emotion.bac = 0.22
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.TIPSY

    def test_very_high_bac_makes_gone(self, fresh_nina):
        fresh_nina.emotion.bac = 0.42
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.GONE

    def test_high_tension_with_bac_makes_manic(self, fresh_nina):
        fresh_nina.emotion.bac = 0.32
        fresh_nina.emotion.tension = 0.75
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.MANIC

    def test_high_suspicion_makes_irritated_when_sober(self, fresh_nina):
        fresh_nina.emotion.suspicion = 0.80
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.IRRITATED

    def test_mood_resistance_prevents_instant_transition(self, fresh_nina):
        """Mood shouldn't change on first evaluation when resistance is active."""
        assert fresh_nina.mood.base == Mood.SMUG
        fresh_nina.emotion.bac = 0.22
        # First evaluation: resistance may block transition
        ms1 = fresh_nina._mood_eng.evaluate(fresh_nina.emotion)
        # Second evaluation: resistance lowered
        ms2 = fresh_nina._mood_eng.evaluate(fresh_nina.emotion)
        # By second eval, should be TIPSY
        assert ms2.base == Mood.TIPSY

    def test_tipsy_soft_requires_affection(self, fresh_nina):
        fresh_nina.emotion.bac = 0.22
        fresh_nina.emotion.affection = 0.60
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.sub == "TIPSY_SOFT"

    def test_tipsy_sloppy_at_high_bac(self, fresh_nina):
        fresh_nina.emotion.bac = 0.34
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.sub == "TIPSY_SLOPPY"

    def test_bored_smug_when_engagement_low(self, fresh_nina):
        fresh_nina.emotion.engagement = 0.15
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.sub == "SMUG_BORED"


# ── Pick Logic Tests ───────────────────────────────────────────────────────────

class TestPickLogic:
    def test_smug_nina_avoids_high_abv(self, fresh_nina):
        """Sober Smug Nina should not pick Absinthe (68% ABV)."""
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.SMUG

        # Run 100 picks, absinthe (idx 1) should rarely be chosen
        picks = []
        for _ in range(100):
            fresh_nina.begin_decision(SHOTS_MIXED)
            d = fresh_nina.decide(SHOTS_MIXED)
            picks.append(d.chosen_idx)

        absinthe_rate = picks.count(1) / 100
        assert absinthe_rate < 0.15, f"Smug Nina picked Absinthe {absinthe_rate:.0%} of the time"

    def test_manic_nina_prefers_high_abv(self, fresh_nina):
        """Manic Nina should prefer the high-ABV shot."""
        fresh_nina.emotion.bac = 0.22
        fresh_nina.emotion.engagement = 0.90
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.MANIC

        picks = []
        for _ in range(100):
            fresh_nina.begin_decision(SHOTS_MIXED)
            d = fresh_nina.decide(SHOTS_MIXED)
            picks.append(d.chosen_idx)

        absinthe_rate = picks.count(1) / 100
        assert absinthe_rate > 0.50, f"Manic Nina should prefer Absinthe"

    def test_nina_avoids_sin_glass_unless_gone(self, fresh_nina):
        """Nina should never pick the Sin glass unless Gone."""
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base != Mood.GONE

        picks = []
        for _ in range(50):
            fresh_nina.begin_decision(SHOTS_WITH_SIN)
            d = fresh_nina.decide(SHOTS_WITH_SIN)
            picks.append(d.chosen_idx)

        sin_rate = picks.count(2) / 50
        assert sin_rate == 0.0, f"Nina picked the Sin glass {sin_rate:.0%} of the time"

    def test_gone_nina_is_random(self, fresh_nina):
        """Gone Nina should have roughly uniform pick distribution."""
        fresh_nina.emotion.bac = 0.43
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)
        assert fresh_nina.mood.base == Mood.GONE

        picks = []
        for _ in range(300):
            fresh_nina.begin_decision(SHOTS_MIXED)
            d = fresh_nina.decide(SHOTS_MIXED)
            picks.append(d.chosen_idx)

        # Each glass should be picked ~33% of the time ±15%
        for idx in [0, 1, 2]:
            rate = picks.count(idx) / 300
            assert 0.18 < rate < 0.48, f"Gone Nina idx {idx} rate={rate:.2f} not uniform"


# ── Emotion Variable Tests ─────────────────────────────────────────────────────

class TestEmotionVariables:
    def test_charm_increases_affection(self, fresh_nina):
        before = fresh_nina.emotion.affection
        fresh_nina.apply_charm()
        assert fresh_nina.emotion.affection > before

    def test_charm_diminishing_returns(self, fresh_nina):
        fresh_nina.emotion.affection = 0.85
        delta1 = fresh_nina.apply_charm()
        fresh_nina.emotion.affection = 0.30
        delta2 = fresh_nina.apply_charm()
        assert delta1 < delta2  # smaller gain at high affection

    def test_taunt_raises_tension(self, fresh_nina):
        before = fresh_nina.emotion.tension
        fresh_nina.apply_taunt()
        assert fresh_nina.emotion.tension > before

    def test_trick_raises_suspicion(self, fresh_nina):
        before = fresh_nina.emotion.suspicion
        fresh_nina.react_to_player_pick(
            shot={"name": "Bourbon", "abv": 40, "hidden": False,
                  "type": "normal", "_table_position": 0},
            decision_ms=3000,
            cards_played=["palmed_switch"],
            round_number=1,
        )
        assert fresh_nina.emotion.suspicion > before

    def test_brave_pick_increases_respect(self, fresh_nina):
        before = fresh_nina.emotion.respect
        fresh_nina.react_to_player_pick(
            shot={"name": "Everclear", "abv": 95, "hidden": False,
                  "type": "normal", "_table_position": 0},
            decision_ms=1500,
            cards_played=[],
            round_number=3,
        )
        assert fresh_nina.emotion.respect > before

    def test_low_streak_reduces_engagement(self, fresh_nina):
        """Three consecutive safe picks should lower engagement."""
        for _ in range(3):
            fresh_nina.react_to_player_pick(
                shot={"name": "Beer", "abv": 5, "hidden": False,
                      "type": "normal", "_table_position": 0},
                decision_ms=5000,
                cards_played=[],
                round_number=1,
            )
        assert fresh_nina.emotion.engagement < 0.50

    def test_drinking_high_abv_raises_engagement(self, fresh_nina):
        before = fresh_nina.emotion.engagement
        fresh_nina.process_drink(70)
        assert fresh_nina.emotion.engagement > before

    def test_bac_clamps_at_max(self, fresh_nina):
        for _ in range(100):
            fresh_nina.process_drink(80)
        assert fresh_nina.emotion.bac <= 0.50


# ── Integration Tests ──────────────────────────────────────────────────────────

class TestNinolaIntegration:
    def test_full_round_sequence(self, fresh_nina):
        """Simulate a full round without crashing."""
        shots = SHOTS_MIXED

        # Player picks
        fresh_nina.react_to_player_pick(
            shot=shots[0], decision_ms=4000, cards_played=[], round_number=1
        )

        # Nina decides
        fresh_nina.begin_decision(shots)
        decision = fresh_nina.decide(shots, player_picked_idx=0)

        assert decision.chosen_idx != 0  # not the player's glass
        assert 0 <= decision.chosen_idx < len(shots)

        # Nina drinks
        shot = shots[decision.chosen_idx]
        drink_key = fresh_nina.process_drink(shot["abv"])
        assert isinstance(drink_key, str)

    def test_nina_state_is_serialisable(self, fresh_nina):
        """Nina's state should survive a round-trip through dict."""
        fresh_nina.emotion.bac = 0.15
        fresh_nina.emotion.affection = 0.45
        fresh_nina._mood_eng.evaluate(fresh_nina.emotion, force=True)

        d = fresh_nina.to_dict()
        restored = Ninoula.from_dict(d)

        assert abs(restored.emotion.bac - 0.15) < 0.001
        assert abs(restored.emotion.affection - 0.45) < 0.001
