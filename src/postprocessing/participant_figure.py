"""One-page overview of one participant through every stage: data flow, quality, signal, events, staging.

Reads only saved outputs (data/qc, data/features, data/features_full, data/features_events and the
within-person staging results). Wake is blue, N2 orange throughout; staging uses a blue-grey-red
diverging scale centred on chance (kappa 0).

Usage: python src/postprocessing/participant_figure.py 01
Writes studies/01-preprocessing-ablation/results/participant_sub-XX_overview.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RESULTS = ROOT / "studies" / "01-preprocessing-ablation" / "results"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
WAKE, N2 = "#2a78d6", "#eb6834"                       # categorical slots 1 and 2 (validated pair)
OK, DROP = "#0ca30c", "#d03b3b"                       # status: good / critical
DIVERGING = LinearSegmentedColormap.from_list("kappa", ["#e34948", "#f0efec", "#2a78d6"])
ARMS = ["raw", "filtered", "cleaned_mne", "cleaned_refined"]
ARM_LABEL = {"raw": "raw", "filtered": "filtered\nonly", "cleaned_mne": "cleaned\n(MNE)",
             "cleaned_refined": "cleaned\n(refined)", "obs_mne": "OBS\n(MNE)", "obs_refined": "OBS\n(refined)"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.titlelocation": "left", "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "axes.spines.top": False, "axes.spines.right": False})


def box(ax, x, y, w, h, title, sub, colour):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                                fc=SURFACE, ec=colour, lw=2))
    ax.text(x + w / 2, y + h * 0.68, title, ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center", fontsize=9, color=INK2)


def arrow(ax, x0, x1, y):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=14, color=INK2, lw=1.4))


def flow(ax, q, kept):
    ax.set_xlim(-0.01, 1.01); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("A · Data flow: from recordings to the epochs that are scored")
    n_ep, n_bad = int(q.n_epochs.sum()), int(q.n_bad_epochs.sum())
    counts = kept.stage.value_counts()
    box(ax, 0.00, 0.12, 0.17, 0.76, f"{len(q)} recordings", f"{(q.file_md5_ok == True).sum()}/{len(q)} checksums OK", OK)  # noqa: E712
    box(ax, 0.235, 0.12, 0.17, 0.76, f"{n_ep} epochs", "30 s each, expert-scored", INK2)
    box(ax, 0.47, 0.12, 0.17, 0.76, f"{n_bad} flagged", f"Autoreject ({100 * n_bad / n_ep:.1f}%)", DROP)
    box(ax, 0.705, 0.12, 0.295, 0.76, f"{len(kept)} epochs kept",
        f"wake {counts.get('W', 0)} · N1 {counts.get('N1', 0)} · N2 {counts.get('N2', 0)}", OK)
    for x0, x1 in ((0.17, 0.235), (0.405, 0.47), (0.64, 0.705)):
        arrow(ax, x0 + 0.005, x1 - 0.005, 0.50)


def quality(ax_flag, ax_inps, q):
    runs = q.session.str.replace("task-", "").str.replace("_run-", " ")
    x = np.arange(len(q))
    ax_flag.bar(x, q.n_bad_epochs, color=DROP, width=0.55)
    ax_flag.bar(x, q.n_epochs - q.n_bad_epochs, bottom=q.n_bad_epochs, color=OK, width=0.55, alpha=0.35)
    for i, (b, n) in enumerate(zip(q.n_bad_epochs, q.n_epochs)):
        ax_flag.text(i, n + 0.6, f"{int(b)}/{int(n)}", ha="center", fontsize=8, color=INK2)
    ax_flag.set_xticks(x, runs, fontsize=8); ax_flag.set_ylabel("epochs")
    ax_flag.set_title("B · Epochs flagged per recording")
    ax_flag.legend(["flagged", "kept"], frameon=False, fontsize=8, loc="upper left")
    w = 0.36
    ax_inps.bar(x - w / 2, q.inps_db_mne, w, color="#1baf7a", label="MNE detector")
    ax_inps.bar(x + w / 2, q.inps_db_refined, w, color="#6250d6", label="refined detector")
    for i, (a, b) in enumerate(zip(q.inps_db_mne, q.inps_db_refined)):
        ax_inps.text(i - w / 2, a + 0.03, f"{a:.1f}", ha="center", fontsize=7.5, color=INK2)
        ax_inps.text(i + w / 2, b + 0.03, f"{b:.1f}", ha="center", fontsize=7.5, color=INK2)
    ax_inps.set_xticks(x, runs, fontsize=8); ax_inps.set_ylabel("dB removed (higher = more)")
    ax_inps.set_title("C · Heartbeat artefact removed (INPS)")
    ax_inps.legend(frameon=False, fontsize=8, loc="upper left")


def wake_vs_n2(ax, d, col, title, ylabel):
    m = d[d.stage.isin(["W", "N2"])].groupby(["arm", "stage"])[col].mean().unstack()
    x, w = np.arange(len(ARMS)), 0.36
    ax.bar(x - w / 2, [m.loc[a, "W"] for a in ARMS], w, color=WAKE, label="wake")
    ax.bar(x + w / 2, [m.loc[a, "N2"] for a in ARMS], w, color=N2, label="N2")
    for i, a in enumerate(ARMS):                      # mark empty bars, so "none detected" is visible
        for dx, st in ((-w / 2, "W"), (w / 2, "N2")):
            if m.loc[a, st] == 0:
                ax.text(i + dx, 0, "0", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(x, [ARM_LABEL[a] for a in ARMS], fontsize=8)
    ax.set_title(title); ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8)


def staging(ax, s):
    arms = [a for a in ARMS + ["obs_mne", "obs_refined"] if a in set(s.arm)]
    rows = [("w_vs_n2", "logreg"), ("w_vs_n2", "gbm"), ("3class", "logreg"), ("3class", "gbm")]
    names = {"w_vs_n2": "wake vs N2", "3class": "3 stages", "logreg": "logistic reg.", "gbm": "boosted trees"}
    k = s.pivot_table(index=["task", "model"], columns="arm", values="kappa")
    grid = np.array([[k.loc[r, a] for a in arms] for r in rows])
    ax.imshow(grid, cmap=DIVERGING, vmin=-0.4, vmax=0.4, aspect="auto")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, f"{grid[i, j]:+.2f}", ha="center", va="center", fontsize=9, color=INK)
    ax.set_xticks(range(len(arms)), [ARM_LABEL[a] for a in arms], fontsize=8)
    ax.set_yticks(range(len(rows)), [f"{names[t]}, {names[m]}" for t, m in rows], fontsize=8)
    ax.set_title("I · Staging score (kappa; 0 = chance, 1 = perfect)")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)


def main(sub):
    q = pd.read_csv(DATA / "qc" / f"sub-{sub}.csv")
    q = q[q.status == "ok"].reset_index(drop=True)
    f = pd.read_csv(DATA / "features" / f"sub-{sub}.csv")
    good = f[~f.qc_epoch_bad.astype(bool)]
    ev = pd.read_csv(DATA / "features_events" / f"sub-{sub}.csv")
    ev = ev[~ev.qc_epoch_bad.astype(bool)]
    stage_file = RESULTS / f"obs_staging_sub-{sub}.csv"
    s = pd.read_csv(stage_file if stage_file.exists() else RESULTS / f"preview_sub-{sub}_scores.csv")

    fig = plt.figure(figsize=(15, 17))
    gs = fig.add_gridspec(5, 6, height_ratios=[0.42, 1, 1, 1, 1.05], hspace=0.6, wspace=0.75, top=0.92, bottom=0.07)
    fig.suptitle(f"Participant {sub} through every stage", x=0.06, y=0.975, ha="left", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.06, 0.952, "OpenNeuro ds003768 · sleep EEG recorded inside an MRI scanner · wake = blue, N2 = orange",
             fontsize=10, color=INK2)
    flow(fig.add_subplot(gs[0, :]), q, good[good.arm == "raw"])
    quality(fig.add_subplot(gs[1, :3]), fig.add_subplot(gs[1, 3:]), q)
    wake_vs_n2(fig.add_subplot(gs[2, 0:2]), good, "posterior_rel_alpha", "D · Alpha, back of head", "share of power")
    wake_vs_n2(fig.add_subplot(gs[2, 2:4]), good, "central_rel_sigma", "E · Spindle band, centre", "share of power")
    wake_vs_n2(fig.add_subplot(gs[2, 4:6]), good, "frontal_rel_delta", "F · Slow waves, front", "share of power")
    wake_vs_n2(fig.add_subplot(gs[3, 0:3]), ev, "sw_density", "G · Slow waves detected (YASA)", "per channel per minute")
    wake_vs_n2(fig.add_subplot(gs[3, 3:6]), ev, "sp_density", "H · Spindles detected (YASA)", "per channel per minute")
    staging(fig.add_subplot(gs[4, :]), s)
    fig.text(0.06, 0.035, "Raw and filtered recordings are dominated by scanner noise, so every brain band looks small there. "
             "Staging uses leave-one-recording-out within this person.", fontsize=9, color=INK2)
    out = RESULTS / f"participant_sub-{sub}_overview.png"
    fig.savefig(out, dpi=130, facecolor=SURFACE)
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "01")
