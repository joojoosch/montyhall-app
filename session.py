# The participant file and the order of the screens.
#
# Everything about one participant is in one dict called `rec` (= the JSON file).
# rec["step"] says which screen they are on. After a refresh the app loads the
# file again and continues there (in a block: with the next game not played yet).

import time
from datetime import datetime, timezone

import config
import game


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def steps(mode):
    # screens after consent, in order
    s = ["prize", "rules_0", "block_0", "belief_1", "rules_1", "block_1",
         "rules_2", "block_2", "belief_2", "prior", "reason", "thresh", "demo"]
    if mode == "pilot":
        s.append("pilot_fb")
    s.append("end")
    return s


def new_record(pid, mode, sequence):
    plan = game.block_plan(sequence)
    return {
        "participant_id": pid,
        "mode": mode,
        "app_version": config.APP_VERSION,
        "sequence": sequence,
        "consent": True,
        "start_time": now_iso(),
        "start_epoch": time.time(),
        "end_time": None,
        "duration_s": None,
        "belief_1": None, "belief_1_time": None,
        "belief_2": None, "belief_2_time": None,
        "comprehension": {b: {"attempts": 0, "wrong": {}} for b, _, _ in plan},
        "prior_knowledge": None,
        "first_game_reason": None,
        # exploratory penalty questions (filled when the "thresh" screen starts)
        "threshold_order": None,      # e.g. ["pen_switch", "pen_stay"], random per person
        "threshold_shown_time": None,
        "thresholds": None,           # one answer per penalty part
        "age": None, "gender": None, "student_status": None, "field_of_study": None,
        "pilot_feedback": None,
        "total_points": 0,
        "completed": False,
        "resumed": False,
        "resume_count": 0,
        "step": "prize",
        "trials": [],
    }


def advance(rec):
    # go to the next screen; reaching "end" marks the participant as completed
    order = steps(rec["mode"])
    i = order.index(rec["step"])
    rec["step"] = order[min(i + 1, len(order) - 1)]
    if rec["step"] == "thresh":
        prepare_thresholds(rec)
    if rec["step"] == "end" and not rec["completed"]:
        rec["completed"] = True
        rec["end_time"] = now_iso()
        rec["duration_s"] = round(time.time() - rec["start_epoch"], 1)
    return rec["step"]


def block_index(step):
    # 'block_1' or 'rules_1' -> 1
    return int(step.split("_")[1])


def block_info(rec, idx):
    # (block, block_order, number of games) for block 0, 1 or 2
    return game.block_plan(rec["sequence"])[idx]


def trials_done_in_block(rec, idx):
    block, _, _ = block_info(rec, idx)
    return sum(1 for t in rec["trials"] if t["block"] == block)


def record_trial(rec, idx, trophy, pick, opened, choice, t_pick_ms, t_decision_ms):
    # work out the result of a game and add it to the file
    block, order, n = block_info(rec, idx)
    res = game.resolve_trial(block, trophy, pick, opened, choice)
    rec["total_points"] += res["points"]
    trial = {
        "trial_overall": len(rec["trials"]) + 1,
        "block": block,
        "block_order": order,
        "trial_in_block": trials_done_in_block(rec, idx) + 1,
        "trophy_door": trophy,
        "first_pick": pick,
        "host_opened": opened,
        **res,
        "cumulative_points": rec["total_points"],
        "t_pick_ms": t_pick_ms,
        "t_decision_ms": t_decision_ms,
        "timestamp": now_iso(),
        "after_resume": rec["resume_count"],
    }
    rec["trials"].append(trial)
    return trial


def block_finished(rec, idx):
    _, _, n = block_info(rec, idx)
    return trials_done_in_block(rec, idx) >= n


def check_comprehension(rec, block, questions, answers):
    # log one attempt (and every wrong answer); True if all answers are right
    log = rec["comprehension"][block]
    log["attempts"] += 1
    ok = True
    for q in questions:
        a = answers.get(q["id"])
        if a != q["correct"]:
            ok = False
            log["wrong"].setdefault(q["id"], []).append(a)
    return ok


def mark_resumed(rec):
    # called when an unfinished file is loaded again after a refresh
    rec["resumed"] = True
    rec["resume_count"] += 1
    # if the block was already finished before the refresh, move on
    if rec["step"].startswith("block_") and block_finished(rec, block_index(rec["step"])):
        advance(rec)
    return rec


# ---------- exploratory penalty questions ("thresh" screen) ----------
# For each penalty part: how big the reduction would have to be for the person
# to change what they usually did there. Asked after all choices and beliefs,
# so it can't influence them. Not paid.

THRESH_TYPES = ("number", "always_stay", "always_switch")


def stay_count(rec, block):
    # how often the person stayed in this part (out of 10)
    return sum(1 for t in rec["trials"] if t["block"] == block and t["choice"] == "stay")


def threshold_variant(stays, n=config.N_PENALTY):
    # what they usually did: 6-10 stays -> stayed, 0-4 -> switched, 5 -> equal
    switches = n - stays
    if stays > switches:
        return "stayed"
    if switches > stays:
        return "switched"
    return "equal"


def prepare_thresholds(rec, rng=None):
    # Done once when the screen starts: random order + which text each part gets.
    # Saved in the file, so a refresh shows exactly the same questions.
    if rec.get("threshold_order"):
        return rec
    order = [config.PEN_STAY, config.PEN_SWITCH]
    (rng or game._SYSTEM_RNG).shuffle(order)
    rec["threshold_order"] = order
    rec["threshold_shown_time"] = now_iso()
    rec["thresholds"] = {}
    for pos, block in enumerate(order, start=1):
        stays = stay_count(rec, block)
        rec["thresholds"][block] = {
            "threshold_value": None,      # 0-100, only if threshold_type == "number"
            "threshold_type": None,       # number / always_stay / always_switch
            "threshold_variant": threshold_variant(stays),
            "stay_count": stays,
            "position": pos,              # 1 = shown first
            "answer_time": None,
        }
    return rec


def check_threshold(ttype, value):
    # returns the value to save; raises ValueError if the answer is incomplete
    if ttype not in THRESH_TYPES:
        raise ValueError("choose one option")
    if ttype == "number":
        return game.validate_belief(value)   # same rule: whole number 0-100
    return None                              # "always ..." has no number


def record_threshold(rec, block, ttype, value):
    part = rec["thresholds"][block]
    part["threshold_value"] = check_threshold(ttype, value)
    part["threshold_type"] = ttype
    part["answer_time"] = now_iso()
    return part
