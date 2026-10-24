"""Pure game logic for the Monty Hall experiment. No Streamlit in here.

Every function that uses randomness takes an optional `rng`. By default it
uses random.SystemRandom (OS entropy, no seed, cannot be reproduced or
predicted). Tests pass a seeded random.Random so they are repeatable.
"""

import random

import config

_SYSTEM_RNG = random.SystemRandom()


def _rng(rng):
    return rng if rng is not None else _SYSTEM_RNG


# ---------- one trial ----------

def draw_trophy_door(rng=None):
    """Trophy door, uniform over 1-3, new on every trial."""
    return _rng(rng).choice(config.DOORS)


def host_opens(first_pick, trophy_door, rng=None):
    """Door the host opens: never the picked door, never the trophy door.

    If the pick is the trophy door, both other doors are empty and the host
    chooses between them at random (50/50).
    """
    _check_door(first_pick)
    _check_door(trophy_door)
    options = [d for d in config.DOORS if d != first_pick and d != trophy_door]
    return _rng(rng).choice(options)


def remaining_door(first_pick, host_opened):
    """The one closed door that is not the participant's pick."""
    if first_pick == host_opened:
        raise ValueError("host cannot open the picked door")
    (door,) = [d for d in config.DOORS if d not in (first_pick, host_opened)]
    return door


def final_door(first_pick, host_opened, choice):
    if choice == "stay":
        return first_pick
    if choice == "switch":
        return remaining_door(first_pick, host_opened)
    raise ValueError(f"choice must be 'stay' or 'switch', got {choice!r}")


def is_penalised(block, choice):
    """True if this choice carries the penalty in this block."""
    _check_block(block)
    return (block == config.PEN_SWITCH and choice == "switch") or (
        block == config.PEN_STAY and choice == "stay"
    )


def points_for(block, choice, won):
    """Points for one trial (see the points table in the brief)."""
    _check_block(block)
    if choice not in ("stay", "switch"):
        raise ValueError(f"invalid choice {choice!r}")
    if not won:
        return 0
    if is_penalised(block, choice):
        return config.POINTS_WIN - config.PENALTY
    return config.POINTS_WIN


def resolve_trial(block, trophy_door, first_pick, host_opened, choice):
    """Outcome of a finished trial as a dict of the data fields."""
    door = final_door(first_pick, host_opened, choice)
    won = door == trophy_door
    pts = points_for(block, choice, won)
    return {
        "choice": choice,
        "final_door": door,
        "switched": int(choice == "switch"),
        "won": int(won),
        # 1 only when the penalty actually reduced the points (a win through
        # the penalised option). The raw choice is stored anyway.
        "penalty_applied": int(won and is_penalised(block, choice)),
        "points": pts,
    }


# ---------- session structure ----------

def block_plan(sequence):
    """List of (block, block_order, n_trials) for a sequence 'A' or 'B'."""
    if sequence not in config.SEQUENCES:
        raise ValueError(f"unknown sequence {sequence!r}")
    plan = []
    for order, block in enumerate(config.SEQUENCES[sequence], start=1):
        n = config.N_CONTROL if block == config.CONTROL else config.N_PENALTY
        plan.append((block, order, n))
    return plan


def total_trials():
    return config.N_CONTROL + 2 * config.N_PENALTY


def assign_sequence(counts=None, rng=None):
    """Balanced assignment: the sequence with fewer participants so far.

    `counts` is e.g. {"A": 12, "B": 11}. Ties (or no counts) are broken at
    random.
    """
    counts = counts or {}
    a, b = counts.get("A", 0), counts.get("B", 0)
    if a < b:
        return "A"
    if b < a:
        return "B"
    return _rng(rng).choice(("A", "B"))


def make_code(rng=None):
    """Random 6-character participant ID / personal code."""
    r = _rng(rng)
    return "".join(r.choice(config.CODE_ALPHABET) for _ in range(config.CODE_LENGTH))


def validate_belief(value):
    """Return the belief as int 0-100, or raise ValueError."""
    if value is None or isinstance(value, bool):
        raise ValueError("belief answer missing")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("belief must be a whole number")
        value = int(value)
    if not isinstance(value, int):
        raise ValueError("belief must be a number")
    if not 0 <= value <= 100:
        raise ValueError("belief must be between 0 and 100")
    return value


# ---------- helpers ----------

def _check_door(door):
    if door not in config.DOORS:
        raise ValueError(f"invalid door {door!r}")


def _check_block(block):
    if block not in config.BLOCKS:
        raise ValueError(f"invalid block {block!r}")
