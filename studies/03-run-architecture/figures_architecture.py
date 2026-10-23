"""Study 03 figures: every participant's hypnogram across the five runs, and the group overview.

Usage: python studies/03-run-architecture/figures_architecture.py [--group qualified|quality|all]
Writes hypnograms.png and run_overview.png in the group's results folder
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_architecture import GROUPS, SHORT  # noqa: E402

OUT = HERE / "results"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
STAGE_COL = {"W": "#f1d9a6", "1": "#8fbce6", "2": "#3a7fc4", "3": "#123f73"}     # wake warm; sleep one hue, light -> deep
STAGE_NAME = {"W": "Wake", "1": "N1", "2": "N2", "3": "N3"}
CLUSTER_COL = {1: "#b13b1f", 2: "#8a5cc2", 3: "#1f7a35", 4: "#eb6834"}
NAMES = {"qualified": {1: "awake in rest 1 and sleep 1", 2: "asleep in most runs"},
         "quality": {1: "awake until sleep 3", 2: "dozed in rest 2 only", 3: "sleep builds across runs", 4: "sleepy throughout"}}
LABEL = {"qualified": "the 14 qualified participants (passed quality, awake < 50%)",
         "quality": "the 27 participants who passed study 01's quality rules and have all five runs",
         "all": "all 31 participants with five runs (quality exclusions ignored)"}
CLUSTER_NAME, GROUP = {}, "qualified"
GAP = 3                                                              # epochs of white space between runs


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                         "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
                         "xtick.color": INK2, "ytick.color": INK2})


def hypnograms(d):
    order = (d.groupby("subject").agg(cluster=("cluster", "first"), sleep=("sleep_share", "mean"))
             .sort_values(["cluster", "sleep"], ascending=[False, False]))
    subs = list(order.index)
    H = 0.42 * len(subs) + 3.2
    fig, ax = plt.subplots(figsize=(16, H))
    starts, x0 = {}, 0
    for r in SHORT:
        starts[r] = x0; x0 += (20 if "rest" in r else 30) + GAP
    for i, sub in enumerate(subs):
        y = len(subs) - 1 - i
        for _, row in d[d.subject == sub].iterrows():
            for j, s in enumerate(row.sequence if isinstance(row.sequence, str) else ""):
                ax.add_patch(Rectangle((starts[row.run] + j, y + 0.08), 0.92, 0.84, color=STAGE_COL[s], lw=0))
            if row.n_uncertain:
                ax.text(starts[row.run] + len(row.sequence if isinstance(row.sequence, str) else "") + 0.3, y + 0.5,
                        f"+{row.n_uncertain}?", fontsize=6.5, color=INK2, va="center")
        c = order.loc[sub, "cluster"]
        ax.text(-1.2, y + 0.5, f"sub-{sub}", ha="right", va="center", fontsize=8.5, color=INK)
        ax.add_patch(Rectangle((-0.9, y + 0.15), 0.5, 0.7, color=CLUSTER_COL.get(c, GRID), lw=0, clip_on=False))
    for r in SHORT:
        ax.text(starts[r] + (10 if "rest" in r else 15), len(subs) + 0.4, r, ha="center", fontsize=11, fontweight="bold",
                color=INK)
        ax.text(starts[r] + (10 if "rest" in r else 15), -0.75, "10 min" if "rest" in r else "15 min", ha="center",
                fontsize=8, color=INK2)
    ax.text(starts["rest 2"] - GAP / 2, len(subs) + 0.4, "task", ha="center", fontsize=8, color=INK2, style="italic")
    ax.set_xlim(-8, x0); ax.set_ylim(-1.2, len(subs) + 2.2); ax.axis("off")
    stage_h = [Patch(color=STAGE_COL[k], label=STAGE_NAME[k]) for k in STAGE_COL]
    clus_h = [Patch(color=CLUSTER_COL[k], label=f"group {k}: {CLUSTER_NAME.get(k, k)}") for k in sorted(d.cluster.dropna().unique().astype(int))]
    fig.legend(handles=stage_h + clus_h, loc="lower center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(f"Study 03 · Every participant across the five runs: {LABEL[GROUP]}", x=0.04, ha="left",
                 fontsize=16, fontweight="bold", color=INK, y=1 - 0.1 / H, va="top")
    fig.text(0.04, 1 - 0.55 / H, "One cell = one 30-s expert-scored epoch. Rows are grouped by the exploratory cluster (colour tab) "
             "and ordered by overall sleep. '+n?' = epochs the expert marked uncertain or unscorable;\n"
             "sub-23 (grey tab) has no scored epochs in rest 1 and sleep 2, so it is shown but not in the tests or clusters.",
             fontsize=9.5, color=INK2, va="top")
    fig.subplots_adjust(top=1 - 1.2 / H, bottom=0.7 / H, left=0.02, right=0.99)
    fig.savefig(OUT / "hypnograms.png", dpi=115, facecolor=SURFACE, bbox_inches="tight")


def composition(ax, d):
    m = d.groupby("run")[[f"{k}_share" for k in ("W", "N1", "N2", "N3")]].mean().loc[SHORT]
    bottom = np.zeros(len(SHORT))
    for k, code in zip(("W", "N1", "N2", "N3"), STAGE_COL):
        v = m[f"{k}_share"].to_numpy()
        ax.bar(range(5), v, 0.62, bottom=bottom, color=STAGE_COL[code], edgecolor=SURFACE, lw=2, label=STAGE_NAME[code])
        for i, (b, h) in enumerate(zip(bottom, v)):
            if h >= 0.08:
                ax.text(i, b + h / 2, f"{h:.0%}", ha="center", va="center", fontsize=8.5,
                        color=SURFACE if code in "23" else INK)
        bottom += v
    ax.set_xticks(range(5), SHORT, fontsize=9); ax.set_ylim(0, 1.0); ax.set_ylabel("mean share of run", fontsize=9, color=INK2)
    ax.set_title("A · Stage make-up of each run (mean)", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.legend(frameon=False, fontsize=8.5, ncol=4, loc="upper left", bbox_to_anchor=(0, 1.13))


def spaghetti(ax, d, col, title, ylabel, fmt, note):
    w = d.pivot(index="subject", columns="run", values=col)[SHORT]
    for _, r in w.iterrows():
        ax.plot(range(5), r.to_numpy(), color=INK2, lw=0.9, alpha=0.28, marker="o", ms=2.5)
    med = w.median()
    ax.plot(range(5), med.to_numpy(), color=INK, lw=3, marker="o", ms=7, label="median")
    for i, v in enumerate(med):
        ax.text(i, v, fmt(v), ha="center", va="bottom", fontsize=8.5, color=INK, fontweight="bold",
                bbox={"fc": SURFACE, "ec": "none", "pad": 1.2}, zorder=5)
    ax.set_xticks(range(5), SHORT, fontsize=9); ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.text(0.5, -0.2, note, transform=ax.transAxes, ha="center", fontsize=8.5, color=INK2)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def cluster_profiles(ax, s):
    for c, prof in s["clusters_exploratory"]["profiles"].items():
        c = int(c); n = s["clusters_exploratory"]["sizes"][str(c)]
        v = [prof[r] for r in SHORT]
        ax.plot(range(5), v, color=CLUSTER_COL[c], lw=2.2, marker="o", ms=8, mec=SURFACE, mew=2)
        ax.text(4.12, v[-1], f"{c}: {CLUSTER_NAME.get(c, c)} (n={n})", fontsize=8.5, color=INK, va="center")
    ax.set_xticks(range(5), SHORT, fontsize=9); ax.set_xlim(-0.2, 6.6); ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel("mean sleep share", fontsize=9, color=INK2)
    k = s["clusters_exploratory"]["k"]; sil = s["clusters_exploratory"]["silhouette"][str(k)]
    ax.set_title("D · Exploratory groups of participants (Ward)", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.text(0.0, -0.2, f"k = {k} by silhouette ({sil:.2f}: weak structure, Rousseeuw 1987); descriptive, not tested",
            transform=ax.transAxes, fontsize=8.5, color=INK2)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def trait(ax, d, s):
    w = d.pivot(index="subject", columns="run", values="sleep_share")[SHORT]
    cl = d.groupby("subject").cluster.first()
    x, y = w[SHORT[:2]].mean(axis=1), w[SHORT[2:]].mean(axis=1)
    for sub in w.index:
        ax.scatter(x[sub], y[sub], s=58, color=CLUSTER_COL.get(cl[sub], GRID), edgecolor=SURFACE, lw=2, zorder=3)
        ax.text(x[sub] + 0.015, y[sub] + 0.012, sub, fontsize=7, color=INK2)
    t = s["trait_rest_vs_sleep"]
    ax.set_xlabel("sleep share in rest runs (mean of 1–2)", fontsize=9, color=INK2)
    ax.set_ylabel("sleep share in sleep runs (mean of 1–3)", fontsize=9, color=INK2)
    ax.set_xlim(-0.04, 1.04); ax.set_ylim(-0.04, 1.04)
    ax.set_title("E · Dozing in rest vs sleep later", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.text(0.97, 0.04, f"Spearman ρ = {t['spearman_rho']:.2f}, p = {t['p']:.3f}", transform=ax.transAxes, fontsize=9.5, ha="right",
            color=INK, va="bottom")
    ax.grid(color=GRID); ax.set_axisbelow(True)


def overview(d, s):
    fig = plt.figure(figsize=(16, 12.5))
    gs = fig.add_gridspec(2, 3, hspace=0.5, wspace=0.32, top=0.86, bottom=0.08, left=0.05, right=0.97)
    h1, h2 = s["H1_friedman_sleep_share"], s["H2_page_trend"]
    fig.suptitle("Study 03 · Sleep across the five runs of a session", x=0.05, ha="left", y=0.985, fontsize=18,
                 fontweight="bold", color=INK)
    fig.text(0.05, 0.93, f"Expert labels; {LABEL[GROUP]}. Tests use {h1['n']} (sub-23 has no scored epochs in two runs).\n"
             f"Sleep share across runs: Friedman p = {h1['p']:.3f} (Kendall's W = {h1['kendall_w']:.2f}); "
             f"trend with run order: Page p = {h2['p']:.3f}.", fontsize=10.5, color=INK2)
    composition(fig.add_subplot(gs[0, 0]), d)
    spaghetti(fig.add_subplot(gs[0, 1]), d, "sleep_share", "B · Share of each run asleep", "sleep share (N1+N2+N3)",
              lambda v: f"{v:.0%}", "thin lines: one participant each · black: median")
    lat = d.assign(sleep_latency_min=d.sleep_latency_s / 60)
    spaghetti(fig.add_subplot(gs[0, 2]), lat, "sleep_latency_min", "C · Time to fall asleep", "minutes to first sleep epoch",
              lambda v: f"{v:.1f}", "no sleep in a run = run length (10 or 15 min)")
    cluster_profiles(fig.add_subplot(gs[1, 0:2]), s)
    trait(fig.add_subplot(gs[1, 2]), d, s)
    fig.savefig(OUT / "run_overview.png", dpi=115, facecolor=SURFACE)


def main():
    import argparse
    global OUT, CLUSTER_NAME, GROUP
    ap = argparse.ArgumentParser(); ap.add_argument("--group", choices=GROUPS, default="qualified")
    GROUP = ap.parse_args().group
    OUT, CLUSTER_NAME = HERE / "results" / GROUPS[GROUP], NAMES.get(GROUP, {})
    style()
    d = pd.read_csv(OUT / "per_run.csv", dtype={"subject": str, "sequence": str})
    s = json.loads((OUT / "summary.json").read_text())
    hypnograms(d); overview(d, s)
    print("saved hypnograms.png, run_overview.png")


if __name__ == "__main__":
    main()
