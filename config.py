# Settings of the experiment, all in one place.

N_CONTROL = 5          # games in the normal block
N_PENALTY = 10         # games in each penalty block
POINTS_WIN = 100       # points for finding the trophy
PENALTY = 25           # taken off when you win with the penalised option

MODE = "pilot"         # "pilot" or "real" - decides the data folder
APP_VERSION = "0.2.0"
CONTACT_FORM_URL = ""  # link to the separate contact form

# Off for now: if the end screen says "switching wins 2 of 3", people could
# tell friends who haven't played yet. Better to send it after data collection.
SHOW_DEBRIEF = False

DOORS = (1, 2, 3)

# block names as they are saved in the data
CONTROL = "control"
PEN_SWITCH = "pen_switch"   # switching costs 25 points
PEN_STAY = "pen_stay"       # staying costs 25 points
BLOCKS = (CONTROL, PEN_SWITCH, PEN_STAY)

# order of the blocks in each sequence
SEQUENCES = {
    "A": (CONTROL, PEN_SWITCH, PEN_STAY),
    "B": (CONTROL, PEN_STAY, PEN_SWITCH),
}

# personal code: no 0/O, 1/I/L so nobody mixes them up
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
