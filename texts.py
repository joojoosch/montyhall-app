"""All participant-facing texts. Edit wording here only.

Placeholders in [SQUARE BRACKETS] must be replaced before MODE = "real";
the app refuses to start in real mode while any are left.
"""

import config

# ---------- general ----------

TITLE = "The door game"
NO_REFRESH = "Please do not refresh or close the page during the study."
CONTINUE = "Continue"
NEXT = "Next"
SAVE_DELAY = "Saving took a little longer than usual. You can simply continue."

# ---------- 1. consent ----------

CONSENT_TEXT = """[CONSENT TEXT: purpose, about 10 to 15 minutes, voluntary,
anonymous, how the prize draw works, contact. To be written by Joo-Ran.]"""
CONSENT_CHECKBOX = "I have read this information and agree to take part."

# ---------- 2. prize ----------

PRIZE_TEXT = """Every point you collect is worth money: 20 Rappen for every 10 points.
After the study ends, two participants will be drawn at random. Each of them
receives the money for their own points. For example, 1,000 points are worth
20 CHF. Your points come from your 25 games. At the end you get a personal
code, and winners are contacted through this code."""

# ---------- 3. rules, control block ----------

RULES_CONTROL = """You will see three doors. Behind one of them is a trophy. Choose the
door where you think the trophy is.

After your first pick, the host opens one of the other two doors. This door
never has the trophy behind it, and it is never the door you picked. If you
picked the door with the trophy, both other doors are empty and the host
picks one of them at random.

Then you can stay with your door or switch to the other closed door. If you
find the trophy you get 100 points, otherwise 0 points."""

# ---------- 7./8. rules, penalty blocks ----------

RULES_PEN_SWITCH = """Everything stays the same, but now there is a penalty of 25 points if
you switch. If you find the trophy after switching, you get 75 points instead
of 100. If you find the trophy by staying with your first door, you get the
full 100 points. If you do not find the trophy, you get 0 points."""

RULES_PEN_STAY = """Everything stays the same, but now there is a penalty of 25 points if
you stay with your first door. If you find the trophy by staying, you get 75
points instead of 100. If you find the trophy by switching, you get the full
100 points. If you do not find the trophy, you get 0 points."""

# Second penalty block: "everything stays the same" would be wrong here,
# because the earlier penalty is removed. PROPOSED wording, check it.
RULES_SECOND_PEN_SWITCH = """Important: the rules change now. The penalty for staying no longer
applies. Instead, there is now a penalty of 25 points if you switch. If you
find the trophy after switching, you get 75 points instead of 100. If you
find the trophy by staying with your first door, you get the full 100 points.
If you do not find the trophy, you get 0 points."""

RULES_SECOND_PEN_STAY = """Important: the rules change now. The penalty for switching no longer
applies. Instead, there is now a penalty of 25 points if you stay with your
first door. If you find the trophy by staying, you get 75 points instead of
100. If you find the trophy by switching, you get the full 100 points. If you
do not find the trophy, you get 0 points."""


def rules_for(block, block_order):
    if block == config.CONTROL:
        return RULES_CONTROL
    first = block_order == 2
    if block == config.PEN_SWITCH:
        return RULES_PEN_SWITCH if first else RULES_SECOND_PEN_SWITCH
    return RULES_PEN_STAY if first else RULES_SECOND_PEN_STAY


# ---------- comprehension checks ----------

POINT_OPTIONS = ["0", "25", "50", "75", "100"]

COMPREHENSION = {
    config.CONTROL: [
        {"id": "host_trophy", "q": "Can the host open the door with the trophy?",
         "options": ["Yes", "No"], "correct": "No"},
        {"id": "host_pick", "q": "Can the host open the door you picked?",
         "options": ["Yes", "No"], "correct": "No"},
        {"id": "points_win", "q": "How many points do you get if you find the trophy?",
         "options": POINT_OPTIONS, "correct": "100"},
    ],
    config.PEN_SWITCH: [
        {"id": "switch_win", "q": "How many points do you get if you switch and win the trophy?",
         "options": POINT_OPTIONS, "correct": "75"},
        {"id": "stay_win", "q": "How many points do you get if you stay and win the trophy?",
         "options": POINT_OPTIONS, "correct": "100"},
    ],
    config.PEN_STAY: [
        {"id": "stay_win", "q": "How many points do you get if you stay and win the trophy?",
         "options": POINT_OPTIONS, "correct": "75"},
        {"id": "switch_win", "q": "How many points do you get if you switch and win the trophy?",
         "options": POINT_OPTIONS, "correct": "100"},
    ],
}
COMP_HEADER = "Before you start, please answer these questions."
COMP_WRONG = "That is not correct. Please read the rules again and try once more."
COMP_SUBMIT = "Check my answers"
COMP_MISSING = "Please answer all questions."

# ---------- trials ----------

PICK_PROMPT = "Choose a door."
DECIDE_PROMPT = "The host opened door {opened}. It is empty."
PAYOFFS = {
    config.CONTROL: "Find the trophy: 100 points",
    config.PEN_SWITCH: "Switch and win: 75 points · Stay and win: 100 points",
    config.PEN_STAY: "Stay and win: 75 points · Switch and win: 100 points",
}
STAY_BUTTON = "Stay with door {door}"
SWITCH_BUTTON = "Switch to door {door}"
WIN = "You found the trophy!"
LOSE = "No trophy this time. The trophy was behind door {door}."
TRIAL_POINTS = "Points in this game: {points}"
PENALTY_NOTE = "Because of the penalty you get 75 instead of 100 points."
NEW_TOTAL = "Your total: {total} points"


def counter(trial_in_block, n_in_block, total):
    return f"Trial {trial_in_block} of {n_in_block} · Total: {total} points"


# ---------- beliefs ----------

BELIEF_QUESTION = """After the host has opened one door, how likely do you think it is that
the trophy is behind the closed door that you did not pick first? Please do
not calculate, just answer from the feeling you got while playing."""
BELIEF_LABEL = "Your answer in % (0 to 100)"
BELIEF_MISSING = "Please enter a whole number between 0 and 100."

# ---------- prior knowledge ----------

PRIOR_QUESTION = "Did you know the three-door problem before this study?"
PRIOR_OPTIONS = ["I knew it before", "I recognised it during the study", "I did not know it"]
PRIOR_MISSING = "Please choose one answer."

# ---------- demographics (all optional) ----------

DEMO_HEADER = "A few questions about you. All of them are optional."
AGE_LABEL = "Age"
GENDER_LABEL = "Gender"
GENDER_OPTIONS = ["female", "male", "diverse", "prefer not to say"]
STUDENT_LABEL = "Are you currently a student?"
STUDENT_OPTIONS = ["Yes", "No", "prefer not to say"]
FIELD_LABEL = "If yes: field of study"

# ---------- pilot feedback ----------

PILOT_QUESTION = "Was anything unclear or confusing?"

# ---------- end ----------

END_TEXT = """Thank you for taking part. You collected **{points}** points.
Your personal code is **{code}**. Please save it.

After the study ends, two participants will be drawn at random. If you want
to be contacted in case you win, please enter your code and your contact
details in this separate form: {link}

Your contact details are stored separately from your answers."""
DEBRIEF = """About this study: in the three-door problem, switching wins in 2 of 3
cases. We were interested in why many people stay with their first door."""
END_SAVE_FAILED = ("Your answers could not be saved yet. Please press the button "
                   "below to try again before closing the page.")
END_RETRY = "Try saving again"
ALREADY_DONE = "You have already completed this study. Your personal code is **{code}**."

# ---------- styling (neutral, phone friendly) ----------

CSS = """
<style>
#MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
.block-container {max-width: 680px; padding-top: 2rem;}
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  width: 100%; min-height: 3.2rem; font-size: 1.05rem;
}
/* keep door buttons and Stay/Switch side by side on phones */
div[data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 0.5rem;}
div[data-testid="stHorizontalBlock"] > div {min-width: 0 !important; flex: 1 1 0 !important;}
.doors {display: flex; gap: 0.5rem; justify-content: center; margin: 1rem 0;}
.door {flex: 1 1 0; max-width: 140px; aspect-ratio: 2 / 3; border-radius: 10px;
  border: 2px solid #8a8a8a; background: #f2efe9; display: flex;
  flex-direction: column; align-items: center; justify-content: center;
  font-size: 1rem; color: #222; text-align: center;}
.door .big {font-size: 2rem; line-height: 1.2;}
.door.picked {border: 4px solid #333;}
.door.opened {background: #d9d9d9; color: #666;}
.counter {text-align: center; font-weight: 600; margin-bottom: 0.5rem;}
.payoff {text-align: center; margin: 0.5rem 0 1rem 0;}
</style>
"""

DOOR_LABELS = {
    "closed": ("🚪", "Door {d}"),
    "picked": ("🚪", "Door {d}<br>your pick"),
    "opened": ("–", "Door {d}<br>empty"),
    "trophy": ("🏆", "Door {d}"),
    "empty": ("–", "Door {d}<br>empty"),
}
FINAL_MARK = "<br><b>your final choice</b>"


def placeholders_left():
    """Names of texts that still contain [PLACEHOLDER] markers."""
    left = [name for name, val in globals().items()
            if name.isupper() and isinstance(val, str) and "[" in val and "]" in val
            and name != "CSS"]
    if not config.CONTACT_FORM_URL:
        left.append("config.CONTACT_FORM_URL")
    return left
