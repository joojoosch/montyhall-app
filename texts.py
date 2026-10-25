# All texts participants see. Change wording here, nowhere else.
# Anything in [square brackets] is a placeholder: in real mode the app
# won't start until it is replaced.

import config
import game

TITLE = "The door game"
CONTINUE = "Continue"
NEXT = "Next"
SAVE_DELAY = "Saving took a bit longer. You can just continue."

# 1. Consent
CONSENT_TEXT = """[CONSENT TEXT: purpose, duration, voluntary, anonymous,
prize draw, contact. Still to be written.]"""
CONSENT_CHECKBOX = "I have read this and agree to take part."
NO_REFRESH = "Please don't refresh or close this page during the study."

# 2. Prize
PRIZE_HEADER = "What your points are worth"
PRIZE_TEXT = """Every 10 points you collect are worth 20 Rappen,
so 1,000 points are worth 20 CHF.

After the study, two participants are drawn at random. Each of them gets
the money for their own points. At the end you get a personal code.
That code is how we contact the winners."""

# 3. Rules of the normal game
RULES_HEADER = "How the game works"
RULES_CONTROL = """Behind one of three doors is a trophy.

1. You pick a door.
2. The host opens one of the other two doors. This door is always empty
   and never your door. If your door has the trophy, he opens one of the
   other two at random.
3. You stay with your door or switch to the other closed door.

Trophy found: **100 points**. No trophy: **0 points**."""

# Penalty rules. The first penalty block says "same game, one change";
# the second one has to say that the old penalty is gone.
RULES_PEN_SWITCH = """Same game, one change: **switching now costs 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_PEN_STAY = """Same game, one change: **staying now costs 25 points.**

- Win after staying: 75 points
- Win after switching: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_SWITCH = """The rule changes: staying is free again, but
**switching now costs 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_STAY = """The rule changes: switching is free again, but
**staying now costs 25 points.**

- Win after staying: 75 points
- Win after switching: 100 points
- No trophy: 0 points"""


def rules_for(block, block_order):
    """Rules text for a block. block_order 2 = first penalty block."""
    if block == config.CONTROL:
        return RULES_CONTROL
    first = block_order == 2
    if block == config.PEN_SWITCH:
        return RULES_PEN_SWITCH if first else RULES_SECOND_PEN_SWITCH
    return RULES_PEN_STAY if first else RULES_SECOND_PEN_STAY


def rules_header(idx):
    return RULES_HEADER if idx == 0 else f"Part {idx + 1} of 3: new rule"


# Comprehension checks (everything must be right to continue)
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
        {"id": "switch_win", "q": "How many points do you get if you switch and win?",
         "options": POINT_OPTIONS, "correct": "75"},
        {"id": "stay_win", "q": "How many points do you get if you stay and win?",
         "options": POINT_OPTIONS, "correct": "100"},
    ],
    config.PEN_STAY: [
        {"id": "stay_win", "q": "How many points do you get if you stay and win?",
         "options": POINT_OPTIONS, "correct": "75"},
        {"id": "switch_win", "q": "How many points do you get if you switch and win?",
         "options": POINT_OPTIONS, "correct": "100"},
    ],
}
COMP_HEADER = "Quick check"
COMP_WRONG = "Not quite. Read the rules again and try once more."
COMP_MISSING = "Please answer every question."
COMP_SUBMIT = "Check answers"

# Games
PICK_PROMPT = "Pick a door."
DECIDE_PROMPT = "The host opened door {opened}. It's empty."
# shown as small lines above the Stay / Switch buttons
PAYOFFS = {
    config.CONTROL: ["Trophy: 100 points"],
    config.PEN_SWITCH: ["Win after staying: 100 points", "Win after switching: 75 points"],
    config.PEN_STAY: ["Win after staying: 75 points", "Win after switching: 100 points"],
}
STAY_BUTTON = "Stay with door {door}"
SWITCH_BUTTON = "Switch to door {door}"
WIN = "You found the trophy!"
LOSE = "No trophy. It was behind door {door}."
POINTS_UNIT = "points"
PENALTY_NOTE = "100 minus 25 for the penalty"
# money bar under the result ("if you are drawn", because only 2 people get paid)
WALLET_LEFT = "Total: {points} points"
WALLET_RIGHT = "{chf} if drawn"
WALLET_MAX = "max. {chf}"
TAG_PICK = "Your pick"
TAG_FINAL = "Your choice"
EMPTY = "Empty"


def counter(trial_in_block, n_in_block):
    return f"Game {trial_in_block} of {n_in_block}"


def total(points):
    # shown at the top right during the games
    if config.SHOW_MONEY:
        return f"{points} points · {game.chf(points)}"
    return f"{points} points"


# Belief question (asked twice)
BELIEF_HEADER = "One question"
BELIEF_QUESTION = """After the host opens a door: how likely do you think it is
that the trophy is behind the **closed door you did not pick first**?

Answer from your feeling while playing. Don't calculate."""
BELIEF_LABEL = "Your answer in %"
BELIEF_MISSING = "Please enter a whole number from 0 to 100."

# Prior knowledge
PRIOR_QUESTION = "Did you know this three-door problem before?"
PRIOR_OPTIONS = ["Yes, I knew it before", "I recognised it during the study", "No"]
PRIOR_MISSING = "Please pick one answer."

# Demographics (all optional)
DEMO_HEADER = "About you"
DEMO_NOTE = "All questions are optional."
AGE_LABEL = "Age"
GENDER_LABEL = "Gender"
GENDER_OPTIONS = ["female", "male", "diverse", "prefer not to say"]
STUDENT_LABEL = "Are you a student?"
STUDENT_OPTIONS = ["Yes", "No", "prefer not to say"]
FIELD_LABEL = "Field of study (if student)"

# Pilot only
PILOT_QUESTION = "Was anything unclear or confusing?"

# End
END_HEADER = "Thank you!"
END_POINTS = "You collected **{points} points**. If you are drawn, you get **{chf}**."
END_CODE_LABEL = "Your personal code"
END_TEXT = """Please save this code. After the study, two participants are
drawn at random. To be contacted if you win, enter your code and contact
details in this separate form: {link}

Your contact details are kept apart from your answers."""
DEBRIEF = """About this study: in the three-door game, switching wins in
2 out of 3 games. We wanted to know why many people stay with their first door."""
END_SAVE_FAILED = "Your answers aren't saved yet. Please press the button below before closing the page."
END_RETRY = "Try saving again"


def placeholders_left():
    """Lists texts that still contain [placeholders], plus a missing form link."""
    left = [name for name, val in globals().items()
            if name.isupper() and isinstance(val, str) and "[" in val and "]" in val]
    if not config.CONTACT_FORM_URL:
        left.append("config.CONTACT_FORM_URL")
    return left
