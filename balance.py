# Keeps sequence A and B balanced.
#
# What counts: people who COMPLETED the study (read from the data repo) plus
# people who are playing right now. Dropouts don't count, otherwise A and B
# could end up uneven among the people I actually analyse.
#
# All participants run in the same app process on Streamlit Cloud, so one
# shared Balancer with a lock is enough: two people who click "Continue" in
# the same second are handled one after the other and get different sequences.

import threading
import time

import config
import game


class Balancer:

    def __init__(self, timeout_s=None, clock=time.time):
        self.lock = threading.Lock()
        self.clock = clock
        self.timeout_s = timeout_s or config.ACTIVE_TIMEOUT_MIN * 60
        self.active = {}  # participant id -> (mode, sequence, start time)

    def _active_counts(self, mode):
        now = self.clock()
        # forget people who started too long ago without finishing (dropouts)
        self.active = {pid: v for pid, v in self.active.items()
                       if now - v[2] < self.timeout_s}
        counts = {"A": 0, "B": 0}
        for m, seq, _ in self.active.values():
            if m == mode:
                counts[seq] += 1
        return counts

    def assign(self, mode, pid, get_completed, rng=None):
        """Returns (sequence, counts used). get_completed() -> {"A": n, "B": n}."""
        with self.lock:
            completed = get_completed()
            active = self._active_counts(mode)
            counts = {s: completed.get(s, 0) + active[s] for s in ("A", "B")}
            seq = game.assign_sequence(counts, rng)
            self.active[pid] = (mode, seq, self.clock())
            return seq, counts

    def finish(self, pid):
        # called once the completed marker is saved, so the person isn't counted twice
        with self.lock:
            self.active.pop(pid, None)
