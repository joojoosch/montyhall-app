# All texts participants see. Change wording here, nowhere else.
# The names match the doc "Door game: all participant texts".
# Anything in [square brackets] is a placeholder: in real mode the app
# won't start until it is replaced.

import config
import game

TITLE = "The Door Game"
CONTINUE = "Continue"
NEXT = "Next"
SAVE_DELAY = "Saving took a bit longer. You can just continue."
NOT_OPEN = "The study isn't open yet. Please try again later."

# 1. Consent: a short version everyone sees, the full text behind "More details"
CONSENT_SHORT = """A short study for my bachelor thesis at the University of St. Gallen (HSG).

- You play 25 rounds of a short game and answer a few questions (about 10 minutes).
- Your choices matter: two randomly drawn participants will be paid their game earnings in cash.
- Your answers are anonymous. You don't need to give your name or email.
- Taking part is voluntary, and you can stop at any time.
- You must be at least 18 years old.

Questions? joo-ran.schaerer@student.unisg.ch"""
CONSENT_MORE = "More details about the study and your data"
CONSENT_TEXT = """**What is this study about?**
I'm Joo-Ran Schärer, and this study is part of my bachelor thesis at
the University of St. Gallen (HSG). It looks at how people make decisions in a simple game.

**What will you do?**
You play 25 rounds of a short game and answer a few questions.
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
Write to me at joo-ran.schaerer@student.unisg.ch."""
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
2. The host opens one of the two doors you didn't pick. He always opens
   a door with no trophy behind it. If neither of them has the trophy, he
   picks one at random.
3. After the host has opened a door, you can either stay with your door or
   switch to the other door that is still closed.

Trophy found: **100 points**. No trophy: **0 points**."""

# Penalty rules. The first penalty part says "same game, one change";
# the second one has to say that the old penalty is gone.
RULES_PEN_SWITCH = """Same game, one change: **switching away from your first choice now reduces the value of the trophy by 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_PEN_STAY = """Same game, one change: **staying with your first choice now reduces the value of the trophy by 25 points.**

- Win after staying: 75 points
- Win after switching: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_SWITCH = """The rule changes: staying is free again, but
**switching away from your first choice now reduces the value of the trophy by 25 points.**

- Win after switching: 75 points
- Win after staying: 100 points
- No trophy: 0 points"""

RULES_SECOND_PEN_STAY = """The rule changes: switching is free again, but
**staying with your first choice now reduces the value of the trophy by 25 points.**

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
DECIDE_PROMPT = "The host opened door {opened}. There is no trophy behind it."
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
that the trophy is behind the **closed door you did not pick**?

Answer from your feeling while playing. Don't calculate.
(Your answer does not affect your points.)"""
# second time only (after game 25): same question, plus a neutral intro
BELIEF2_HEADER = "The same question again"
BELIEF2_INTRO = ("You have now played all 25 games. Please answer this question again, "
                 "from your feeling now. Your answer can be the same as before or different.")
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


# Exploratory penalty questions (after the first-game question, before "About you").
# One question per penalty part, both on one page, in random order.
# Which text someone sees depends on what they did in that part (10 games):
# 6-10 stays = "stayed", 0-4 stays = "switched", 5 stays = "equal".
THRESH_HEADER = "Two last questions about the penalty"
THRESH_NOTE = "These are hypothetical. Your answer does not affect your points."

# part where STAYING reduced the value of the trophy
THRESH_STAY_STAYED = ("In the part where staying with your first choice reduced the value of the "
                      "trophy by 25 points, you more often stayed. How big would the reduction "
                      "have to be for you to switch instead?")
THRESH_STAY_SWITCHED = ("In the part where staying with your first choice reduced the value of the "
                        "trophy by 25 points, you more often switched. How small would the "
                        "reduction have to be for you to stay instead?")
THRESH_STAY_EQUAL = ("In the part where staying with your first choice reduced the value of the "
                     "trophy by 25 points, you stayed and switched equally often. From which size "
                     "of the reduction on would you switch rather than stay?")

# part where SWITCHING reduced the value of the trophy (mirror texts)
THRESH_SWITCH_SWITCHED = ("In the part where switching to the other door reduced the value of the "
                          "trophy by 25 points, you more often switched. How big would the "
                          "reduction have to be for you to stay instead?")
THRESH_SWITCH_STAYED = ("In the part where switching to the other door reduced the value of the "
                        "trophy by 25 points, you more often stayed. How small would the "
                        "reduction have to be for you to switch instead?")
THRESH_SWITCH_EQUAL = ("In the part where switching to the other door reduced the value of the "
                       "trophy by 25 points, you stayed and switched equally often. From which "
                       "size of the reduction on would you stay rather than switch?")

# answer: exactly one of these three (saved as the code on the left)
THRESH_OPTIONS = {
    "number": "A reduction of this size (enter below)",
    "always_stay": "I would always stay, whatever the reduction",
    "always_switch": "I would always switch, whatever the reduction",
}
THRESH_NUMBER_LABEL = "Size of the reduction in points (0 to 100)"
THRESH_MISSING = ("Please answer both questions. If you choose a size, enter a whole number "
                  "from 0 to 100.")


def thresh_question(block, variant):
    texts_for = {
        config.PEN_STAY: {"stayed": THRESH_STAY_STAYED, "switched": THRESH_STAY_SWITCHED,
                          "equal": THRESH_STAY_EQUAL},
        config.PEN_SWITCH: {"stayed": THRESH_SWITCH_STAYED, "switched": THRESH_SWITCH_SWITCHED,
                            "equal": THRESH_SWITCH_EQUAL},
    }
    return texts_for[block][variant]


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
# The prize form is a big button right under the code (pilot: a text link was easy to miss)
END_TEXT = """If you want to take part in the prize draw, please write this code down
now. It won't be shown again once you leave this page. Then enter it, together
with your email, in the prize draw form:"""
FORM_LINK = "Click here to open the prize draw form ↗"
END_TEXT_AFTER = """After the study, two participants are drawn at random from everyone who
entered their code and contact details in this form. Your contact details are
kept apart from your answers."""
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
