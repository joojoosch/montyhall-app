"""Draws the two prize winners after data collection.

Use:      python draw_winners.py <forms export (.xlsx or .csv)> <data folder> [--seed NUMBER]
Example:  python draw_winners.py prize_form.xlsx montyhall-data-main/data/real --seed 20261109

Who can win (as promised in the consent text):
  - the code was entered in the prize form, AND
  - a participant file with that code exists and is marked completed.
Each code counts once, even if it was entered several times.

--seed makes the draw repeatable: anyone running the script again with the same
files and the same seed gets the same winners (good for the thesis). Pick the
seed BEFORE looking at the entries, e.g. the date of the draw.
"""

import argparse
import json
import os
import random
import sys

import pandas as pd

import config

N_WINNERS = 2


def load_form(path):
    # Microsoft Forms export: find the code and email columns by their titles
    df = pd.read_excel(path) if path.lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    code_col = next((c for c in df.columns if "code" in str(c).lower()), None)
    # Microsoft Forms adds its own "Email" column (usually "anonymous") before the
    # questions, so take the LAST column with "mail" in its title = your question
    mail_cols = [c for c in df.columns if "mail" in str(c).lower() and c != code_col]
    mail_col = mail_cols[-1] if mail_cols else None
    if code_col is None:
        raise SystemExit(f"No column with 'code' in its title. Columns: {list(df.columns)}")
    entries = []
    for _, row in df.iterrows():
        raw = "" if pd.isna(row[code_col]) else str(row[code_col])
        entries.append({"raw": raw, "code": clean_code(raw),
                        "email": None if mail_col is None or pd.isna(row[mail_col]) else str(row[mail_col]).strip()})
    return entries


def clean_code(raw):
    # people type codes in many ways: " ma5rtk ", "MA5 RTK" -> "MA5RTK"
    return "".join(ch for ch in str(raw).upper() if ch.isalnum())


def load_completed(folder):
    # code -> participant file (only finished people)
    done = {}
    for name in os.listdir(folder):
        if name.endswith(".json"):
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("completed"):
                done[rec["participant_id"]] = rec
    return done


def check_entries(entries, done):
    valid, problems, seen = {}, [], {}
    for e in entries:
        c = e["code"]
        if len(c) != config.CODE_LENGTH:
            problems.append((e["raw"], e["email"], "not 6 characters"))
        elif c not in done:
            problems.append((e["raw"], e["email"], "no finished participant with this code"))
        elif c in valid:
            seen.setdefault(c, [valid[c]["email"]]).append(e["email"])  # counted once
        else:
            valid[c] = e
    duplicates = {c: emails for c, emails in seen.items()}
    return valid, problems, duplicates


def draw(valid_codes, seed=None, k=N_WINNERS):
    codes = sorted(valid_codes)                 # fixed order, so the seed gives the same result
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    return rng.sample(codes, min(k, len(codes)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("form")
    ap.add_argument("folder")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args(argv)

    entries = load_form(a.form)
    done = load_completed(a.folder)
    valid, problems, duplicates = check_entries(entries, done)

    print(f"Form entries: {len(entries)}. Finished participants in the data: {len(done)}.")
    print(f"Valid tickets (finished + in the form, each code once): {len(valid)}")
    for raw, email, why in problems:
        print(f"  not valid: {raw!r} ({email}): {why}")
    for c, emails in duplicates.items():
        print(f"  {c} was entered {len(emails)} times (counted once). Emails: {emails}")
    if a.seed is None:
        print("No --seed given: the draw cannot be repeated. Use --seed for the thesis.")
    winners = draw(valid, a.seed)
    print(f"\nWINNERS (seed {a.seed}):")
    for c in winners:
        rec = done[c]
        pts = rec["total_points"]
        print(f"  {c}: {pts} points = CHF {pts * config.CHF_PER_POINT:.2f}, contact: {valid[c]['email']}")
    return winners


if __name__ == "__main__":
    main(sys.argv[1:])
