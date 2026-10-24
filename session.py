"""The participant record and the order of steps. Pure Python, no Streamlit.

The whole participant file is one dict (`rec`). `rec["step"]` is the screen
the participant is on; after a refresh the app reloads the file and goes back
to that step (inside a block: the next unplayed trial).
"""

import time
from datetime import datetime, timezone

import config
import game


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def steps(mode):
    """Screens in order (after consent and before the end screen)."""
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
    """Move to the next step. Returns the new step."""
    order = steps(rec["mode"])
    i = order.index(rec["step"])
    rec["step"] = order[min(i + 1, len(order) - 1)]
    if rec["step"] == "end" and not rec["completed"]:
        rec["completed"] = True
        rec["end_time"] = now_iso()
        rec["duration_s"] = round(time.time() - rec["start_epoch"], 1)
    return rec["step"]


def block_index(step):
    """'block_1' / 'rules_1' -> 1."""
    return int(step.split("_")[1])


def block_info(rec, idx):
    """(block, block_order, n_trials) for block number idx (0-2)."""
    return game.block_plan(rec["sequence"])[idx]


def trials_done_in_block(rec, idx):
    block, _, _ = block_info(rec, idx)
    return sum(1 for t in rec["trials"] if t["block"] == block)


def record_trial(rec, idx, trophy, pick, opened, choice, t_pick_ms, t_decision_ms):
    """Resolve a trial, append it to the record and return it."""
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
    """Log one attempt. Returns True if all answers are correct.

    `answers` maps question id -> chosen option (None if unanswered).
    """
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
    """Called when a saved, unfinished record is reloaded after a refresh."""
    rec["resumed"] = True
    rec["resume_count"] += 1
    # A finished block that was saved before advancing: move on.
    if rec["step"].startswith("block_") and block_finished(rec, block_index(rec["step"])):
        advance(rec)
    return rec
