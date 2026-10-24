# Game rules of the Monty Hall experiment (no Streamlit here, so it's easy to test).
#
# Randomness: SystemRandom uses the computer's own random source, with no seed,
# so nobody can predict the doors. The tests pass their own seeded rng instead.

import random

import config

_SYSTEM_RNG = random.SystemRandom()


def _rng(rng):
    return rng if rng is not None else _SYSTEM_RNG


# ---------- one game ----------

def draw_trophy_door(rng=None):
    # new random trophy door for every game
    return _rng(rng).choice(config.DOORS)


def host_opens(first_pick, trophy_door, rng=None):
    # The host never opens the picked door or the trophy door.
    # If the pick IS the trophy door, two doors are left and he picks one at random.
    _check_door(first_pick)
    _check_door(trophy_door)
    options = [d for d in config.DOORS if d != first_pick and d != trophy_door]
    return _rng(rng).choice(options)


def remaining_door(first_pick, host_opened):
    # the closed door you get when you switch
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
    # switching costs in pen_switch, staying costs in pen_stay
    _check_block(block)
    return (block == config.PEN_SWITCH and choice == "switch") or (
        block == config.PEN_STAY and choice == "stay"
    )


def points_for(block, choice, won):
    # win = 100, win with the penalised option = 75, loss = 0
    _check_block(block)
    if choice not in ("stay", "switch"):
        raise ValueError(f"invalid choice {choice!r}")
    if not won:
        return 0
    if is_penalised(block, choice):
        return config.POINTS_WIN - config.PENALTY
    return config.POINTS_WIN


def resolve_trial(block, trophy_door, first_pick, host_opened, choice):
    # everything that is saved about the result of one game
    door = final_door(first_pick, host_opened, choice)
    won = door == trophy_door
    return {
        "choice": choice,
        "final_door": door,
        "switched": int(choice == "switch"),
        "won": int(won),
        # 1 only if the penalty really cost points (a win with the penalised option)
        "penalty_applied": int(won and is_penalised(block, choice)),
        "points": points_for(block, choice, won),
    }


# ---------- whole session ----------

def block_plan(sequence):
    # [(block, block_order, number of games), ...] for sequence A or B
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
    # give the sequence with fewer people so far, random if it's a tie
    counts = counts or {}
    a, b = counts.get("A", 0), counts.get("B", 0)
    if a < b:
        return "A"
    if b < a:
        return "B"
    return _rng(rng).choice(("A", "B"))


def make_code(rng=None):
    # 6-character code = participant ID (no 0/O/1/I/L, so it's easy to read)
    r = _rng(rng)
    return "".join(r.choice(config.CODE_ALPHABET) for _ in range(config.CODE_LENGTH))


def validate_belief(value):
    # belief answer must be a whole number from 0 to 100
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


def _check_door(door):
    if door not in config.DOORS:
        raise ValueError(f"invalid door {door!r}")


def _check_block(block):
    if block not in config.BLOCKS:
        raise ValueError(f"invalid block {block!r}")
