# Look of the app: colours, font, doors.
# Rule for this experiment: Stay and Switch must look exactly the same,
# and the picked door only gets a small label, never a different colour.

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

/* result after each game */
.result { background: #fff; border: 1px solid var(--line); border-radius: 12px;
  padding: 1rem 1.25rem; margin: 0.75rem 0 1rem; text-align: center; }
.result .head { font-size: 1.2rem; font-weight: 700; }
.result .pts { font-size: 1.05rem; margin-top: 0.25rem; }
.result .note { color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }

/* personal code on the end screen */
.code { font-size: 2.2rem; font-weight: 700; letter-spacing: 0.15em; text-align: center;
  background: #fff; border: 2px dashed var(--door); border-radius: 12px; padding: 0.75rem; margin: 0.5rem 0 1rem; }
</style>
"""


def door(d, state, tag=""):
    """HTML for one door. state: closed, open, trophy."""
    if state == "trophy":
        inner = f'🏆<small>{d}</small>'
    elif state == "open":
        inner = f'{d}<small>{texts.EMPTY}</small>'
    else:
        inner = str(d)
    cls = {"closed": "door", "open": "door open", "trophy": "door trophy"}[state]
    return (f'<div class="{cls}" aria-label="Door {d}"><span class="num">{inner}</span></div>'
            f'<div class="tag">{tag}</div>')


def progress(share):
    pct = max(0, min(100, round(share * 100)))
    return f'<div class="progress"><div style="width:{pct}%"></div></div>'
