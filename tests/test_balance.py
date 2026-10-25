# Tests for balance.py: A and B stay even among people who finish.

import os
import random
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from balance import Balancer  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_simultaneous_starts_get_different_sequences():
    # 20 people press "Continue" at the same moment, nobody finished yet
    b = Balancer()
    got = []

    def start(i):
        seq, _ = b.assign("real", f"P{i}", lambda: {"A": 0, "B": 0})
        got.append(seq)

    threads = [threading.Thread(target=start, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert got.count("A") == got.count("B") == 10


def test_dropouts_dont_unbalance_completed():
    # 300 simulated studies: people arrive, play for 8-20 min, 20% drop out.
    rng = random.Random(42)
    worst = 0
    for _ in range(300):
        clock = Clock()
        b = Balancer(timeout_s=45 * 60, clock=clock)
        completed = {"A": 0, "B": 0}
        events = []  # (finish time, pid, seq, drops out)
        for i in range(60):
            clock.t = i * rng.uniform(0, 240)          # arrivals, sometimes in bursts
            # finish everyone whose time has come
            for ev in sorted(e for e in events if e[0] <= clock.t):
                events.remove(ev)
                if not ev[3]:
                    completed[ev[2]] += 1
                    b.finish(ev[1])
            seq, _ = b.assign("real", f"P{i}", lambda: dict(completed), rng)
            events.append((clock.t + rng.uniform(480, 1200), f"P{i}", seq, rng.random() < 0.2))
        for ev in sorted(events):
            if not ev[3]:
                completed[ev[2]] += 1
        worst = max(worst, abs(completed["A"] - completed["B"]))
    # pure coin flipping would often be off by 8 or more with ~48 people
    assert worst <= 4, worst


def test_finished_people_are_not_counted_twice():
    b = Balancer()
    completed = {"A": 0, "B": 0}
    seq, _ = b.assign("real", "P1", lambda: dict(completed))
    completed[seq] += 1
    b.finish("P1")
    seq2, counts = b.assign("real", "P2", lambda: dict(completed))
    assert counts[seq] == 1 and seq2 != seq


def test_pilot_and_real_are_balanced_separately():
    b = Balancer()
    b.assign("pilot", "X1", lambda: {"A": 0, "B": 0})
    _, counts = b.assign("real", "R1", lambda: {"A": 0, "B": 0})
    assert counts == {"A": 0, "B": 0}
