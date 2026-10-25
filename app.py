# Monty Hall experiment - the screens.
# Run locally with:  streamlit run app.py
#
# The game rules are in game.py, the order of screens in session.py and the
# saving in storage.py. This file only draws screens and handles buttons.
# Every button calls a function that first checks we are still on the right
# screen, so a double click can't skip anything.

import inspect
import sys
import time

import streamlit as st

import config
import game
from balance import Balancer
import session as sess
import style
import texts
from storage import make_storage

st.set_page_config(page_title=texts.TITLE, page_icon="🚪", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(style.CSS, unsafe_allow_html=True)
S = st.session_state


# ---------- helpers ----------

@st.cache_resource
def get_balancer():
    # one Balancer shared by all participants (same app process)
    return Balancer()


def get_storage():
    # GitHub if the secrets are set, otherwise a local folder (for testing)
    if "storage" not in S:
        try:
            secrets = dict(st.secrets)
        except Exception:
            secrets = {}
        S.storage = make_storage(secrets)
    return S.storage


def save():
    ok = get_storage().save(S.rec)
    S.last_save_ok = ok
    if not ok:
        print(f"[app] SAVE FAILED {S.rec['participant_id']} at {S.rec['step']}",
              file=sys.stderr, flush=True)
    return ok


def current_step():
    return S.rec["step"] if S.rec else "consent"


def set_msg(text):
    # error message that only shows on the screen where it happened
    S.msg = (current_step(), text)


def show_msg():
    if S.get("msg") and S.msg[0] == current_step():
        st.error(S.msg[1])


def on_step(expected):
    return S.rec is not None and S.rec["step"] == expected


def go_next(expected):
    if on_step(expected):
        sess.advance(S.rec)
        S.msg = None
        S.need_save = True


def html(code):
    st.markdown(code, unsafe_allow_html=True)


# Newer Streamlit makes buttons only as wide as their text. I want every
# button to fill its column (centred under the doors, big for thumbs), so
# I pass width="stretch" when this Streamlit version supports it.
_STRETCH = {"width": "stretch"} if "width" in inspect.signature(st.button).parameters else {}
_STRETCH_FORM = ({"width": "stretch"}
                 if "width" in inspect.signature(st.form_submit_button).parameters else {})


def button(where, label, **kwargs):
    return where.button(label, **_STRETCH, **kwargs)


def progress_bar():
    # rough progress through the whole study (screens + games)
    order = sess.steps(S.rec["mode"])
    done = order.index(S.rec["step"]) + len(S.rec["trials"])
    html(style.progress(done / (len(order) + game.total_trials())))


def doors_row(states, tags):
    # three doors next to each other, each with a small label underneath
    for col, d in zip(st.columns(3), config.DOORS):
        with col:
            html(style.door(d, states[d], tags.get(d, "")))


# ---------- start: new participant or coming back after a refresh ----------

def init():
    if S.get("init"):
        return
    S.init = True
    S.rec = None
    S.trial = None
    S.need_save = False
    S.last_save_ok = True
    S.msg = None
    # the ID is in the URL, so after a refresh we can load the saved file
    pid = st.query_params.get("pid")
    seq = st.query_params.get("seq")
    if pid and seq in ("A", "B"):
        rec = get_storage().load(config.MODE, pid, seq)
        if rec is not None and rec.get("mode") == config.MODE:
            S.rec = rec
            if not rec["completed"]:
                sess.mark_resumed(rec)
                S.need_save = True


def check_mode():
    # pilot: small note at the top. real: refuse to run if something is missing
    if config.MODE == "pilot":
        st.caption(f"Pilot mode · saving to {get_storage().kind}")
        return
    if config.MODE != "real":
        st.error("config.MODE must be 'pilot' or 'real'.")
        st.stop()
    problems = texts.placeholders_left()
    if get_storage().kind != "github":
        problems.append("GitHub secrets missing")
    if problems:
        st.error("The study isn't open yet. Please try again later.")
        print(f"[app] real mode blocked: {problems}", file=sys.stderr, flush=True)
        st.stop()


# ---------- 1. consent ----------

def on_consent():
    if S.rec is not None or not S.get("consent_cb"):
        return
    # balanced: the sequence with fewer completed + currently playing people
    pid = game.make_code()
    seq, counts = get_balancer().assign(
        config.MODE, pid, lambda: get_storage().count_completed(config.MODE))
    S.rec = sess.new_record(pid, config.MODE, seq)
    S.rec["assign_counts"] = counts  # what the balance looked like (for the method part)
    S.need_save = True  # the file is created right after consent


def screen_consent():
    st.title(texts.TITLE)
    st.markdown(texts.CONSENT_TEXT)
    st.info(texts.NO_REFRESH)
    agreed = st.checkbox(texts.CONSENT_CHECKBOX, key="consent_cb")
    button(st, texts.CONTINUE, key="go_consent", disabled=not agreed, on_click=on_consent)


# ---------- 2. prize ----------

def screen_prize():
    st.header(texts.PRIZE_HEADER)
    st.markdown(texts.PRIZE_TEXT)
    button(st, texts.CONTINUE, key="go_prize", on_click=go_next, args=("prize",))


# ---------- rules + comprehension check before each block ----------

def on_comp(idx):
    step = f"rules_{idx}"
    if not on_step(step):
        return
    block = sess.block_info(S.rec, idx)[0]
    questions = texts.COMPREHENSION[block]
    answers = {q["id"]: S.get(f"comp_{idx}_{q['id']}") for q in questions}
    if None in answers.values():
        set_msg(texts.COMP_MISSING)
        return
    if sess.check_comprehension(S.rec, block, questions, answers):  # also logs wrong answers
        S.trial = None
        go_next(step)
    else:
        set_msg(texts.COMP_WRONG)


def screen_rules(idx):
    block, order, _ = sess.block_info(S.rec, idx)
    st.header(texts.rules_header(idx))
    st.markdown(texts.rules_for(block, order))
    st.subheader(texts.COMP_HEADER)
    with st.form(f"comp_form_{idx}", border=False):
        for q in texts.COMPREHENSION[block]:
            # index=None: nothing is pre-selected
            st.radio(q["q"], q["options"], index=None, horizontal=True,
                     key=f"comp_{idx}_{q['id']}")
        st.form_submit_button(texts.COMP_SUBMIT, on_click=on_comp, args=(idx,), **_STRETCH_FORM)
    show_msg()


# ---------- the games ----------
# One game has three phases: pick -> decide (stay/switch) -> feedback.

def new_trial(idx):
    S.trial = {
        # unique id, so buttons from an old game can't act on a new one
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
    S.need_save = True  # save after every game, so a refresh loses nothing


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
    html(f'<div class="gamebar"><span>{texts.counter(t["k"], n)}</span>'
         f'<span class="pts">{texts.total(S.rec["total_points"])}</span></div>')

    if t["phase"] == "pick":
        doors_row({d: "closed" for d in config.DOORS}, {})
        html(f'<div class="prompt">{texts.PICK_PROMPT}</div>')
        for col, d in zip(st.columns(3), config.DOORS):
            button(col, f"Door {d}", key=f"pick_{t['id']}_{d}", on_click=on_pick, args=(t["id"], d))

    elif t["phase"] == "decide":
        other = game.remaining_door(t["pick"], t["opened"])
        states = {d: "closed" for d in config.DOORS}
        states[t["opened"]] = "open"
        doors_row(states, {t["pick"]: texts.TAG_PICK})
        html(f'<div class="prompt">{texts.DECIDE_PROMPT.format(opened=t["opened"])}</div>'
             f'<div class="payoffs">{"<br>".join(texts.PAYOFFS[block])}</div>')
        left, right = st.columns(2)  # Stay always left, Switch always right
        button(left, texts.STAY_BUTTON.format(door=t["pick"]), key=f"stay_{t['id']}",
                    on_click=on_choice, args=(t["id"], "stay"))
        button(right, texts.SWITCH_BUTTON.format(door=other), key=f"switch_{t['id']}",
                     on_click=on_choice, args=(t["id"], "switch"))

    else:  # feedback: show what was behind every door, then the result card
        r = t["result"]
        states = {d: ("trophy" if d == t["trophy"] else "open") for d in config.DOORS}
        for col, d in zip(st.columns(3), config.DOORS):
            with col:
                tag = f"<b>{texts.TAG_FINAL}</b>" if d == r["final_door"] else ""
                html(style.door(d, states[d], tag, won=bool(r["won"])))
        html(style.result_card(r, S.rec["total_points"]))
        button(st, texts.NEXT, key=f"go_next_{t['id']}", on_click=on_next_trial, args=(t["id"],))


# ---------- belief question (after the control block and at the end) ----------

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
    st.header(texts.BELIEF_HEADER)
    st.markdown(texts.BELIEF_QUESTION)
    # value=None: empty field, so nobody is anchored on a default number
    st.number_input(texts.BELIEF_LABEL, min_value=0, max_value=100, step=1, value=None,
                    placeholder="0 to 100", key=f"belief_in_{num}")
    button(st, texts.NEXT, key=f"go_belief_{num}", on_click=on_belief, args=(num,))
    show_msg()


# ---------- prior knowledge and demographics ----------

def on_prior():
    if not on_step("prior"):
        return
    if S.get("prior_in") is None:
        set_msg(texts.PRIOR_MISSING)
        return
    S.rec["prior_knowledge"] = S.prior_in
    go_next("prior")


def screen_prior():
    st.radio(texts.PRIOR_QUESTION, texts.PRIOR_OPTIONS, index=None, key="prior_in")
    button(st, texts.NEXT, key="go_prior", on_click=on_prior)
    show_msg()


def on_demo():
    if not on_step("demo"):
        return
    S.rec["age"] = S.get("age_in")
    S.rec["gender"] = S.get("gender_in")
    S.rec["student_status"] = S.get("student_in")
    S.rec["field_of_study"] = (S.get("field_in") or "").strip() or None
    go_next("demo")


def screen_demo():
    st.header(texts.DEMO_HEADER)
    st.caption(texts.DEMO_NOTE)
    st.number_input(texts.AGE_LABEL, min_value=15, max_value=99, step=1, value=None, key="age_in")
    st.radio(texts.GENDER_LABEL, texts.GENDER_OPTIONS, index=None, key="gender_in")
    st.radio(texts.STUDENT_LABEL, texts.STUDENT_OPTIONS, index=None, key="student_in")
    st.text_input(texts.FIELD_LABEL, max_chars=60, key="field_in")
    button(st, texts.CONTINUE, key="go_demo", on_click=on_demo)


def on_pilot_fb():
    if not on_step("pilot_fb"):
        return
    S.rec["pilot_feedback"] = (S.get("pilot_in") or "").strip() or None
    go_next("pilot_fb")


def screen_pilot_fb():
    st.text_area(texts.PILOT_QUESTION, max_chars=2000, key="pilot_in")
    button(st, texts.CONTINUE, key="go_pilot", on_click=on_pilot_fb)


# ---------- end ----------

def on_retry():
    S.need_save = True


def screen_end():
    link = config.CONTACT_FORM_URL or "[link missing]"
    st.header(texts.END_HEADER)
    st.markdown(texts.END_POINTS.format(points=S.rec["total_points"],
                                        chf=game.chf(S.rec["total_points"])))
    st.caption(texts.END_CODE_LABEL)
    html(f'<div class="code">{S.rec["participant_id"]}</div>')
    st.markdown(texts.END_TEXT.format(link=link))
    if config.SHOW_DEBRIEF:
        st.info(texts.DEBRIEF)
    if not S.last_save_ok:
        st.error(texts.END_SAVE_FAILED)
        button(st, texts.END_RETRY, key="go_retry", on_click=on_retry)


# ---------- main ----------

def main():
    init()
    check_mode()
    if S.rec is None:
        screen_consent()
        return

    # keep the ID in the URL so a refresh can continue where it stopped
    if st.query_params.get("pid") != S.rec["participant_id"]:
        st.query_params["pid"] = S.rec["participant_id"]
        st.query_params["seq"] = S.rec["sequence"]

    step = S.rec["step"]
    if step == "end" and S.need_save:  # last save before the thank-you screen
        S.need_save = False
        if save() and get_storage().mark_completed(S.rec):
            get_balancer().finish(S.rec["participant_id"])

    progress_bar()
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

    # save after drawing the screen, so nobody waits for GitHub
    if S.need_save:
        S.need_save = False
        if not save():
            st.caption(texts.SAVE_DELAY)


main()
