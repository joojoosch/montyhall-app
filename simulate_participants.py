"""Makes fake participant files to test the analysis before real data exists.

Use:      python simulate_participants.py [number of people] [output folder]
Example:  python simulate_participants.py 60 data/fake

The files have exactly the same format as the real ones (made with the same
code as the app). Each fake person has a known type, saved as "_true_type",
so I can check whether the analysis finds the types again. Real files never
have this field.
"""

import json
import os
import random
import sys

import config
import game
import session as sess

# How each type plays: probability of STAYING in each block, and their belief.
TYPES = {
    #                  control  pen_switch  pen_stay   belief_1 (mean, spread)
    "rational":        (0.15,    0.10,       0.05,     (67, 5)),
    "familiarity":     (0.85,    0.90,       0.85,     (50, 10)),  # stays even when it costs
    "equiprobability": (0.80,    0.90,       0.10,     (50, 4)),   # avoids the penalty
    "inconsistent":    (0.50,    0.10,       0.90,     (50, 20)),  # the reverse pattern
    "random":          (0.50,    0.50,       0.50,     (50, 30)),
}
# share of each type in the fake sample
MIX = {"rational": 0.2, "familiarity": 0.2, "equiprobability": 0.3,
       "inconsistent": 0.05, "random": 0.25}
DROPOUT_RATE = 0.15


def _belief(mean, spread, rng):
    return max(0, min(100, int(round(rng.gauss(mean, spread)))))


def make_participant(ptype, sequence, rng, mode="fake", dropout=False):
    stay_p = dict(zip(config.BLOCKS, TYPES[ptype][:3]))
    rec = sess.new_record(game.make_code(rng), mode, sequence)
    rec["_true_type"] = ptype
    rec["start_epoch"] -= rng.uniform(300, 900)  # pretend it took 5 to 15 minutes
    stop_at = rng.choice(sess.steps(mode)[1:-1]) if dropout else None
    while rec["step"] != "end":
        step = rec["step"]
        if step == stop_at:
            return rec  # dropout: file stays with completed = False
        if step.startswith("rules_"):
            idx = sess.block_index(step)
            block = sess.block_info(rec, idx)[0]
            questions = texts_comprehension(block)
            if rng.random() < 0.2:  # some people need a second try
                sess.check_comprehension(rec, block, questions, {q["id"]: "0" for q in questions})
            sess.check_comprehension(rec, block, questions, {q["id"]: q["correct"] for q in questions})
        elif step.startswith("block_"):
            idx = sess.block_index(step)
            block = sess.block_info(rec, idx)[0]
            while not sess.block_finished(rec, idx):
                trophy = game.draw_trophy_door(rng)
                pick = rng.choice(config.DOORS)
                opened = game.host_opens(pick, trophy, rng)
                choice = "stay" if rng.random() < stay_p[block] else "switch"
                sess.record_trial(rec, idx, trophy, pick, opened, choice,
                                  rng.randint(600, 4000), rng.randint(500, 5000))
        elif step.startswith("belief_"):
            mean, spread = TYPES[ptype][3]
            rec[f"belief_{step[-1]}"] = _belief(mean, spread, rng)
            rec[f"belief_{step[-1]}_time"] = sess.now_iso()
        elif step == "prior":
            rec["prior_knowledge"] = rng.choices(
                ["Yes, I knew it before", "I recognised it during the study", "No"], [1, 2, 6])[0]
        elif step == "reason":
            rec["first_game_reason"] = rng.choices(
                ["better_choice", "equal_chance", "try_out", "gut_feeling", "no_reason"],
                [3, 3, 2, 3, 1])[0]
        elif step == "thresh":
            for block in rec["threshold_order"]:
                ttype = rng.choices(list(sess.THRESH_TYPES), [6, 1, 1])[0]
                sess.record_threshold(rec, block, ttype, rng.randint(0, 100))
        elif step == "demo":
            rec["age"] = rng.randint(19, 35)
            rec["gender"] = rng.choice(["female", "male", "diverse", "prefer not to say"])
        sess.advance(rec)
    return rec


def texts_comprehension(block):
    import texts
    return texts.COMPREHENSION[block]


def make_sample(n, rng=None, mode="fake"):
    rng = rng or random.Random()
    recs, counts = [], {"A": 0, "B": 0}
    types = list(MIX)
    for _ in range(n):
        ptype = rng.choices(types, [MIX[t] for t in types])[0]
        seq = game.assign_sequence(counts, rng)
        counts[seq] += 1
        recs.append(make_participant(ptype, seq, rng, mode, dropout=rng.random() < DROPOUT_RATE))
    return recs


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    out = sys.argv[2] if len(sys.argv) > 2 else "data/fake"
    os.makedirs(out, exist_ok=True)
    for rec in make_sample(n):
        path = os.path.join(out, f"{rec['participant_id']}_{rec['sequence']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f"{n} fake participants written to {out}/")


if __name__ == "__main__":
    main()
