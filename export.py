"""Turn all participant JSON files of one mode into two CSV files.

Usage:
    python export.py <folder with the JSON files> [output folder]

Example (after downloading the data repo):
    python export.py montyhall-data/data/real out/

Writes trials.csv (one row per trial) and participants.csv (one row per
participant, incl. dropouts with completed = False).
"""

import csv
import json
import os
import sys

PARTICIPANT_FIELDS = [
    "participant_id", "mode", "app_version", "sequence", "consent", "start_time",
    "end_time", "duration_s", "completed", "resumed", "resume_count",
    "belief_1", "belief_1_time", "belief_2", "belief_2_time",
    "prior_knowledge", "age", "gender", "student_status", "field_of_study",
    "pilot_feedback", "total_points", "n_trials",
    "comp_control_attempts", "comp_pen_switch_attempts", "comp_pen_stay_attempts",
    "comp_wrong",
]
TRIAL_FIELDS = [
    "participant_id", "sequence", "trial_overall", "block", "block_order",
    "trial_in_block", "trophy_door", "first_pick", "host_opened", "choice",
    "final_door", "switched", "won", "penalty_applied", "points",
    "cumulative_points", "t_pick_ms", "t_decision_ms", "timestamp", "after_resume",
]


def load_all(folder):
    recs = []
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json"):
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                recs.append(json.load(f))
    return recs


def participant_row(rec):
    row = {k: rec.get(k) for k in PARTICIPANT_FIELDS}
    row["n_trials"] = len(rec.get("trials", []))
    comp = rec.get("comprehension", {})
    for block in ("control", "pen_switch", "pen_stay"):
        row[f"comp_{block}_attempts"] = comp.get(block, {}).get("attempts")
    row["comp_wrong"] = json.dumps({b: v.get("wrong") for b, v in comp.items()
                                    if v.get("wrong")}, ensure_ascii=False)
    return row


def export(folder, out="."):
    recs = load_all(folder)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "participants.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PARTICIPANT_FIELDS)
        w.writeheader()
        for rec in recs:
            w.writerow(participant_row(rec))
    n_trials = 0
    with open(os.path.join(out, "trials.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TRIAL_FIELDS)
        w.writeheader()
        for rec in recs:
            for t in rec.get("trials", []):
                row = {k: t.get(k) for k in TRIAL_FIELDS}
                row["participant_id"] = rec["participant_id"]
                row["sequence"] = rec["sequence"]
                w.writerow(row)
                n_trials += 1
    done = sum(1 for r in recs if r.get("completed"))
    print(f"{len(recs)} participants ({done} completed), {n_trials} trials -> {out}")
    return recs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    export(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
