"""Stage-transition diagrams from the expert labels: one per participant plus the group, and a pattern check.

The group diagram is a ladder W > N1 > N2 > N3. Circle area = share of time in the stage; the number inside =
chance of staying in that stage at the next 30-s epoch; arrows = moves to another stage (deeper on the left,
lighter on the right), width and label = probability. Each participant is shown as a transition grid (row =
current stage, column = next stage, cell = row percentage, shade = probability); rows with fewer than 5 epochs
are greyed out because their percentages are unreliable. Consecutive epochs within a recording only; uncertain
or unscorable epochs break the chain.

Usage: python src/postprocessing/transitions_figure.py 01 04 07 ...   (default: the amendment-8 sleepers)
Writes studies/01-preprocessing-ablation/results/transitions_sleepers.png and transitions_sleepers.csv
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "01-preprocessing-ablation"
sys.path.insert(0, str(STUDY))
from build_dataset import load_labels  # noqa: E402

SLEEPERS = ["01", "04", "07", "09", "11", "14", "15", "16", "18", "19", "23", "24", "25", "27"]
MAP = {"W": "W", "1": "N1", "2": "N2", "3": "N3"}
ST = ["W", "N1", "N2", "N3"]
COL = {"W": "#d2622c", "N1": "#2f8cc4", "N2": "#5a4ad0", "N3": "#b0429e"}
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
Y = {s: 3 - i for i, s in enumerate(ST)}                         # W at the top


def counts(subs):
    pairs, time = [], {s: 0 for s in ST}
    for sub in subs:
        lab = load_labels(sub)
        for _, g in lab.groupby("session"):
            seq = [MAP.get(x) for x in g.sort_values("t").stage_raw]
            for x in seq:
                if x:
                    time[x] += 1
            pairs += [(sub, a, b) for a, b in zip(seq, seq[1:]) if a and b]
    p = pd.DataFrame(pairs, columns=["sub", "from", "to"])
    return p, time


def matrix(p):
    return pd.crosstab(p["from"], p["to"]).reindex(index=ST, columns=ST, fill_value=0)


def ladder(ax, M, time, title, big=False):
    ax.set_xlim(-1.6, 1.6); ax.set_ylim(-0.75, 3.75); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=13 if big else 10, fontweight="bold", color=INK, pad=4)
    total = max(sum(time.values()), 1)
    prob = M.div(M.sum(1).replace(0, np.nan), axis=0).fillna(0)
    for s in ST:
        share = time[s] / total
        if time[s] == 0:
            ax.add_patch(Circle((0, Y[s]), 0.18, fill=False, ls=(0, (2, 2)), ec=INK2, lw=1))
            ax.text(0, Y[s], s, ha="center", va="center", fontsize=8 if not big else 10, color=INK2)
            continue
        r = (0.24 if big else 0.16) + 0.34 * np.sqrt(share)
        ax.add_patch(Circle((0, Y[s]), r, fc=COL[s], ec=SURFACE, lw=2, zorder=3))
        ax.text(0, Y[s] + (0.07 if big else 0.06), s, ha="center", va="center", color="white", zorder=4,
                fontsize=11 if big else 8, fontweight="bold")
        ax.text(0, Y[s] - (0.13 if big else 0.11), f"{100 * prob.loc[s, s]:.0f}%", ha="center", va="center",
                color="white", zorder=4, fontsize=9 if big else 6.5)
    for a in ST:
        for b in ST:
            pr = prob.loc[a, b]
            if a == b or pr < 0.005:
                continue
            deeper = Y[b] < Y[a]
            x = -0.55 if deeper else 0.55
            rad = 0.45 * (1 if deeper else 1) * (abs(Y[a] - Y[b]) ** 0.4)
            arr = FancyArrowPatch((x * 0.55, Y[a]), (x * 0.55, Y[b]),
                                  connectionstyle=f"arc3,rad={rad if deeper else rad}",
                                  arrowstyle="-|>", mutation_scale=8 + 10 * pr, lw=0.6 + 9 * pr,
                                  color=COL[b], alpha=0.85, zorder=2, shrinkA=10, shrinkB=10)
            ax.add_patch(arr)
            mid = (Y[a] + Y[b]) / 2
            if pr >= (0.02 if big else 0.04):
                ax.text(x * (1.95 if abs(Y[a] - Y[b]) > 1 else 1.55), mid, f"{100 * pr:.0f}%", ha="center", va="center",
                        fontsize=9 if big else 6.5, color=COL[b], fontweight="bold")


def grid(ax, M, title):
    """Transition grid for one person: row = from, column = to, row percentages."""
    present = [s for s in ST if M.loc[s].sum() + M[s].sum() > 0]
    n = M.loc[present, present]
    rowsum = n.sum(1)
    pr = n.div(rowsum.replace(0, np.nan), axis=0)
    ax.imshow(np.zeros((len(present), len(present))), cmap="Greys", vmin=0, vmax=1)
    for i, a in enumerate(present):
        for j, b in enumerate(present):
            v, few = pr.iloc[i, j], rowsum.iloc[i] < 5
            if not few and not np.isnan(v):
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color=COL[b], alpha=0.12 + 0.83 * v, lw=0))
            txt = "" if np.isnan(v) else f"{100 * v:.0f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5,
                    color=GRID if few else ("white" if v > .5 else INK), fontweight="bold" if i == j else None)
    ax.set_xticks(range(len(present)), [f"→{s}" for s in present], fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(present)), present, fontsize=7.5, color=INK2)
    ax.tick_params(length=0, pad=1)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.set_title(title, fontsize=10, fontweight="bold", color=INK, pad=4)


def patterns(M):
    """The five group patterns, checked for one person (True/False/None when not testable)."""
    off = M.values.sum() - np.trace(M.values)
    adj = sum(M.iloc[i, j] for i in range(4) for j in range(4) if abs(i - j) == 1)
    stay = {s: M.loc[s, s] / M.loc[s].sum() if M.loc[s].sum() else np.nan for s in ST}
    left_w = M.loc["W", "N1"] + M.loc["W", "N2"]
    left_n2 = M.loc["N2", "N1"] + M.loc["N2", "W"]
    return {
        "Falls asleep through N1": None if left_w == 0 else M.loc["W", "N1"] > M.loc["W", "N2"],
        "Moves one step at a time (>90%)": None if off == 0 else adj / off > 0.9,
        "N2 steadier than N1": None if np.isnan(stay["N2"]) or np.isnan(stay["N1"]) else stay["N2"] > stay["N1"],
        "N1 is a crossroads (both ways)": M.loc["N1", "W"] > 0 and M.loc["N1", "N2"] > 0,
        "Wakes from N2 via N1": None if left_n2 == 0 else M.loc["N2", "N1"] >= M.loc["N2", "W"],
    }


def main(subs):
    p, time = counts(subs)
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    fig = plt.figure(figsize=(17, 15.5))
    gs = fig.add_gridspec(4, 9, height_ratios=[1.35, 1, 1, 0.95], hspace=0.45, wspace=0.45)
    fig.suptitle("Sleep-stage transitions: each sleeper, and all of them together", x=0.05, ha="left", y=1.0,
                 fontsize=18, fontweight="bold", color=INK)
    fig.text(0.05, 0.948, "Expert labels, 30-s epochs. Top: all 14 together (circle size = time in stage; number inside = chance of "
             "staying; arrows deeper on the left, lighter on the right).\nMiddle: each person's grid, row = current stage, "
             "column = next stage, % of that row; bold diagonal = staying put; grey rows have under 5 epochs.", fontsize=10.5, color=INK2)

    ladder(fig.add_subplot(gs[0, 0:3]), matrix(p), time, f"All {len(subs)} sleepers combined", big=True)
    ax = fig.add_subplot(gs[0, 3:9]); ax.axis("off")
    M = matrix(p); prob = 100 * M.div(M.sum(1), axis=0)
    lines = [("Falls asleep through N1", f"{M.loc['W','N1']} of {M.loc['W','N1'] + M.loc['W','N2']} departures from wake go to N1"),
             ("Moves one step at a time", f"{100 * sum(M.iloc[i, j] for i in range(4) for j in range(4) if abs(i - j) == 1) / (M.values.sum() - np.trace(M.values)):.0f}% of all stage changes go to a neighbouring stage"),
             ("Deeper is steadier", "chance of staying: " + ", ".join(f"{s} {prob.loc[s, s]:.0f}%" for s in ST)),
             ("N1 is a crossroads", f"from N1: back to wake {prob.loc['N1','W']:.1f}%, on to N2 {prob.loc['N1','N2']:.1f}%"),
             ("Wakes from N2 via N1", f"N2 to N1 {M.loc['N2','N1']} times, N2 to wake {M.loc['N2','W']} times")]
    ax.text(0, 0.97, "What all 14 have in common", fontsize=13, fontweight="bold", color=INK, va="top")
    for i, (h, d) in enumerate(lines):
        y = 0.82 - i * 0.165
        ax.text(0, y, f"{i + 1}", fontsize=13, fontweight="bold", color=COL[ST[min(i, 3)]], va="top")
        ax.text(0.04, y, h, fontsize=12, fontweight="bold", color=INK, va="top")
        ax.text(0.04, y - 0.06, d, fontsize=10.5, color=INK2, va="top")

    rows = []
    for k, sub in enumerate(subs):
        ps, ts = counts([sub])
        Ms = matrix(ps)
        mins = sum(ts.values()) / 2
        grid(fig.add_subplot(gs[1 + k // 7, k % 7 + 1]), Ms, f"P{sub} · {mins:.0f} min")   # 7 per row
        rows.append({"participant": sub, **patterns(Ms)})

    R = pd.DataFrame(rows).set_index("participant")
    ax = fig.add_subplot(gs[3, 1:8])
    vals = R.map(lambda v: np.nan if v is None else float(v)).T.to_numpy(dtype=float)
    ax.imshow(np.where(np.isnan(vals), 0.5, vals), cmap=matplotlib.colors.ListedColormap(["#f3d9cf", "#eeeeea", "#d5ecd9"]),
              vmin=0, vmax=1, aspect="auto")
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            v = vals[i, j]
            ax.text(j, i, "–" if np.isnan(v) else ("✓" if v else "✗"), ha="center", va="center", fontsize=12,
                    color="#1f7a35" if v == 1 else "#b13b1f" if v == 0 else INK2, fontweight="bold")
    ax.set_xticks(range(len(subs)), [f"P{s}" for s in subs], fontsize=9, color=INK2)
    ax.set_yticks(range(len(R.columns)), [f"{c}  ({int(np.nansum(vals[i]))}/{int(np.sum(~np.isnan(vals[i])))})" for i, c in enumerate(R.columns)],
                  fontsize=9.5, color=INK)
    ax.tick_params(length=0); [sp.set_visible(False) for sp in ax.spines.values()]
    ax.set_title("Does each person follow the group pattern?  ✓ yes  ✗ no  – not testable", fontsize=11, fontweight="bold",
                 color=INK, loc="left")
    out = STUDY / "results" / "transitions_sleepers.png"
    fig.savefig(out, dpi=120, facecolor=SURFACE, bbox_inches="tight")
    R.to_csv(out.with_suffix(".csv"))
    print(R.to_string()); print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:] or SLEEPERS)
