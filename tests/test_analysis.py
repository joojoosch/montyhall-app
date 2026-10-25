# Tests for analysis.py. They also lock the rules fixed on 25 Oct 2026:
# if someone changes a test direction or threshold, these tests fail.

import os
import random
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analysis as an  # noqa: E402
import simulate_participants as sim  # noqa: E402


def test_rules_are_the_fixed_ones():
    assert an.TESTS == {"H1": "two-sided", "H2": "two-sided", "H3a": "two-sided", "H3b": "greater"}
    assert an.H1_MAIN == "all"
    assert an.ALPHA == 0.05
    assert (an.STAYER_MIN, an.BACKUP_MOST, an.THRESHOLD) == (4, 3, 7)
    assert an.ROBUST_THRESHOLDS == (6, 8)
    assert an.BAND == (43, 57) and an.WIDE_BAND == (40, 60)


def test_thresholds_from_the_design_doc():
    # H1: 17 or fewer switchers of 50 rejects, 18 does not
    assert an.binom(17, 50, 0.5, "two-sided")["p"] < 0.05
    assert an.binom(18, 50, 0.5, "two-sided")["p"] > 0.05
    # H3a: 21 of 30 rejects (two-sided), 20 does not
    assert an.binom(21, 30, 0.5, "two-sided")["p"] < 0.05
    assert an.binom(20, 30, 0.5, "two-sided")["p"] > 0.05
    # H3b: 2 of 10 against 2.95% rejects (one-sided), 1 does not
    chance = an.chance_one_pattern(7)
    assert abs(chance - 0.0295) < 0.0001
    assert an.binom(2, 10, chance, "greater")["p"] < 0.05
    assert an.binom(1, 10, chance, "greater")["p"] > 0.05


def test_confidence_interval_is_two_sided_also_for_h3b():
    lo, hi = an.binom(2, 10, an.chance_one_pattern(), "greater")["ci"]
    assert 0.02 < lo < 0.03 and 0.55 < hi < 0.56   # exact 95% interval for 2 of 10


def test_patterns():
    # (stays in switching-penalty block, stays in staying-penalty block)
    assert an.pattern(9, 8) == "stays in both"
    assert an.pattern(8, 2) == "stay, then switch"
    assert an.pattern(1, 0) == "switches in both"
    assert an.pattern(2, 9) == "switch, then stay"
    assert an.pattern(9, 5) == "mixed"          # clear in one block only
    assert an.pattern(6, 6) == "mixed"
    assert an.pattern(7, 7) == "stays in both"  # exactly 7 of 10 counts
    assert an.pattern(6, 6, t=6) == "stays in both"


def test_belief_bands():
    assert an.band(42) == "below" and an.band(43) == "50/50 band"
    assert an.band(57) == "50/50 band" and an.band(58) == "above"
    assert an.band(40, an.WIDE_BAND) == "50/50 band" and an.band(61, an.WIDE_BAND) == "above"


def _fake_folder(n=200, seed=3):
    d = tempfile.mkdtemp()
    for rec in sim.make_sample(n, random.Random(seed)):
        with open(os.path.join(d, f"{rec['participant_id']}_{rec['sequence']}.json"), "w") as f:
            json.dump(rec, f)
    return d


def test_end_to_end_on_fake_data_finds_the_types():
    folder = _fake_folder()
    out = tempfile.mkdtemp()
    df = an.run(folder, out)
    for name in ("results.md", "participants_summary.csv", "crosstab_main.csv",
                 "learning.csv", "scatter.png"):
        assert os.path.exists(os.path.join(out, name)), name
    expected = {"familiarity": "stays in both", "equiprobability": "stay, then switch",
                "rational": "switches in both", "inconsistent": "switch, then stay"}
    for ptype, pat in expected.items():
        d = df[df._true_type == ptype]
        assert len(d) > 0
        assert (d.pattern == pat).mean() >= 0.8, (ptype, (d.pattern == pat).mean())
    # random clickers mostly end up unclassified
    assert (df[df._true_type == "random"].pattern == "mixed").mean() >= 0.7
    # only complete participants are analysed
    assert df.participant_id.is_unique and len(df) < 200


def test_h1_without_try_out_leaves_them_out():
    folder = _fake_folder(80, seed=5)
    _, complete = an.load(folder)
    import pandas as pd
    df = pd.DataFrame([an.summarise(r) for r in complete])
    main, check = an.test_h1(df), an.test_h1(df, without_try_out=True)
    assert main["n"] == len(df)
    assert check["n"] == int((df.first_game_reason != "try_out").sum()) < main["n"]
