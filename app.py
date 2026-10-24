"""Monty Hall experiment: screens. Run locally with:  streamlit run app.py

All logic lives in game.py / session.py / storage.py; this file only shows
screens and reacts to buttons. Every button uses a callback that first checks
that the participant is still on the screen the button belongs to, so a
double click can never advance twice.
"""

import sys
import time

import streamlit as st

import config
import game
import session as sess
import texts
from storage import make_storage

st.set_page_config(page_title=texts.TITLE, page_icon="🚪", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(texts.CSS, unsafe_allow_html=True)
S = st.session_state


# ---------------------------------------------------------------- helpers

def get_storage():
    if "storage" not in S:
        try:
            secrets = dict(st.secrets)
        except Exception:  # no secrets file: local saving
            secrets = {}
        S.storage = make_storage(secrets)
    return S.storage


def save():
    ok = get_storage().save(S.rec)
    S.last_save_ok = ok
    if not ok:
        print(f"[app] SAVE FAILED for {S.rec['participant_id']} at {S.rec['step']}",
              file=sys.stderr, flush=True)
    return ok


def set_msg(text):
    S.msg = (S.rec["step"] if S.rec else "consent", text)


def show_msg():
    step = S.rec["step"] if S.rec else "consent"
    if S.get("msg") and S.msg[0] == step:
        st.error(S.msg[1])


def on_step(expected):
    return S.rec is not None and S.rec["step"] == expected


def go_next(expected):
    """Advance to the next step if still on `expected`."""
    if on_step(expected):
        sess.advance(S.rec)
        S.msg = None
        S.need_save = True


def doors_html(states, final=None):
    parts = []
    for d in config.DOORS:
        state = states[d]
        icon, label = texts.DOOR_LABELS[state]
        label = label.format(d=d) + (texts.FINAL_MARK if final == d else "")
        cls = "door"
        if state == "picked" or final == d:
            cls += " picked"
        if state in ("opened", "empty"):
            cls += " opened"
        parts.append(f'<div class="{cls}"><div class="big">{icon}</div><div>{label}</div></div>')
    st.markdown('<div class="doors">' + "".join(parts) + "</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- start-up

def init():
    if S.get("init"):
        return
    S.init = True
    S.rec = None
    S.trial = None
    S.need_save = False
    S.last_save_ok = True
    S.msg = None
    # Resume after refresh / phone sleep: the ID is in the URL.
    pid = st.query_params.get("pid")
    seq = st.query_params.get("seq")
    if pid and seq in ("A", "B"):
        rec = get_storage().load(config.MODE, pid, seq)
        if rec is not None and rec.get("mode") == config.MODE:
            S.rec = rec
            if not rec["completed"]:
                sess.mark_resumed(rec)
                S.need_save = True


def guard_real_mode():
    if config.MODE != "real":
        if config.MODE != "pilot":
            st.error("config.MODE must be 'pilot' or 'real'.")
            st.stop()
        st.caption(f"PILOT MODE · saving: {get_storage().kind}")
        return
    problems = texts.placeholders_left()
    if get_storage().kind != "github":
        problems.append("GitHub secrets missing: data would not be saved")
    if problems:
        st.error("The study is not ready yet. Please try again later.")
        print(f"[app] real mode blocked: {problems}", file=sys.stderr, flush=True)
        st.stop()


# ---------------------------------------------------------------- 1. consent

def on_consent():
    if S.rec is not None or not S.get("consent_cb"):
        return
    seq = game.assign_sequence(get_storage().count_sequences(config.MODE))
    S.rec = sess.new_record(game.make_code(), config.MODE, seq)
    S.need_save = True


def screen_consent():
    st.title(texts.TITLE)
    st.markdown(texts.CONSENT_TEXT)
    st.warning(texts.NO_REFRESH)
    agreed = st.checkbox(texts.CONSENT_CHECKBOX, key="consent_cb")
    st.button(texts.CONTINUE, disabled=not agreed, on_click=on_consent)


# ---------------------------------------------------------------- 2. prize

def screen_prize():
    st.subheader("How you can win")
    st.markdown(texts.PRIZE_TEXT)
    st.button(texts.CONTINUE, on_click=go_next, args=("prize",))


# ---------------------------------------------------------------- rules + comprehension

def on_comp(idx):
    step = f"rules_{idx}"
    if not on_step(step):
        return
    block, _, _ = sess.block_info(S.rec, idx)
    questions = texts.COMPREHENSION[block]
    answers = {q["id"]: S.get(f"comp_{idx}_{q['id']}") for q in questions}
    if any(a is None for a in answers.values()):
        set_msg(texts.COMP_MISSING)
        return
    if sess.check_comprehension(S.rec, block, questions, answers):
        S.trial = None
        go_next(step)
    else:
        set_msg(texts.COMP_WRONG)


def screen_rules(idx):
    block, order, _ = sess.block_info(S.rec, idx)
    st.subheader("The rules" if idx == 0 else f"Part {idx + 1}: new rules")
    st.markdown(texts.rules_for(block, order))
    st.markdown(f"**{texts.COMP_HEADER}**")
    with st.form(f"comp_form_{idx}", border=False):
        for q in texts.COMPREHENSION[block]:
            st.radio(q["q"], q["options"], index=None, horizontal=True,
                     key=f"comp_{idx}_{q['id']}")
        st.form_submit_button(texts.COMP_SUBMIT, on_click=on_comp, args=(idx,))
    show_msg()


# ---------------------------------------------------------------- trials

def new_trial(idx):
    S.trial = {
        "id": f"{idx}-{len(S.rec['trials'])}-{S.rec['resume_count']}",
        "idx": idx,
        "k": sess.trials_done_in_block(S.rec, idx) + 1,
        "trophy": game.draw_trophy_door(),
        "pick": None, "opened": None, "phase": "pick",
        "t0": time.time(), "t1": None, "t_pick_ms": None, "result": None,
    }


def trial_ok(tid, phase):
    t = S.get("trial")
    return t is not None and t["id"] == tid and t["phase"] == phase


def on_pick(tid, door):
    if not trial_ok(tid, "pick"):
        return
    t = S.trial
    t["pick"] = door
    t["opened"] = game.host_opens(door, t["trophy"])
    t["t_pick_ms"] = int((time.time() - t["t0"]) * 1000)
    t["t1"] = time.time()
    t["phase"] = "decide"


def on_choice(tid, choice):
    if not trial_ok(tid, "decide"):
        return
    t = S.trial
    t_dec = int((time.time() - t["t1"]) * 1000)
    t["result"] = sess.record_trial(S.rec, t["idx"], t["trophy"], t["pick"], t["opened"],
                                    choice, t["t_pick_ms"], t_dec)
    t["phase"] = "feedback"
    S.need_save = True  # save after every trial


def on_next_trial(tid):
    if not trial_ok(tid, "feedback"):
        return
    idx = S.trial["idx"]
    S.trial = None
    if sess.block_finished(S.rec, idx):
        go_next(f"block_{idx}")


def screen_block(idx):
    block, _, n = sess.block_info(S.rec, idx)
    if S.trial is None or S.trial["idx"] != idx:
        new_trial(idx)
    t = S.trial
    st.markdown(f'<div class="counter">{texts.counter(t["k"], n, S.rec["total_points"])}</div>',
                unsafe_allow_html=True)

    if t["phase"] == "pick":
        doors_html({d: "closed" for d in config.DOORS})
        st.markdown(f'<div class="payoff">{texts.PICK_PROMPT}</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for col, d in zip(cols, config.DOORS):
            col.button(f"Door {d}", key=f"pick_{t['id']}_{d}", on_click=on_pick, args=(t["id"], d))

    elif t["phase"] == "decide":
        other = game.remaining_door(t["pick"], t["opened"])
        states = {d: "closed" for d in config.DOORS}
        states[t["pick"]] = "picked"
        states[t["opened"]] = "opened"
        doors_html(states)
        st.markdown(f'<div class="payoff">{texts.DECIDE_PROMPT.format(opened=t["opened"])}'
                    f'<br><b>{texts.PAYOFFS[block]}</b></div>', unsafe_allow_html=True)
        left, right = st.columns(2)  # fixed order: Stay left, Switch right
        left.button(texts.STAY_BUTTON.format(door=t["pick"]), key=f"stay_{t['id']}",
                    on_click=on_choice, args=(t["id"], "stay"))
        right.button(texts.SWITCH_BUTTON.format(door=other), key=f"switch_{t['id']}",
                     on_click=on_choice, args=(t["id"], "switch"))

    else:  # feedback
        r = t["result"]
        states = {d: ("trophy" if d == t["trophy"] else "empty") for d in config.DOORS}
        doors_html(states, final=r["final_door"])
        if r["won"]:
            st.success(texts.WIN)
        else:
            st.info(texts.LOSE.format(door=t["trophy"]))
        lines = [texts.TRIAL_POINTS.format(points=r["points"])]
        if r["penalty_applied"]:
            lines.append(texts.PENALTY_NOTE)
        lines.append(f"**{texts.NEW_TOTAL.format(total=S.rec['total_points'])}**")
        st.markdown("  \n".join(lines))
        st.button(texts.NEXT, key=f"next_{t['id']}", on_click=on_next_trial, args=(t["id"],))


# ---------------------------------------------------------------- beliefs

def on_belief(num):
    step = f"belief_{num}"
    if not on_step(step):
        return
    try:
        value = game.validate_belief(S.get(f"belief_in_{num}"))
    except ValueError:
        set_msg(texts.BELIEF_MISSING)
        return
    S.rec[f"belief_{num}"] = value
    S.rec[f"belief_{num}_time"] = sess.now_iso()
    go_next(step)


def screen_belief(num):
    st.subheader("A short question")
    st.markdown(texts.BELIEF_QUESTION)
    st.number_input(texts.BELIEF_LABEL, min_value=0, max_value=100, step=1, value=None,
                    placeholder="0 to 100", key=f"belief_in_{num}")
    st.button(texts.NEXT, key=f"belief_next_{num}", on_click=on_belief, args=(num,))
    show_msg()


# ---------------------------------------------------------------- prior knowledge, demographics

def on_prior():
    if not on_step("prior"):
        return
    answer = S.get("prior_in")
    if answer is None:
        set_msg(texts.PRIOR_MISSING)
        return
    S.rec["prior_knowledge"] = answer
    go_next("prior")


def screen_prior():
    st.radio(texts.PRIOR_QUESTION, texts.PRIOR_OPTIONS, index=None, key="prior_in")
    st.button(texts.NEXT, key="prior_next", on_click=on_prior)
    show_msg()


def on_demo():
    if not on_step("demo"):
        return
    S.rec["age"] = S.get("age_in")
    S.rec["gender"] = S.get("gender_in")
    S.rec["student_status"] = S.get("student_in")
    field = (S.get("field_in") or "").strip()
    S.rec["field_of_study"] = field or None
    go_next("demo")


def screen_demo():
    st.markdown(texts.DEMO_HEADER)
    st.number_input(texts.AGE_LABEL, min_value=15, max_value=99, step=1, value=None, key="age_in")
    st.radio(texts.GENDER_LABEL, texts.GENDER_OPTIONS, index=None, key="gender_in")
    st.radio(texts.STUDENT_LABEL, texts.STUDENT_OPTIONS, index=None, key="student_in")
    st.text_input(texts.FIELD_LABEL, max_chars=60, key="field_in")
    st.button(texts.CONTINUE, key="demo_next", on_click=on_demo)


def on_pilot_fb():
    if not on_step("pilot_fb"):
        return
    S.rec["pilot_feedback"] = (S.get("pilot_in") or "").strip() or None
    go_next("pilot_fb")


def screen_pilot_fb():
    st.text_area(texts.PILOT_QUESTION, max_chars=2000, key="pilot_in")
    st.button(texts.CONTINUE, key="pilot_next", on_click=on_pilot_fb)


# ---------------------------------------------------------------- end

def on_retry():
    S.need_save = True


def screen_end():
    link = config.CONTACT_FORM_URL or "[link missing]"
    st.subheader("Thank you!")
    st.markdown(texts.END_TEXT.format(points=S.rec["total_points"],
                                      code=S.rec["participant_id"], link=link))
    if config.SHOW_DEBRIEF:
        st.info(texts.DEBRIEF)
    if not S.last_save_ok:
        st.error(texts.END_SAVE_FAILED)
        st.button(texts.END_RETRY, on_click=on_retry)


# ---------------------------------------------------------------- main

def main():
    init()
    guard_real_mode()
    rec = S.rec

    if rec is None:
        screen_consent()
        return

    # keep the ID in the URL so a refresh can resume
    if st.query_params.get("pid") != rec["participant_id"]:
        st.query_params["pid"] = rec["participant_id"]
        st.query_params["seq"] = rec["sequence"]

    step = rec["step"]
    if step == "end" and S.need_save:  # final save before showing the result
        S.need_save = False
        save()

    if step == "prize":
        screen_prize()
    elif step.startswith("rules_"):
        screen_rules(sess.block_index(step))
    elif step.startswith("block_"):
        screen_block(sess.block_index(step))
    elif step.startswith("belief_"):
        screen_belief(int(step[-1]))
    elif step == "prior":
        screen_prior()
    elif step == "demo":
        screen_demo()
    elif step == "pilot_fb":
        screen_pilot_fb()
    elif step == "end":
        screen_end()

    # Save after the screen is drawn, so the participant does not wait for it.
    if S.need_save:
        S.need_save = False
        if not save():
            st.caption(texts.SAVE_DELAY)


main()
