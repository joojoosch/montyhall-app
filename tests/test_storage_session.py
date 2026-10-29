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
        if step == "thresh":
            for b in rec["threshold_order"]:
                sess.record_threshold(rec, b, "number", 30)
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
    assert left == []   # consent text and form link are filled in: ready for real mode


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


# ---------- background saving ----------

class SlowStorage:
    # pretends every save takes a while, and remembers the order of writes
    def __init__(self, delay=0.05, fail=False):
        import threading
        self.delay, self.fail = delay, fail
        self.written = []
        self.lock = threading.Lock()

    def save(self, rec):
        import time
        time.sleep(self.delay)
        if self.fail:
            return False
        with self.lock:
            self.written.append(len(rec["trials"]))
        return True


def test_background_saver_writes_newest_and_never_goes_back():
    from storage import BackgroundSaver
    st = SlowStorage()
    saver = BackgroundSaver(st)
    rec = sess.new_record("BGS234", "pilot", "A")
    rec["step"] = "block_0"
    for _ in range(5):                 # 5 quick games, faster than saving
        sess.record_trial(rec, 0, 1, 1, 2, "stay", 500, 500)
        saver.submit(rec)
    assert saver.flush(timeout=5)
    assert st.written[-1] == 5                     # the newest version is saved
    assert st.written == sorted(st.written)        # never an older one after a newer one
    assert len(st.written) < 5                     # in-between versions were skipped


def test_background_saver_reports_failure():
    from storage import BackgroundSaver
    saver = BackgroundSaver(SlowStorage(fail=True))
    saver.submit(sess.new_record("BGS234", "pilot", "A"))
    assert saver.flush(timeout=5) is False


def test_background_saver_copies_the_record():
    from storage import BackgroundSaver
    st = SlowStorage(delay=0.2)
    saver = BackgroundSaver(st)
    rec = sess.new_record("BGS234", "pilot", "A")
    saver.submit(rec)
    rec["trials"].append({"changed": "after submit"})   # the app keeps playing
    assert saver.flush(timeout=5)
    assert st.written == [0]   # what was saved is the state at submit time


# ---------- exploratory penalty questions ("thresh") ----------

def _rec_with_part(block, stays, seq="A"):
    # a record where the given penalty part has exactly `stays` stays out of 10
    rec = sess.new_record("THR234", "pilot", seq)
    idx = [b for b, _, _ in game.block_plan(seq)].index(block)
    rec["step"] = f"block_{idx}"
    for i in range(10):
        sess.record_trial(rec, idx, 1, 1, 2, "stay" if i < stays else "switch", 500, 500)
    return rec


def test_threshold_variant_counts():
    # 6-10 stays = stayed, 0-4 = switched, exactly 5 = equal
    expected = {0: "switched", 1: "switched", 4: "switched", 5: "equal",
                6: "stayed", 9: "stayed", 10: "stayed"}
    for stays, variant in expected.items():
        assert sess.threshold_variant(stays) == variant, stays
    for block in (config.PEN_STAY, config.PEN_SWITCH):
        for stays, variant in expected.items():
            rec = _rec_with_part(block, stays)
            sess.prepare_thresholds(rec, random.Random(1))
            part = rec["thresholds"][block]
            assert part["stay_count"] == stays
            assert part["threshold_variant"] == variant


def test_threshold_texts_follow_the_brief():
    # stay-penalty part: count stays; switching-penalty part: count switches (= mirror)
    cases = [
        (config.PEN_STAY, 10, texts.THRESH_STAY_STAYED, "How big", "switch instead"),
        (config.PEN_STAY, 0, texts.THRESH_STAY_SWITCHED, "How small", "stay instead"),
        (config.PEN_STAY, 5, texts.THRESH_STAY_EQUAL, "From which size", "switch rather than stay"),
        (config.PEN_SWITCH, 0, texts.THRESH_SWITCH_SWITCHED, "How big", "stay instead"),      # 10 switches
        (config.PEN_SWITCH, 10, texts.THRESH_SWITCH_STAYED, "How small", "switch instead"),   # 0 switches
        (config.PEN_SWITCH, 5, texts.THRESH_SWITCH_EQUAL, "From which size", "stay rather than switch"),
    ]
    for block, stays, text, start, end in cases:
        rec = _rec_with_part(block, stays)
        sess.prepare_thresholds(rec, random.Random(2))
        shown = texts.thresh_question(block, rec["thresholds"][block]["threshold_variant"])
        assert shown == text and start in shown and end in shown, (block, stays)
    assert "staying with your first choice" in texts.THRESH_STAY_STAYED
    assert "switching to the other door" in texts.THRESH_SWITCH_SWITCHED


def test_threshold_order_random_saved_and_stable():
    orders = set()
    for seed in range(40):
        rec = _rec_with_part(config.PEN_STAY, 3)
        sess.prepare_thresholds(rec, random.Random(seed))
        order = tuple(rec["threshold_order"])
        orders.add(order)
        assert sorted(order) == ["pen_stay", "pen_switch"]
        assert [rec["thresholds"][b]["position"] for b in order] == [1, 2]
        sess.prepare_thresholds(rec, random.Random(seed + 99))   # second call changes nothing
        assert tuple(rec["threshold_order"]) == order
    assert len(orders) == 2   # both orders happen


def test_threshold_answers_validated():
    rec = _rec_with_part(config.PEN_STAY, 7)
    sess.prepare_thresholds(rec, random.Random(3))
    part = sess.record_threshold(rec, config.PEN_STAY, "number", 40)
    assert part["threshold_value"] == 40 and part["threshold_type"] == "number" and part["answer_time"]
    part = sess.record_threshold(rec, config.PEN_SWITCH, "always_stay", 55)
    assert part["threshold_value"] is None and part["threshold_type"] == "always_stay"
    assert sess.check_threshold("number", 0) == 0 and sess.check_threshold("number", 100) == 100
    for bad in [("number", None), ("number", 101), ("number", -1), ("number", 12.5),
                (None, 30), ("maybe", 30)]:
        try:
            sess.check_threshold(*bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")


def test_threshold_screen_order_and_resume():
    order = sess.steps("real")
    assert order.index("reason") < order.index("thresh") < order.index("demo")
    assert order.index("belief_2") < order.index("prior") < order.index("thresh")
    # play until the thresh screen, then "refresh": same order and texts come back
    rec = _full_record("B")
    assert rec["completed"] and rec["thresholds"] and rec["threshold_shown_time"]
    rec2 = sess.new_record("RSM234", "pilot", "A")
    rec2["trials"] = rec["trials"]
    rec2["step"] = "reason"
    sess.advance(rec2)                                   # enters "thresh"
    assert rec2["step"] == "thresh" and rec2["threshold_order"]
    reloaded = json.loads(json.dumps(rec2))              # what comes back from the file
    sess.mark_resumed(reloaded)
    assert reloaded["step"] == "thresh"
    assert reloaded["threshold_order"] == rec2["threshold_order"]
    assert reloaded["thresholds"] == rec2["thresholds"]


def test_threshold_export_columns():
    with tempfile.TemporaryDirectory() as d:
        s = LocalStorage(d)
        rec = _full_record("A", rng=random.Random(4))
        s.save(rec)
        out = os.path.join(d, "out")
        export.export(os.path.join(d, "data", "pilot"), out)
        import csv
        with open(os.path.join(out, "participants.csv")) as f:
            row = next(csv.DictReader(f))
        assert row["threshold_order"] in ("pen_stay,pen_switch", "pen_switch,pen_stay")
        for b in ("pen_stay", "pen_switch"):
            part = rec["thresholds"][b]
            assert row[f"{b}_threshold_type"] == part["threshold_type"]
            assert row[f"{b}_threshold_variant"] == part["threshold_variant"]
            assert int(row[f"{b}_stay_count"]) == part["stay_count"]
            assert row[f"{b}_position"] in ("1", "2")
            assert row[f"{b}_answer_time"]


# ---------- prize draw ----------

def test_draw_winners_valid_tickets_and_repeatable():
    import draw_winners as dw
    with tempfile.TemporaryDirectory() as d:
        s = LocalStorage(d)
        codes = []
        for i, seq in enumerate("ABAB"):
            rec = _full_record(seq, rng=random.Random(20 + i))
            s.save(rec)
            codes.append(rec["participant_id"])
        unfinished = sess.new_record("UNF234", "real", "A")
        s.save(unfinished)
        folder = os.path.join(d, "data", "pilot")
        done = dw.load_completed(folder)
        assert set(done) == set(codes)
        entries = [{"raw": f" {codes[0].lower()} ", "code": dw.clean_code(f" {codes[0].lower()} "), "email": "a@x"},
                   {"raw": codes[1], "code": codes[1], "email": "b@x"},
                   {"raw": codes[1], "code": codes[1], "email": "b2@x"},       # twice
                   {"raw": "UNF234", "code": "UNF234", "email": "c@x"},        # not finished
                   {"raw": "AB", "code": "AB", "email": "d@x"}]                # typo
        valid, problems, dup = dw.check_entries(entries, done)
        assert set(valid) == {codes[0], codes[1]}
        assert len(problems) == 2 and codes[1] in dup
        assert dw.draw(valid, seed=7) == dw.draw(valid, seed=7)              # repeatable
        assert sorted(dw.draw(valid, seed=7)) == sorted(valid)               # 2 tickets -> both win
