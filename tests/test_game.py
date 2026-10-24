"""Tests for game.py. Run with:  pytest -q"""

import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import game  # noqa: E402

N = 100_000


def _seeded(seed=12345):
    return random.Random(seed)


def _approx(x, target, tol):
    return abs(x - target) < tol


def test_host_never_opens_pick_or_trophy():
    rng = _seeded(1)
    for _ in range(N):
        trophy = game.draw_trophy_door(rng)
        pick = rng.choice(config.DOORS)
        opened = game.host_opens(pick, trophy, rng)
        assert opened != pick
        assert opened != trophy
        assert opened in config.DOORS


def test_host_is_50_50_when_pick_is_trophy():
    rng = _seeded(2)
    for pick in config.DOORS:
        counts = Counter(game.host_opens(pick, pick, rng) for _ in range(N // 3))
        others = [d for d in config.DOORS if d != pick]
        assert set(counts) == set(others)
        share = counts[others[0]] / sum(counts.values())
        assert _approx(share, 0.5, 0.015), share


def test_host_with_system_rng_also_random():
    # The real app uses SystemRandom; check it is not always the same door.
    seen = {game.host_opens(1, 1) for _ in range(200)}
    assert seen == {2, 3}


def test_trophy_door_uniform():
    rng = _seeded(3)
    counts = Counter(game.draw_trophy_door(rng) for _ in range(N))
    for d in config.DOORS:
        assert _approx(counts[d] / N, 1 / 3, 0.01), counts


def test_switch_wins_two_thirds_stay_one_third():
    rng = _seeded(4)
    wins = {"stay": 0, "switch": 0}
    for _ in range(N):
        trophy = game.draw_trophy_door(rng)
        pick = rng.choice(config.DOORS)
        opened = game.host_opens(pick, trophy, rng)
        for choice in wins:
            res = game.resolve_trial(config.CONTROL, trophy, pick, opened, choice)
            wins[choice] += res["won"]
    assert _approx(wins["switch"] / N, 2 / 3, 0.01), wins
    assert _approx(wins["stay"] / N, 1 / 3, 0.01), wins


def test_points_table_all_12_combinations():
    expected = {
        (config.CONTROL, "stay", True): 100,
        (config.CONTROL, "switch", True): 100,
        (config.CONTROL, "stay", False): 0,
        (config.CONTROL, "switch", False): 0,
        (config.PEN_SWITCH, "stay", True): 100,
        (config.PEN_SWITCH, "switch", True): 75,
        (config.PEN_SWITCH, "stay", False): 0,
        (config.PEN_SWITCH, "switch", False): 0,
        (config.PEN_STAY, "stay", True): 75,
        (config.PEN_STAY, "switch", True): 100,
        (config.PEN_STAY, "stay", False): 0,
        (config.PEN_STAY, "switch", False): 0,
    }
    assert len(expected) == 12
    for (block, choice, won), pts in expected.items():
        assert game.points_for(block, choice, won) == pts, (block, choice, won)


def test_resolve_trial_fields():
    # pick 1, trophy 2, host must open 3; switching goes to 2 and wins
    res = game.resolve_trial(config.PEN_SWITCH, trophy_door=2, first_pick=1,
                             host_opened=3, choice="switch")
    assert res == {"choice": "switch", "final_door": 2, "switched": 1, "won": 1,
                   "penalty_applied": 1, "points": 75}
    res = game.resolve_trial(config.PEN_SWITCH, 2, 1, 3, "stay")
    assert res["won"] == 0 and res["points"] == 0 and res["penalty_applied"] == 0


def test_invalid_inputs_rejected():
    for bad in [lambda: game.points_for("x", "stay", True),
                lambda: game.points_for(config.CONTROL, "maybe", True),
                lambda: game.host_opens(4, 1),
                lambda: game.remaining_door(2, 2),
                lambda: game.block_plan("C")]:
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_block_plan():
    assert game.block_plan("A") == [(config.CONTROL, 1, 5), (config.PEN_SWITCH, 2, 10),
                                    (config.PEN_STAY, 3, 10)]
    assert game.block_plan("B") == [(config.CONTROL, 1, 5), (config.PEN_STAY, 2, 10),
                                    (config.PEN_SWITCH, 3, 10)]
    assert game.total_trials() == 25


def test_sequence_assignment_balanced():
    rng = _seeded(5)
    counts = {"A": 0, "B": 0}
    for _ in range(1001):
        counts[game.assign_sequence(counts, rng)] += 1
        assert abs(counts["A"] - counts["B"]) <= 1
    assert game.assign_sequence({"A": 3, "B": 5}) == "A"
    assert game.assign_sequence({"A": 5, "B": 3}) == "B"
    ties = Counter(game.assign_sequence({}, rng) for _ in range(10_000))
    assert _approx(ties["A"] / 10_000, 0.5, 0.03)


def test_make_code():
    rng = _seeded(6)
    codes = {game.make_code(rng) for _ in range(10_000)}
    assert len(codes) > 9_990  # collisions extremely rare (31^6 ≈ 887 million)
    for c in list(codes)[:500]:
        assert len(c) == 6
        assert not set(c) & set("0O1IL")


def test_validate_belief():
    assert game.validate_belief(0) == 0
    assert game.validate_belief(67) == 67
    assert game.validate_belief(100) == 100
    assert game.validate_belief(50.0) == 50
    for bad in [None, -1, 101, 50.5, "50", True, [50]]:
        try:
            game.validate_belief(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted invalid belief {bad!r}")
