"""Analysis of the door game (bachelor thesis, Joo-Ran Schärer).

Use:      python analysis.py <folder with the participant JSON files> [output folder]
Example:  python analysis.py montyhall-data-main/data/real results/

Writes into the output folder:
  results.md               all results in plain words, hypothesis by hypothesis
  participants_summary.csv one row per analysed participant (counts, pattern, belief band)
  crosstab_*.csv           choice pattern x belief band
  learning.csv             switching rate per game, split by sequence
  scatter.png              switching rate in the two penalty blocks, one dot per person

The rules below were fixed on 25 October 2026, BEFORE data collection, and
follow the design doc (section 6). The GitHub commit date is my proof of that.
Don't change them after seeing the data.
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

import export

# ============================== FIXED RULES (25 Oct 2026) ==============================
ALPHA = 0.05
TESTS = {                      # direction of every test
    "H1": "two-sided",
    "H2": "two-sided",
    "H3a": "two-sided",
    "H3b": "greater",          # one-sided: only "more than chance" is meaningful
}
H1_MAIN = "all"                # main H1 result uses everyone; without try_out is a check
STAYER_MIN = 4                 # control block: stayer = stays in at least 4 of 5 games
BACKUP_MOST = 3                # H1 backup: stays in most (= at least 3) of the 5 games
THRESHOLD = 7                  # choice pattern: at least 7 of 10 in BOTH penalty blocks
ROBUST_THRESHOLDS = (6, 8)
BAND = (43, 57)                # belief band "about 50/50" (from 3/7 and 4/7), inclusive
WIDE_BAND = (40, 60)
KNEW_IT = "Yes, I knew it before"
N_CONTROL, N_PENALTY = 5, 10
# ========================================================================================

PATTERNS = ["stays in both", "stay, then switch", "switches in both", "switch, then stay", "mixed"]
PATTERN_READING = {
    "stays in both": "consistent with familiarity",
    "stay, then switch": "consistent with equiprobability",
    "switches in both": "rational",
    "switch, then stay": "inconsistent",
    "mixed": "no clear pattern",
}


# ---------- data ----------

def load(folder):
    # all files, and the complete ones (only those are analysed)
    recs = export.load_all(folder)
    complete = [r for r in recs if r.get("completed") and len(r.get("trials", [])) == 25]
    return recs, complete


def summarise(rec):
    # one row per participant with everything the tests need
    t = pd.DataFrame(rec["trials"])
    stays = lambda block: int((t[t.block == block].choice == "stay").sum())
    row = {
        "participant_id": rec["participant_id"],
        "sequence": rec["sequence"],
        "first_switch": int(t.iloc[0].switched),          # game 1, before any feedback
        "control_stays": stays("control"),
        "pen_switch_stays": stays("pen_switch"),
        "pen_stay_stays": stays("pen_stay"),
        "belief_1": rec.get("belief_1"),
        "belief_2": rec.get("belief_2"),
        "prior_knowledge": rec.get("prior_knowledge"),
        "first_game_reason": rec.get("first_game_reason"),
        "resumed": bool(rec.get("resumed")),
        "duration_s": rec.get("duration_s"),
        "total_points": rec.get("total_points"),
    }
    row["pen_switch_rate"] = (N_PENALTY - row["pen_switch_stays"]) / N_PENALTY
    row["pen_stay_rate"] = (N_PENALTY - row["pen_stay_stays"]) / N_PENALTY
    row["diff"] = row["pen_stay_rate"] - row["pen_switch_rate"]   # H2 (expected > 0)
    if "_true_type" in rec:                                       # fake data only
        row["_true_type"] = rec["_true_type"]
    return row


def pattern(ps_stays, pt_stays, t=THRESHOLD):
    # ps = switching-penalty block, pt = staying-penalty block (stays out of 10)
    ps_sw, pt_sw = N_PENALTY - ps_stays, N_PENALTY - pt_stays
    if ps_stays >= t and pt_stays >= t:
        return "stays in both"
    if ps_stays >= t and pt_sw >= t:
        return "stay, then switch"
    if ps_sw >= t and pt_sw >= t:
        return "switches in both"
    if ps_sw >= t and pt_stays >= t:
        return "switch, then stay"
    return "mixed"


def band(b, lo_hi=BAND):
    lo, hi = lo_hi
    if b is None or pd.isna(b):
        return "missing"
    return "below" if b < lo else ("above" if b > hi else "50/50 band")


def chance_one_pattern(t=THRESHOLD):
    # probability that a random clicker shows one given pattern (2.95% at 7 of 10)
    p = stats.binom.sf(t - 1, N_PENALTY, 0.5)
    return p * p


# ---------- tests ----------

def binom(k, n, p0, alternative):
    # exact binomial test + exact (Clopper-Pearson) 95% interval
    if n == 0:
        return {"k": 0, "n": 0, "share": None, "p": None, "ci": (None, None)}
    res = stats.binomtest(k, n, p0, alternative=alternative)
    # the interval is always the usual two-sided 95% one, also for the one-sided H3b
    ci = stats.binomtest(k, n, p0).proportion_ci(confidence_level=0.95, method="exact")
    return {"k": k, "n": n, "share": k / n, "p": res.pvalue, "ci": (ci.low, ci.high)}


def test_h1(df, without_try_out=False):
    d = df[df.first_game_reason != "try_out"] if without_try_out else df
    return binom(int(d.first_switch.sum()), len(d), 0.5, TESTS["H1"])


def test_h1_backup(df):
    k = int((df.control_stays >= BACKUP_MOST).sum())
    return binom(k, len(df), 0.5, TESTS["H1"])


def test_h2(df):
    d = df["diff"].to_numpy()
    nz = d[d != 0]
    out = {"n": len(d), "n_pos": int((d > 0).sum()), "n_neg": int((d < 0).sum()),
           "n_zero": int((d == 0).sum()), "median": float(np.median(d)) if len(d) else None,
           "mean": float(np.mean(d)) if len(d) else None, "p": None, "r": None}
    if len(nz) > 0:
        res = stats.wilcoxon(nz, alternative=TESTS["H2"], zero_method="wilcox")
        out["p"] = float(res.pvalue)
        ranks = stats.rankdata(np.abs(nz))
        # matched-pairs rank-biserial correlation (effect size, -1 to 1)
        out["r"] = float((ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum())
    return out


def test_h2_sequence(df):
    # side observation: does the difference depend on the order (learning)?
    a, b = df[df.sequence == "A"]["diff"], df[df.sequence == "B"]["diff"]
    out = {"mean_A": a.mean() if len(a) else None, "mean_B": b.mean() if len(b) else None,
           "n_A": len(a), "n_B": len(b), "p": None}
    if len(a) and len(b):
        out["p"] = float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
    return out


def test_h3a(df, belief="belief_1", lo_hi=BAND):
    stayers = df[df.control_stays >= STAYER_MIN]
    k = int(sum(band(b, lo_hi) == "50/50 band" for b in stayers[belief]))
    return binom(k, len(stayers), 0.5, TESTS["H3a"])


def test_h3b(df, belief="belief_1", lo_hi=BAND, t=THRESHOLD):
    above = df[[band(b, lo_hi) == "above" for b in df[belief]]]
    k = int(sum(pattern(r.pen_switch_stays, r.pen_stay_stays, t) == "stays in both"
                for r in above.itertuples()))
    res = binom(k, len(above), chance_one_pattern(t), TESTS["H3b"])
    res["chance"] = chance_one_pattern(t)
    return res


# ---------- tables ----------

def crosstab(df, t=THRESHOLD, belief="belief_1", lo_hi=BAND):
    pat = [pattern(a, b, t) for a, b in zip(df.pen_switch_stays, df.pen_stay_stays)]
    bnd = [band(b, lo_hi) for b in df[belief]]
    tab = pd.crosstab(pd.Categorical(pat, PATTERNS), pd.Categorical(bnd, ["below", "50/50 band", "above"]),
                      rownames=["pattern"], colnames=["belief"], dropna=False, margins=True,
                      margins_name="total")
    return tab


def learning_table(complete):
    rows = []
    for rec in complete:
        for t in rec["trials"]:
            rows.append({"sequence": rec["sequence"], "game": t["trial_overall"],
                         "block": t["block"], "switched": t["switched"]})
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows)
    return d.pivot_table(index=["game", "block"], columns="sequence", values="switched",
                         aggfunc="mean").round(2)


def scatter(df, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(0)
    colors = {"below": "#b5651d", "50/50 band": "#2a6fb0", "above": "#2e8b57", "missing": "#999999"}
    fig, ax = plt.subplots(figsize=(6, 6.4))
    for name, col in colors.items():
        d = df[[band(b) == name for b in df.belief_1]]
        if len(d):
            jit = lambda s: s + rng.uniform(-0.025, 0.025, len(s))   # move points slightly apart
            ax.scatter(jit(d.pen_switch_rate), jit(d.pen_stay_rate), s=40, alpha=0.8,
                       color=col, label=f"belief 1: {name} (n={len(d)})", edgecolors="white")
    for v in (0.3, 0.7):  # the 7-of-10 lines
        ax.axvline(v, color="#ccc", lw=0.8, zorder=0)
        ax.axhline(v, color="#ccc", lw=0.8, zorder=0)
    ax.plot([0, 1], [0, 1], color="#ccc", lw=0.8, ls="--", zorder=0)
    # name the four corners after the choice patterns
    for x, y, txt, ha, va in [(0.0, 0.0, "stays in both", "left", "bottom"),
                              (0.0, 1.0, "stay, then switch", "left", "top"),
                              (1.0, 1.0, "switches in both", "right", "top"),
                              (1.0, 0.0, "switch, then stay", "right", "bottom")]:
        ax.text(x, y + (0.04 if va == "bottom" else -0.04), txt, ha=ha, va=va,
                fontsize=8, color="#888", style="italic")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Switching rate, switching-penalty block")
    ax.set_ylabel("Switching rate, staying-penalty block")
    ax.set_title("One dot per participant")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ---------- report ----------

def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def pval(p):
    # "p = 0.027" or "p < .001"
    return "p = n/a" if p is None else ("p < .001" if p < 0.001 else f"p = {p:.3f}")


def fmt_binom(r):
    if not r["n"]:
        return "not testable (nobody in this group)"
    return (f"{r['k']} of {r['n']} ({pct(r['share'])}), 95% CI {pct(r['ci'][0])} to "
            f"{pct(r['ci'][1])}, {pval(r['p'])}")


def verdict(p):
    if p is None:
        return "not testable"
    return "significant" if p < ALPHA else "not significant (we cannot tell)"


def run(folder, out="results"):
    os.makedirs(out, exist_ok=True)
    recs, complete = load(folder)
    df = pd.DataFrame([summarise(r) for r in complete])
    if df.empty:
        raise SystemExit("No complete participants found in " + folder)
    df["pattern"] = [pattern(a, b) for a, b in zip(df.pen_switch_stays, df.pen_stay_stays)]
    df["band_1"] = [band(b) for b in df.belief_1]
    df["band_2"] = [band(b) for b in df.belief_2]
    df.to_csv(os.path.join(out, "participants_summary.csv"), index=False)

    L = []  # lines of the report
    w = L.append
    w("# Results: door game\n")
    w(f"Rules fixed on 25 Oct 2026 before data collection. Alpha = {ALPHA}. "
      f"H1, H2, H3a two-sided, H3b one-sided.\n")

    # sample
    started = len(recs)
    w("## Sample\n")
    w(f"- Started: {started}. Complete (analysed): {len(df)}. Not finished: {started - len(df)}.")
    w(f"- Sequence A: {(df.sequence == 'A').sum()}, sequence B: {(df.sequence == 'B').sum()}.")
    w(f"- Continued after a reload: {int(df.resumed.sum())}.")
    if df.duration_s.notna().any():
        w(f"- Duration: median {df.duration_s.median() / 60:.1f} min "
          f"(fastest {df.duration_s.min() / 60:.1f}, slowest {df.duration_s.max() / 60:.1f}).")
    w(f"- Knew the problem before: {(df.prior_knowledge == KNEW_IT).sum()}.")
    reasons = df.first_game_reason.value_counts()
    w("- First-game reason: " + ", ".join(f"{k} {v}" for k, v in reasons.items()) + ".\n")

    # H1
    h1 = test_h1(df)
    h1b = test_h1(df, without_try_out=True)
    bk = test_h1_backup(df)
    w("## H1: most participants do not switch in the control block\n")
    w(f"- **Main (game 1, everyone):** switched {fmt_binom(h1)}. Test against 50%: {verdict(h1['p'])}.")
    w(f"- Check without 'try out' ({reasons.get('try_out', 0)} people left out): switched "
      f"{fmt_binom(h1b)}.")
    w(f"- Backup (stays in at least {BACKUP_MOST} of 5 control games): {fmt_binom(bk)}.\n")

    # H2
    h2 = test_h2(df)
    sq = test_h2_sequence(df)
    w("## H2: switching differs between the penalty blocks\n")
    w(f"- Switching rate: switching-penalty block {pct(df.pen_switch_rate.mean())}, "
      f"staying-penalty block {pct(df.pen_stay_rate.mean())} (means).")
    w(f"- Difference per person (staying-penalty minus switching-penalty): median {h2['median']:+.2f}, "
      f"mean {h2['mean']:+.2f}. Positive {h2['n_pos']}, negative {h2['n_neg']}, zero {h2['n_zero']} "
      f"(zeros dropped).")
    r_txt = "n/a" if h2["r"] is None else f"{h2['r']:+.2f}"
    w(f"- Wilcoxon signed-rank, two-sided: {pval(h2['p'])}, rank-biserial r = {r_txt}. "
      f"{verdict(h2['p']).capitalize()}.")
    w(f"- Side observation, order: mean difference A {sq['mean_A']:+.2f} (n={sq['n_A']}), "
      f"B {sq['mean_B']:+.2f} (n={sq['n_B']}), Mann-Whitney {pval(sq['p'])}.\n"
      if sq["mean_A"] is not None and sq["mean_B"] is not None else
      "- Side observation, order: only one sequence present.\n")

    # H3a
    h3a = test_h3a(df)
    w("## H3a: stayers mostly believe 50/50 (belief 1)\n")
    w(f"- Stayers (at least {STAYER_MIN} of 5 control games stayed): {h3a['n']}.")
    w(f"- In the {BAND[0]}-{BAND[1]}% band: {fmt_binom(h3a)}. Test against 50%: {verdict(h3a['p'])}.\n")

    # H3b
    h3b = test_h3b(df)
    w("## H3b: people who think switching is better still stay in both penalty blocks\n")
    w(f"- Belief 1 above {BAND[1]}%: {h3b['n']} people.")
    w(f"- Stay in both penalty blocks ({THRESHOLD} of 10): {fmt_binom(h3b)}. One-sided test against "
      f"chance ({pct(h3b['chance'])}): {verdict(h3b['p'])}.")
    w("- Read as 'consistent with familiarity', not 'caused by'.\n")

    # patterns and cross-table
    tab = crosstab(df)
    tab.to_csv(os.path.join(out, "crosstab_main.csv"))
    w("## Choice patterns and belief 1\n")
    counts = df.pattern.value_counts()
    for p in PATTERNS:
        w(f"- {p} ({PATTERN_READING[p]}): {counts.get(p, 0)}")
    w(f"\nRandom clickers would land in one of the four patterns about "
      f"{pct(4 * chance_one_pattern())} of the time.\n")
    w("Cross-table (rows: pattern, columns: belief 1 band):\n")
    w("```\n" + tab.to_string() + "\n```\n")
    w("By sequence:\n")
    by_seq = pd.crosstab(pd.Categorical(df.pattern, PATTERNS), df.sequence,
                         rownames=["pattern"], dropna=False)
    w("```\n" + by_seq.to_string() + "\n```\n")

    # robustness
    w("## Robustness checks\n")
    for t in ROBUST_THRESHOLDS:
        r = test_h3b(df, t=t)
        c = pd.Series([pattern(a, b, t) for a, b in zip(df.pen_switch_stays, df.pen_stay_stays)]).value_counts()
        w(f"- Threshold {t} of 10: patterns " + ", ".join(f"{p} {c.get(p, 0)}" for p in PATTERNS)
          + f". H3b: {fmt_binom(r)} vs chance {pct(r['chance'])}.")
        crosstab(df, t=t).to_csv(os.path.join(out, f"crosstab_threshold_{t}.csv"))
    no_knew = df[df.prior_knowledge != KNEW_IT]
    w(f"- Without people who knew the problem (n={len(no_knew)}): H1 {fmt_binom(test_h1(no_knew))}; "
      f"H2 {pval(test_h2(no_knew)['p'])}; H3a {fmt_binom(test_h3a(no_knew))}; "
      f"H3b {fmt_binom(test_h3b(no_knew))}.")
    w(f"- Belief 2 instead of belief 1: H3a {fmt_binom(test_h3a(df, 'belief_2'))}; "
      f"H3b {fmt_binom(test_h3b(df, 'belief_2'))}.")
    w(f"- Wider band {WIDE_BAND[0]}-{WIDE_BAND[1]}%: H3a {fmt_binom(test_h3a(df, lo_hi=WIDE_BAND))}; "
      f"H3b {fmt_binom(test_h3b(df, lo_hi=WIDE_BAND))}.")
    crosstab(df, lo_hi=WIDE_BAND).to_csv(os.path.join(out, "crosstab_wide_band.csv"))
    b1, b2 = df.belief_1.astype(float), df.belief_2.astype(float)
    w(f"- Beliefs: belief 1 median {b1.median():.0f}%, belief 2 median {b2.median():.0f}%. "
      f"Share in the 50/50 band: {pct((df.band_1 == '50/50 band').mean())} -> "
      f"{pct((df.band_2 == '50/50 band').mean())}.\n")

    # learning (side observation)
    learn = learning_table(complete)
    learn.to_csv(os.path.join(out, "learning.csv"))
    w("## Learning (side observation)\n")
    w("Switching rate per game, split by sequence: see learning.csv.\n")

    scatter(df, os.path.join(out, "scatter.png"))
    w("## Figure\n")
    w("scatter.png: one dot per participant. Grey lines mark 3 and 7 of 10 switches.\n")

    # fake data only: how well were the true types found?
    if "_true_type" in df:
        w("## Check on fake data (true type vs pattern)\n")
        w("```\n" + pd.crosstab(df._true_type, df.pattern).to_string() + "\n```\n")

    with open(os.path.join(out, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"{len(df)} complete participants analysed -> {out}/results.md")
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "results")
