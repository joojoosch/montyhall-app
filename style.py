# Look of the app: colours, font, doors, result card.
# Rules for this experiment:
# - Stay and Switch must look exactly the same.
# - The picked door only gets a small label, never a different colour.
# - The result looks only depends on win or loss, never on stay or switch.

import config
import game
import texts

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');

:root {
  --bg: #F3F5F8;
  --ink: #1E2433;
  --muted: #5A6375;
  --line: #D5DAE3;
  --door: #34427A;
  --frame: #232B4F;
  --brass: #D4AF37;
  --inside: #1B1F2B;
  --gold-inside: #FBF1CF;
  --win: #17784A;
  --win-bg: #FFF8E1;
  --gold: #E3B428;
  --loss-bg: #E9ECF1;
}

/* font everywhere except Streamlit's icon font */
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3,
.stApp button, .stApp input, .stApp textarea, .stApp div[data-testid="stMarkdownContainer"] {
  font-family: 'Atkinson Hyperlegible', system-ui, sans-serif;
}
.stApp { background: var(--bg); color: var(--ink); }
.block-container { max-width: 620px; padding: 1.5rem 1rem 4rem; }
.stApp h1, .stApp h2, .stApp h3 { color: var(--ink); font-weight: 700; letter-spacing: -0.01em; }
.stApp p, .stApp li { font-size: 1.05rem; line-height: 1.55; }

/* hide Streamlit's menu, header and footer for participants */
header[data-testid="stHeader"], #MainMenu, footer { display: none; }

/* progress line at the top */
.progress { height: 4px; background: var(--line); border-radius: 2px; margin-bottom: 1.5rem; }
.progress > div { height: 100%; background: var(--door); border-radius: 2px; }

/* buttons: big enough for thumbs, all the same neutral style */
/* backup for older Streamlit versions: stretch buttons to the full column */
div[data-testid="stElementContainer"]:has(div.stButton),
div[data-testid="stElementContainer"]:has(div[data-testid="stFormSubmitButton"]),
div.stButton, div[data-testid="stButton"], div[data-testid="stFormSubmitButton"] { width: 100% !important; }
div.stButton button, div[data-testid="stButton"] button { width: 100% !important; }
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  width: 100%; min-height: 3.2rem; font-size: 1.05rem; border-radius: 10px;
  background: #fff; color: var(--ink); border: 1.5px solid var(--ink);
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
  background: #E9ECF2; color: var(--ink); border-color: var(--ink);
}
div.stButton > button:focus-visible { outline: 3px solid var(--brass); outline-offset: 2px; }
div.stButton > button:disabled { opacity: 0.4; }
/* "Continue" / "Next" buttons are filled so the way forward is clear */
.st-key-go button, div[class*="st-key-go"] button, div[data-testid="stFormSubmitButton"] > button {
  background: var(--ink); color: #fff;
}
div[class*="st-key-go"] button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
  background: #343C52; color: #fff;
}

/* door buttons: same width as the door, centred under it */
div[class*="st-key-pick_"] button { max-width: 150px !important; margin: 0 auto; display: block; }

/* keep the three doors (and Stay/Switch) side by side on phones */
div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.6rem; }
div[data-testid="stHorizontalBlock"] > div { min-width: 0 !important; flex: 1 1 0 !important; }

/* game header: game number left, points right */
.gamebar { display: flex; justify-content: space-between; font-weight: 700;
  font-size: 1rem; margin-bottom: 0.75rem; }
.gamebar .pts { color: var(--muted); font-weight: 400; }

/* doors */
.door {
  position: relative; max-width: 150px; margin: 0 auto; aspect-ratio: 3 / 5;
  background: var(--door); border: 5px solid var(--frame);
  border-radius: 70px 70px 6px 6px;
  box-shadow: inset 0 0 0 9px var(--door), inset 0 0 0 11px #2A3666;
  display: flex; align-items: center; justify-content: center;
}
.door .num { display: flex; flex-direction: column; align-items: center; line-height: 1.1;
  color: var(--brass); font-size: 2.4rem; font-weight: 700; font-family: 'Atkinson Hyperlegible', system-ui, sans-serif; }
.door::after {  /* door knob */
  content: ""; position: absolute; right: 11%; top: 58%;
  width: 10px; height: 10px; border-radius: 50%; background: var(--brass);
}
.door.open { background: var(--inside); box-shadow: none; }
.door.open::after, .door.trophy::after { display: none; }
.door .num small { font-size: 0.85rem; font-weight: 400; margin-top: 0.3rem; }
.door.open .num { color: #8C95A8; font-size: 1.6rem; }
.door.trophy { background: var(--gold-inside); box-shadow: none; }
.door.trophy .num { font-size: 2.6rem; color: var(--frame); }
.tag { text-align: center; font-size: 0.9rem; color: var(--muted); min-height: 1.5em; margin: 0.4rem 0 0.5rem; }
.tag b { color: var(--ink); }

.prompt { text-align: center; font-size: 1.1rem; margin: 0.5rem 0 0.25rem; }
.payoffs { text-align: center; color: var(--muted); font-size: 0.95rem; margin-bottom: 1rem; }

/* result after each game: big points number + money bar */
.result { border-radius: 14px; padding: 1rem 1.25rem 1.1rem; margin: 0.25rem 0 1rem; text-align: center; }
.result.win { background: var(--win-bg); border: 2px solid var(--gold); }
.result.loss { background: var(--loss-bg); border: 2px solid var(--line); }
.result .big { font-size: 3.4rem; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.result.win .big { color: var(--win); animation: pop 0.45s ease-out; }
.result.loss .big { color: #8C95A8; }
.result .unit { font-size: 0.95rem; color: var(--muted); margin-bottom: 0.4rem; }
.result .head { font-size: 1.15rem; font-weight: 700; }
.result .note { color: var(--muted); font-size: 0.95rem; margin-top: 0.15rem; }
.wallet { margin-top: 0.9rem; text-align: left; }
.wallet .bar { display: flex; height: 14px; background: #fff; border: 1px solid var(--line);
  border-radius: 7px; overflow: hidden; }
.wallet .old { background: var(--door); }
.wallet .gain { background: var(--gold); animation: grow 0.7s ease-out 0.15s both; }
.wallet .line { display: flex; justify-content: space-between; gap: 0.5rem; font-size: 0.88rem; margin-top: 0.35rem; white-space: nowrap; }
.wallet .line b { color: var(--ink); }
.wallet .line span:last-child { color: var(--muted); }
.wallet .max { font-size: 0.8rem; color: var(--muted); text-align: right; }

/* the trophy door glows when you win */
.door.trophy.won { box-shadow: 0 0 0 4px var(--gold), 0 0 24px 6px rgba(227, 180, 40, 0.55);
  animation: glow 0.6s ease-out; }

@keyframes pop { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.12); opacity: 1; } 100% { transform: scale(1); } }
@keyframes grow { from { width: 0; } }
@keyframes glow { from { box-shadow: 0 0 0 0 var(--gold); } }
@media (prefers-reduced-motion: reduce) {
  .result.win .big, .wallet .gain, .door.trophy.won { animation: none; }
}

/* personal code on the end screen */
.code { font-size: 2.2rem; font-weight: 700; letter-spacing: 0.15em; text-align: center;
  background: #fff; border: 2px dashed var(--door); border-radius: 12px; padding: 0.75rem; margin: 0.5rem 0 1rem; }
</style>
"""


def door(d, state, tag="", won=False):
    """HTML for one door. state: closed, open, trophy. won=True makes the trophy glow."""
    if state == "trophy":
        inner = f'🏆<small>{d}</small>'
    elif state == "open":
        inner = f'{d}<small>{texts.EMPTY}</small>'
    else:
        inner = str(d)
    cls = {"closed": "door", "open": "door open", "trophy": "door trophy"}[state]
    if won and state == "trophy":
        cls += " won"
    return (f'<div class="{cls}" aria-label="Door {d}"><span class="num">{inner}</span></div>'
            f'<div class="tag">{tag}</div>')


def progress(share):
    pct = max(0, min(100, round(share * 100)))
    return f'<div class="progress"><div style="width:{pct}%"></div></div>'


def result_card(trial, total_points):
    """Big result after each game: +points, what happened, and the money bar."""
    won = trial["won"]
    head = texts.WIN if won else texts.LOSE.format(door=trial["trophy_door"])
    note = f'<div class="note">{texts.PENALTY_NOTE}</div>' if trial["penalty_applied"] else ""

    # money bar: blue = points before this game, gold = points just won
    maxp = game.max_points()
    old_pct = 100 * (total_points - trial["points"]) / maxp
    gain_pct = 100 * trial["points"] / maxp
    left = texts.WALLET_LEFT.format(points=total_points)
    right = texts.WALLET_RIGHT.format(chf=game.chf(total_points)) if config.SHOW_MONEY else ""
    wallet = (f'<div class="wallet"><div class="bar">'
              f'<div class="old" style="width:{old_pct:.1f}%"></div>'
              f'<div class="gain" style="width:{gain_pct:.1f}%"></div></div>'
              f'<div class="line"><b>{left}</b><span>{right}</span></div>')
    if config.SHOW_MONEY:
        wallet += f'<div class="max">{texts.WALLET_MAX.format(chf=game.chf(maxp))}</div>'
    wallet += "</div>"

    return (f'<div class="result {"win" if won else "loss"}">'
            f'<div class="big">+{trial["points"]}</div><div class="unit">{texts.POINTS_UNIT}</div>'
            f'<div class="head">{head}</div>{note}{wallet}</div>')
