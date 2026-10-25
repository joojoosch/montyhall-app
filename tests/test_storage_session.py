# Tests for storage.py, session.py and export.py. Run with:  pytest -q

import base64
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import export  # noqa: E402
import game  # noqa: E402
import session as sess  # noqa: E402
import texts  # noqa: E402
from storage import GitHubStorage, LocalStorage, file_path  # noqa: E402


# ---------- a fake GitHub contents API ----------

class Resp:
    def __init__(self, status, data=None):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data


class FakeGitHub:
    # keeps files in memory and behaves like GitHub, can also fake errors

    def __init__(self):
        self.files = {}          # path -> (sha, content_b64)
        self.fail_next = []      # list of status codes to return on next PUTs
        self.counter = 0
        self.puts = 0

    def _path(self, url):
        return url.split("/contents/", 1)[1]

    def get(self, url, headers=None, params=None, timeout=None):
        path = self._path(url)
        if path in self.files:
            sha, content = self.files[path]
            return Resp(200, {"sha": sha, "content": content})
        prefix = path.rstrip("/") + "/"
        listing = [{"name": p[len(prefix):]} for p in self.files if p.startswith(prefix)]
        return Resp(200, listing) if listing else Resp(404, {})

    def put(self, url, headers=None, json=None, timeout=None):
        self.puts += 1
        if self.fail_next:
            return Resp(self.fail_next.pop(0), {})
        path = self._path(url)
        current = self.files.get(path)
        if current and json.get("sha") != current[0]:
            return Resp(409 if json.get("sha") else 422, {})
        if not current and json.get("sha"):
            return Resp(422, {})
        self.counter += 1
        sha = f"sha{self.counter}"
        self.files[path] = (sha, json["content"])
        return Resp(200 if current else 201, {"content": {"sha": sha}})

    def read(self, path):
        return __import__("json").loads(base64.b64decode(self.files[path][1]))


def _gh(fake):
    return GitHubStorage("me/data", "TOKEN", http=fake, sleep=lambda s: None)


def _full_record(seq="A", mode="pilot", choose=None, rng=None):
    # plays a whole session through session.py, like the app does
    rng = rng or random.Random(0)
    rec = sess.new_record(game.make_code(rng), mode, seq)
    while rec["step"] != "end":
        step = rec["step"]
        if step.startswith("rules_"):
            idx = sess.block_index(step)
            block, _, _ = sess.block_info(rec, idx)
            qs = texts.COMPREHENSION[block]
            assert not sess.check_comprehension(rec, block, qs, {q["id"]: None for q in qs})
            assert sess.check_comprehension(rec, block, qs, {q["id"]: q["correct"] for q in qs})
        if step.startswith("block_"):
            idx = sess.block_index(step)
            while not sess.block_finished(rec, idx):
                trophy = game.draw_trophy_door(rng)
                pick = rng.choice(config.DOORS)
                opened = game.host_opens(pick, trophy, rng)
                block = sess.block_info(rec, idx)[0]
                choice = choose(block) if choose else rng.choice(["stay", "switch"])
                sess.record_trial(rec, idx, trophy, pick, opened, choice, 1000, 800)
        if step.startswith("belief_"):
            rec[step] = 50
        if step == "reason":
            rec["first_game_reason"] = "try_out"
        sess.advance(rec)
    return rec


# ---------- GitHub storage ----------

def test_github_create_update_load_roundtrip():
    fake = FakeGitHub()
    s = _gh(fake)
    rec = sess.new_record("ABC234", "pilot", "A")
    assert s.save(rec)
    rec["belief_1"] = 67
    assert s.save(rec)  # update uses the stored sha
    path = file_path("pilot", "ABC234", "A")
    assert fake.read(path)["belief_1"] == 67
    loaded = _gh(fake).load("pilot", "ABC234", "A")  # new session, e.g. after refresh
    assert loaded == json.loads(json.dumps(rec))


def test_github_retries_on_conflict_and_server_error():
    fake = FakeGitHub()
    s = _gh(fake)
    rec = sess.new_record("ABC234", "pilot", "A")
    fake.fail_next = [409, 502, 409]
    assert s.save(rec)
    assert fake.puts == 4


def test_github_recovers_when_sha_is_outdated():
    # e.g. a save succeeded on GitHub but the answer got lost on the way back
    fake = FakeGitHub()
    s = _gh(fake)
    rec = sess.new_record("ABC234", "pilot", "A")
    assert s.save(rec)
    other = _gh(fake)
    other.load("pilot", "ABC234", "A")
    rec["total_points"] = 100
    assert other.save(rec)          # file now has a newer sha
    rec["total_points"] = 200
    assert s.save(rec)              # s has the old sha -> 409 -> refresh -> ok
    assert fake.read(file_path("pilot", "ABC234", "A"))["total_points"] == 200


def test_github_gives_up_and_reports_failure():
    fake = FakeGitHub()
    s = _gh(fake)
    fake.fail_next = [500] * 10
    assert s.save(sess.new_record("ABC234", "pilot", "A")) is False
    fake2 = FakeGitHub()
    fake2.fail_next = [401]
    assert _gh(fake2).save(sess.new_record("ABC234", "pilot", "A")) is False
    assert fake2.puts == 1  # wrong token: no pointless retries


def test_github_counts_only_completed_and_separates_pilot_real():
    fake = FakeGitHub()
    s = _gh(fake)
    assert s.count_completed("real") == {"A": 0, "B": 0}
    for i, seq in enumerate("AABAB"):
        rec = sess.new_record(f"P{i}AAAA", "pilot", seq)
        s.save(rec)
        if i < 4:                      # P4 drops out: not counted
            assert s.mark_completed(rec)
    assert s.mark_completed(sess.new_record("P0AAAA", "pilot", "A"))  # twice is fine
    real = sess.new_record("R1AAAA", "real", "B")
    s.save(real)
    s.mark_completed(real)
    assert s.count_completed("pilot") == {"A": 3, "B": 1}
    assert s.count_completed("real") == {"A": 0, "B": 1}


# ---------- local storage ----------

def test_local_roundtrip_and_counts():
    with tempfile.TemporaryDirectory() as d:
        s = LocalStorage(d)
        rec = sess.new_record("XYZ789", "pilot", "B")
        assert s.save(rec)
        assert s.load("pilot", "XYZ789", "B")["sequence"] == "B"
        assert s.load("pilot", "NOPE22", "B") is None
        assert s.count_completed("pilot") == {"A": 0, "B": 0}  # not finished yet
        assert s.mark_completed(rec)
        assert s.count_completed("pilot") == {"A": 0, "B": 1}
        assert s.count_completed("real") == {"A": 0, "B": 0}


# ---------- session flow ----------

def test_full_session_both_sequences():
    for seq, order in (("A", ["control", "pen_switch", "pen_stay"]),
                       ("B", ["control", "pen_stay", "pen_switch"])):
        rec = _full_record(seq)
        assert rec["completed"] and rec["end_time"] and rec["duration_s"] is not None
        assert len(rec["trials"]) == 25
        assert [t["trial_overall"] for t in rec["trials"]] == list(range(1, 26))
        blocks = [t["block"] for t in rec["trials"]]
        assert blocks == [order[0]] * 5 + [order[1]] * 10 + [order[2]] * 10
        assert [t["trial_in_block"] for t in rec["trials"]] == \
            list(range(1, 6)) + list(range(1, 11)) * 2
        assert rec["total_points"] == sum(t["points"] for t in rec["trials"])
        assert rec["trials"][-1]["cumulative_points"] == rec["total_points"]
        for b in order:
            assert rec["comprehension"][b]["attempts"] == 2
        assert "pilot_fb" in sess.steps("pilot") and "pilot_fb" not in sess.steps("real")
        order = sess.steps("real")
        assert order.index("prior") < order.index("reason") < order.index("demo")
        assert rec["first_game_reason"] == "try_out"


def test_always_switch_scores_more_than_always_stay():
    rng = random.Random(7)
    sw = sum(_full_record(choose=lambda b: "switch", rng=rng)["total_points"] for _ in range(200))
    stay = sum(_full_record(choose=lambda b: "stay", rng=rng)["total_points"] for _ in range(200))
    assert sw > 1.6 * stay


def test_resume_mid_block_continues_at_next_trial():
    rng = random.Random(3)
    rec = sess.new_record("RES234", "pilot", "A")
    rec["step"] = "block_1"
    for _ in range(4):
        sess.record_trial(rec, 1, 1, 1, 2, "stay", 500, 500)
    reloaded = json.loads(json.dumps(rec))     # what comes back from the file
    sess.mark_resumed(reloaded)
    assert reloaded["resumed"] and reloaded["resume_count"] == 1
    assert reloaded["step"] == "block_1"
    assert sess.trials_done_in_block(reloaded, 1) == 4
    t = sess.record_trial(reloaded, 1, 2, 1, 3, "switch", 500, 500)
    assert t["trial_in_block"] == 5 and t["after_resume"] == 1


def test_resume_after_finished_block_moves_on():
    rec = sess.new_record("RES234", "pilot", "A")
    rec["step"] = "block_0"
    for _ in range(5):
        sess.record_trial(rec, 0, 1, 1, 2, "stay", 500, 500)
    sess.mark_resumed(rec)
    assert rec["step"] == "belief_1"


def test_comprehension_logs_wrong_answers():
    rec = sess.new_record("CMP234", "pilot", "A")
    qs = texts.COMPREHENSION["pen_switch"]
    assert not sess.check_comprehension(rec, "pen_switch", qs,
                                        {"switch_win": "100", "stay_win": "100"})
    assert sess.check_comprehension(rec, "pen_switch", qs,
                                    {"switch_win": "75", "stay_win": "100"})
    log = rec["comprehension"]["pen_switch"]
    assert log == {"attempts": 2, "wrong": {"switch_win": ["100"]}}


def test_second_penalty_block_says_rules_change():
    assert texts.rules_for("pen_stay", 2).startswith("Same game, one change")
    assert texts.rules_for("pen_stay", 3).startswith("The rule changes")
    assert texts.rules_for("pen_switch", 3).startswith("The rule changes")


def test_placeholders_detected():
    left = texts.placeholders_left()
    assert "CONSENT_TEXT" in left and "config.CONTACT_FORM_URL" in left


def test_record_has_no_identifying_fields():
    rec = _full_record()
    forbidden = {"ip", "name", "email", "user_agent", "device"}
    assert not forbidden & set(rec)


# ---------- export ----------

def test_export_csv():
    with tempfile.TemporaryDirectory() as d:
        s = LocalStorage(d)
        rng = random.Random(11)
        for seq in "AB":
            s.save(_full_record(seq, rng=rng))
        dropout = sess.new_record("DROP22", "pilot", "A")
        s.save(dropout)
        out = os.path.join(d, "out")
        export.export(os.path.join(d, "data", "pilot"), out)
        with open(os.path.join(out, "trials.csv")) as f:
            assert len(f.readlines()) == 1 + 50
        with open(os.path.join(out, "participants.csv")) as f:
            lines = f.readlines()
        assert len(lines) == 4
        assert any("DROP22" in line and "False" in line for line in lines)
        assert "first_game_reason" in lines[0]
        assert sum("try_out" in line for line in lines) == 2  # the two finished people
