# All texts participants see. Change wording here, nowhere else.
# The names match the doc "Door game: all participant texts".
# Anything in [square brackets] is a placeholder: in real mode the app
# won't start until it is replaced.

import config
import game

TITLE = "The door game"
CONTINUE = "Continue"
NEXT = "Next"
SAVE_DELAY = "Saving took a bit longer. You can just continue."
NOT_OPEN = "The study isn't open yet. Please try again later."

# 1. Consent
CONSENT_TEXT = """**What is this study about?**
I'm Joo-Ran Schärer, and this study is part of my bachelor thesis at
[UNIVERSITY]. It looks at how people make decisions in a simple game with doors.

**What will you do?**
You play 25 short games and answer a few questions.
This takes about 10 minutes. You can use a phone or a computer.

**Prize**
In the game you collect points. After the study closes on 8 November 2026,
two participants are drawn at random. They each get 20 Rappen for every
10 points they collected (up to CHF 50). Only people who finish the study
and enter their personal code in a separate form at the end can be drawn.

**Your data**
The study does not ask for your name or email address, and your answers are
saved without them. If you join the prize draw, your contact details are
collected in a separate form and kept apart from your answers. Your answers
are only used for this bachelor thesis and only reported as group results.

**Taking part is voluntary**
You can stop at any time by closing the page, without giving a reason.
Answers you gave up to that point are kept, without your name. If you want
your answers deleted later, send me your personal code (shown at the end)
before 15 November 2026.

**Who can take part?**
Everyone who is at least 18 years old.

**Questions?**
Write to me at [YOUR UNIVERSITY EMAIL]."""
CONSENT_CHECKBOX = "I am at least 18 years old, I have read this information and I agree to take part."
NO_REFRESH = "Please don't refresh or close this page during the study."

# 2. Prize
PRIZE_HEADER = "Win a real prize"
PRIZE_TEXT = """In the following game you can collect points. Every 10 points you
collect are worth 20 Rappen, so 1,000 points are worth 20 CHF.

After the study, two participants are drawn at random. Each of them gets the
money for the points they earned. At the end you get a personal code. That
code is how we contact the winners. You can decide yourself whether you want
to take part in the draw."""

# 3. Rules of the normal game
RULES_HEADER = "How the game works"
RULES_HEADER_NEW = "Part {part} of 3: new rule"
RULES_CONTROL = """Behind one of three doors is a trophy.

1. You pick a door.
2. The host opens one of the other two doors. This door is always empty
   and never your door. If your door has the trophy, he opens one of the
   other two at random.
3. After the host has opened a door, you can either stay with your door or
   switch to the other door that is still closed.

Trophy found: **100 points**. No trophy: **0 points**."""

# Penalty rules. The first penalty part says "same game, one change";
# the second one has to say that the old penalty is gone.
RULES_PEN_SWITCH = """Same game, one change: **switching away from your first choice now costs 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_PEN_STAY = """Same game, one change: **staying with your first choice now costs 25 points.**

- Win after staying: 75 points
- Win after switching: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_SWITCH = """The rule changes: staying is free again, but
**switching away from your first choice now costs 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_STAY = """The rule changes: switching is free again, but
**staying with your first choice now costs 25 points.**

- Win after staying: 75 points
- Win after switching: 100 points
- No trophy: 0 points"""


def rules_for(block, block_order):
    """Rules text for a block. block_order 2 = first penalty part."""
    if block == config.CONTROL:
        return RULES_CONTROL
    first = block_order == 2
    if block == config.PEN_SWITCH:
        return RULES_PEN_SWITCH if first else RULES_SECOND_PEN_SWITCH
    return RULES_PEN_STAY if first else RULES_SECOND_PEN_STAY


def rules_header(idx):
    return RULES_HEADER if idx == 0 else RULES_HEADER_NEW.format(part=idx + 1)


# 4. Quick check (everything must be right to continue)
COMP_HEADER = "Quick check"
COMP_SUBMIT = "Check answers"
COMP_WRONG = "Not quite. Please read the rules and try again."
COMP_MISSING = "Please answer every question."

POINT_OPTIONS = ["0", "25", "50", "75", "100"]
Q_HOST_TROPHY = "Can the host open the door with the trophy?"
Q_HOST_PICK = "Can the host open the door you picked?"
Q_POINTS_WIN = "How many points do you get if you find the trophy?"
Q_SWITCH_WIN = "How many points do you get if you switch and win?"
Q_STAY_WIN = "How many points do you get if you stay and win?"

COMPREHENSION = {
    config.CONTROL: [
        {"id": "host_trophy", "q": Q_HOST_TROPHY, "options": ["Yes", "No"], "correct": "No"},
        {"id": "host_pick", "q": Q_HOST_PICK, "options": ["Yes", "No"], "correct": "No"},
        {"id": "points_win", "q": Q_POINTS_WIN, "options": POINT_OPTIONS, "correct": "100"},
    ],
    config.PEN_SWITCH: [
        {"id": "switch_win", "q": Q_SWITCH_WIN, "options": POINT_OPTIONS, "correct": "75"},
        {"id": "stay_win", "q": Q_STAY_WIN, "options": POINT_OPTIONS, "correct": "100"},
    ],
    config.PEN_STAY: [
        {"id": "stay_win", "q": Q_STAY_WIN, "options": POINT_OPTIONS, "correct": "75"},
        {"id": "switch_win", "q": Q_SWITCH_WIN, "options": POINT_OPTIONS, "correct": "100"},
    ],
}

# 5. During the games
COUNTER = "Game {n} of {total}"
TOTAL = "{points} points · {chf}"
EMPTY = "Empty"
PICK_PROMPT = "Pick a door."
DOOR_BUTTON = "Door {door}"
TAG_PICK = "Your pick"
DECIDE_PROMPT = "The host opened door {opened}. It's empty."
# small grey lines above the Stay / Switch buttons
PAYOFF_CONTROL = ["Trophy: 100 points"]
PAYOFF_PEN_SWITCH = ["Win after staying: 100 points", "Win after switching: 75 points"]
PAYOFF_PEN_STAY = ["Win after staying: 75 points", "Win after switching: 100 points"]
PAYOFFS = {config.CONTROL: PAYOFF_CONTROL, config.PEN_SWITCH: PAYOFF_PEN_SWITCH,
           config.PEN_STAY: PAYOFF_PEN_STAY}
STAY_BUTTON = "Stay with door {door}"
SWITCH_BUTTON = "Switch to door {door}"


def counter(trial_in_block, n_in_block):
    return COUNTER.format(n=trial_in_block, total=n_in_block)


def total(points):
    # shown at the top right during the games
    if config.SHOW_MONEY:
        return TOTAL.format(points=points, chf=game.chf(points))
    return f"{points} points"


# 6. Result after each game
TAG_FINAL = "Your choice"
POINTS_UNIT = "points"
WIN = "You found the trophy!"
LOSE = "No trophy. It was behind door {door}."
PENALTY_NOTE = "100 minus 25 for the penalty"
# money bar ("if drawn", because only 2 people get paid)
WALLET_LEFT = "Total: {points} points"
WALLET_RIGHT = "{chf} if drawn"
WALLET_MAX = "max. {chf}"

# 7. Belief question (after game 5 and after game 25)
BELIEF_HEADER = "One question"
BELIEF_QUESTION = """After the host opens a door: how likely do you think it is
that the trophy is behind the **closed door you did not pick first**?

Answer from your feeling while playing. Don't calculate.
(Your answer does not affect your points.)"""
BELIEF_LABEL = "Your answer in %"
BELIEF_PLACEHOLDER = "0 to 100"
BELIEF_MISSING = "Please enter a whole number from 0 to 100."

# 9. Questions at the end
PRIOR_QUESTION = "Did you know this three-door problem before?"
PRIOR_OPTIONS = ["Yes, I knew it before", "I recognised it during the study", "No"]
PRIOR_MISSING = "Please pick one answer."

# The question names what the person really did in game 1.
REASON_QUESTION = ("In your very first game you **{choice}**. "
                   "What was the main reason for your choice?")
REASON_CHOICE = {"stay": "stayed with your door", "switch": "switched to the other door"}
REASON_QUESTION_FALLBACK = ("Think back to your very first game. What was the main "
                            "reason for your choice (stay or switch)?")
# saved as the code on the left, shown as the text on the right
REASON_OPTIONS = {
    "better_choice": "I thought it was more likely to win.",
    "equal_chance": "Both doors seemed equally likely, so it didn't matter.",
    "try_out": "I wanted to try out what happens.",
    "gut_feeling": "It felt right, a gut feeling.",
    "no_reason": "No particular reason.",
}


def reason_question(first_choice):
    if first_choice in REASON_CHOICE:
        return REASON_QUESTION.format(choice=REASON_CHOICE[first_choice])
    return REASON_QUESTION_FALLBACK


# 10. About you (all optional)
DEMO_HEADER = "About you"
DEMO_NOTE = "All questions are optional, so you can leave them empty if you want."
AGE_LABEL = "Age"
GENDER_LABEL = "Gender"
GENDER_OPTIONS = ["female", "male", "diverse", "prefer not to say"]
STUDENT_LABEL = "Are you a student?"
STUDENT_OPTIONS = ["Yes", "No", "prefer not to say"]
FIELD_LABEL = "Field of study or job"

# Pilot only
PILOT_QUESTION = "Was anything unclear or confusing?"

# 11. End page
END_HEADER = "Thank you!"
END_POINTS = "You collected **{points} points**. If you are drawn, you get **{chf}**."
END_CODE_LABEL = "Your personal code"
END_TEXT = """If you want to take part in the prize draw, please write this code
down now. It won't be shown again once you leave this page. After the study,
two participants are drawn at random from everyone who entered their code and
contact details in this separate form: {link}

Your contact details are kept apart from your answers."""
DEBRIEF = """About this study: in the three-door game, switching wins in
2 out of 3 games. We wanted to know why many people stay with their first door."""

# 12. Rare messages
END_SAVE_FAILED = "Your answers aren't saved yet. Please press the button below before closing the page."
END_RETRY = "Try saving again"


def placeholders_left():
    """Lists texts that still contain [placeholders], plus a missing form link."""
    left = [name for name, val in globals().items()
            if name.isupper() and isinstance(val, str) and "[" in val and "]" in val]
    if not config.CONTACT_FORM_URL:
        left.append("config.CONTACT_FORM_URL")
    return left
