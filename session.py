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
         "rules_2", "block_2", "belief_2", "prior", "demo"]
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
