"""All constants of the experiment in one place."""

N_CONTROL = 5          # trials in the control block
N_PENALTY = 10         # trials in each penalty block
POINTS_WIN = 100       # points for finding the trophy
PENALTY = 25           # deducted when the penalised option wins

MODE = "pilot"         # "pilot" or "real" -- decides the data folder
APP_VERSION = "0.1.0"
CONTACT_FORM_URL = ""  # separate contact form, filled in by Joo-Ran
# Off by default: a debrief that says "switching wins 2 of 3" can spread to
# people who have not played yet. Better: send it after data collection.
SHOW_DEBRIEF = False

DOORS = (1, 2, 3)

# Block codes as saved in the data
CONTROL = "control"
PEN_SWITCH = "pen_switch"   # switching is penalised
PEN_STAY = "pen_stay"       # staying is penalised
BLOCKS = (CONTROL, PEN_SWITCH, PEN_STAY)

# Order of blocks per sequence
SEQUENCES = {
    "A": (CONTROL, PEN_SWITCH, PEN_STAY),
    "B": (CONTROL, PEN_STAY, PEN_SWITCH),
}

# Personal code: no 0/O, 1/I/L to avoid confusion
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
