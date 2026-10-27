# Monty Hall experiment app (bachelor thesis, Joo-Ran Schärer)

## Files
| File | What it does |
|---|---|
| `app.py` | the screens (Streamlit) |
| `texts.py` | **all participant texts**: edit wording here only |
| `style.py` | colours, font, doors and the result card |
| `balance.py` | keeps sequence A and B balanced |
| `config.py` | constants: trials, points, `MODE`, `CONTACT_FORM_URL`, `SHOW_DEBRIEF` |
| `game.py` | game rules (host, points, sequence, code) |
| `session.py` | participant record, order of screens, resume after refresh |
| `storage.py` | saving to the private GitHub data repo (or locally for testing) |
| `export.py` | JSON files → `trials.csv` + `participants.csv` |
| `tests/` | automated tests (`pytest -q`) |

## Run on your own computer
```
pip install streamlit requests pytest
pytest -q                 # all tests must pass
streamlit run app.py      # opens in the browser; saves to local_data/
```
Without secrets the app saves into `local_data/` (only allowed in pilot mode).

## Deploy (Streamlit Community Cloud)
1. Upload all files to the GitHub repo `montyhall-app` (also the `.streamlit` folder, but never a `secrets.toml`).
2. share.streamlit.io → **Create app** → repo `montyhall-app`, branch `main`, file `app.py` → Deploy.
3. App → **Settings → Secrets**, paste (with your own token):
   ```
   GITHUB_TOKEN = "..."
   DATA_REPO = "joojoosch/montyhall-data"
   DATA_BRANCH = "main"
   ```
4. Open the app. The grey line at the top must say `PILOT MODE · saving: github`.

**Token** (create on deployment day): GitHub → profile picture → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token. Expiration: end of December. Repository access: *Only select repositories* → `montyhall-data`. Permissions: **Contents: Read and write**. Copy it straight into the Streamlit secrets.

## After every change to the code
Streamlit reloads `app.py` after a push, but can keep other files (like
`texts.py` or `config.py`) in memory. So after every push: share.streamlit.io
-> three dots next to the app -> **Reboot app**, then check in a private window.

## Pilot → real
In `config.py` set `MODE = "real"` and commit. Before that, fill `CONSENT_TEXT` in `texts.py` and `CONTACT_FORM_URL` in `config.py`: in real mode the app refuses to start while placeholders are left or the GitHub secrets are missing. Pilot data stays in `data/pilot/`, real data goes to `data/real/`.

**Wake the app** (open the link yourself) before launch and before every reminder: free apps sleep after 12 hours without visits.

## Where the data is
Private repo `montyhall-data`, one file per participant: `data/{mode}/{code}_{sequence}.json`. Dropouts stay with `"completed": false`. Finished participants also get an empty marker in `data/{mode}/completed/` (used for balancing A and B). Saved after consent, after every trial and after every screen.

## Export to CSV
Download the data repo (GitHub → Code → Download ZIP), unzip, then:
```
python export.py montyhall-data-main/data/real out/
```

## Analysis
The rules (test directions, thresholds, belief bands) are fixed at the top of
`analysis.py` since 25 Oct 2026, before data collection. `tests/test_analysis.py`
fails if anyone changes them.
```
pip install -r requirements-analysis.txt
python export.py montyhall-data-main/data/real out/            # optional: CSV tables
python analysis.py montyhall-data-main/data/real results/      # all tests -> results/results.md
```
Output: `results.md` (H1, H2, H3a, H3b, patterns x beliefs, robustness checks),
`participants_summary.csv`, `crosstab_*.csv`, `learning.csv`, `scatter.png`.

**Exploratory part** (the two penalty questions, added 27 Oct): a separate block at the
end of `analysis.py`, written to `exploratory.md`, `exploratory_*.csv` and
`exploratory_thresholds.png`. Descriptive only, no tests on subgroups, not paid.
It never changes `results.md` (tested in `tests/test_analysis.py`).

Test the analysis on fake data first:
```
python simulate_participants.py 60 data/fake
python analysis.py data/fake results_fake/
```
Fake files contain the true type (`_true_type`), so `results.md` then also shows
how well the patterns find the types.

## Fields that differ from the brief
- Balancing: a new participant gets the sequence with fewer *completed + currently playing* people (playing = started in the last 45 min). Simultaneous starts are handled one after the other. The counts at that moment are saved as `assign_counts`.
- File name contains the sequence (`ABC234_A.json`).
- Extra fields: `resumed`, `resume_count` (participant level), `after_resume` (trial level), `field_of_study`, `start_epoch`.
- `penalty_applied` = 1 only when a win came through the penalised option (points really reduced).
- Response times are measured on the server, so they include internet delay. Use them only roughly.

## Manual test checklist (pilot mode, before Wed 28 Oct)
- [ ] Full run on a **phone**, sequence A and B (open the app in a private window until you get each).
- [ ] Doors and Stay/Switch buttons sit side by side at phone width; nothing cut off.
- [ ] Give wrong comprehension answers → message appears, rules still visible; then correct → continues.
- [ ] Belief question: "Next" without a number → message; with 60 → continues.
- [ ] **Refresh in the middle of a penalty block** → you are back in the same block at the next trial, points total unchanged.
- [ ] Lock the phone for 2 minutes mid-block, unlock → same as above.
- [ ] Double-tap "Next" and the door buttons quickly → never skips a trial.
- [ ] File appears in `montyhall-data/data/pilot/` and opens; `trials` has 25 entries at the end; `completed: true`.
- [ ] Simultaneous start: 3 people press "Continue" on the consent page at the same moment → 3 complete files.
- [ ] End screen shows points, code and form link.
- [ ] Note the time you need for one full run (for the consent text).
- [ ] Launch day: `MODE = "real"` pushed → **Reboot app** → grey "Pilot mode" line is gone → play once, file appears in `data/real/` → delete that test file (and its marker in `data/real/completed/`).
