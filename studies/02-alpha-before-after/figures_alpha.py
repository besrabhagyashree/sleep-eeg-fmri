"""Study 02 figure: design, inclusion, mean spectra, per-participant alpha frequency and power, wake share.

Usage: python studies/02-alpha-before-after/figures_alpha.py
Writes results/alpha_overview.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(HERE))
from methods.alpha import concat_segments, spectrum  # noqa: E402
from run_alpha import EXCLUDED, MIN_EPOCHS, POSTERIOR, RUNS  # noqa: E402

DATA = ROOT / "data"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COL = {"before": "#2a78d6", "after": "#eb6834"}             # validated categorical pair
UP, DOWN, SAME = "#1f7a35", "#b13b1f", "#8a8d99"             # direction of change (with a legend)
OUT = HERE / "results"


def group_spectra(d):
    """Mean posterior wake spectrum per run for participants with enough wake in both runs."""
    ok = d.pivot(index="subject", columns="run", values="n_wake_epochs").min(axis=1) >= MIN_EPOCHS
    specs = {"before": [], "after": []}
    for sub in ok[ok].index:
        feats = pd.read_csv(DATA / "features" / f"sub-{sub}.csv", dtype={"subject": str})
        kept = feats[(feats.arm == "cleaned_mne") & (feats.stage == "W") & ~feats.qc_epoch_bad.astype(bool)]
        for session, when in RUNS.items():
            raw = mne.io.read_raw_fif(DATA / "clean" / f"sub-{sub}_{session}_clean-mne_raw.fif", preload=True, verbose="error")
            names = [c for c in POSTERIOR if c in raw.ch_names]
            x = concat_segments(raw.get_data(picks=names), raw.info["sfreq"], kept[kept.session == session].t)
            f, p = spectrum(x, raw.info["sfreq"])
            specs[when].append(np.log10(p))
    return f, {k: np.array(v) for k, v in specs.items()}


def box(ax, x, y, w, h, title, sub, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=SURFACE, ec=col, lw=2.2))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h * 0.3, sub, ha="center", va="center", fontsize=9, color=INK2)


def design(ax):
    ax.set_xlim(0, 10); ax.set_ylim(0, 2.2); ax.axis("off")
    ax.set_title("A · Design: one scanner session per participant", loc="left", fontsize=12, fontweight="bold", color=INK)
    box(ax, 0.1, 0.6, 2.6, 1.1, "Rest run 1 · before", "10 min · eyes not documented", COL["before"])
    box(ax, 3.7, 0.6, 2.6, 1.1, "Visual-motor task", "adaptation (Albouy et al., 2012)", INK2)
    box(ax, 7.3, 0.6, 2.6, 1.1, "Rest run 2 · after", "10 min, then sleep runs", COL["after"])
    for a, b in ((2.75, 3.65), (6.35, 7.25)):
        ax.add_patch(FancyArrowPatch((a, 1.15), (b, 1.15), arrowstyle="-|>", mutation_scale=16, lw=2, color=INK2))
    ax.text(5, 0.18, "Used: expert-scored wake epochs not rejected by Autoreject, posterior electrodes (O1, O2, Oz, P3, P4, Pz, P7, P8). "
            "No control condition.", ha="center", fontsize=9.5, color=INK2)


def inclusion(ax, d):
    w = d.pivot(index="subject", columns="run", values="n_wake_epochs")
    both = int((w.min(axis=1) >= MIN_EPOCHS).sum())
    paf = int(d.pivot(index="subject", columns="run", values="paf").dropna().shape[0])
    stages = [("Analysed in study 01", 29), ("≥ 3 min awake in both rest runs", both), ("Alpha peak found in both runs", paf)]
    ax.set_title("B · Who could be included", loc="left", fontsize=12, fontweight="bold", color=INK)
    y = np.arange(len(stages))[::-1]
    ax.barh(y, [n for _, n in stages], color=[GRID, "#9ec5f4", COL["before"]], height=0.6)
    for yi, (lab, n) in zip(y, stages):
        ax.text(n + 0.5, yi, f"{n}", va="center", fontsize=11, fontweight="bold", color=INK)
    ax.set_xlim(0, 33); ax.set_yticks(y, [lab for lab, _ in stages], fontsize=9)
    ax.set_xlabel("participants (many dozed off during rest)", fontsize=9, color=INK2)


def spectra(ax, f, s):
    keep = (f >= 2) & (f <= 30)
    ax.axvspan(8, 12, color=GRID, alpha=0.6, lw=0)
    ax.text(10, ax.get_ylim()[1] if False else 0, "", fontsize=1)
    for when in ("before", "after"):
        m, se = s[when].mean(0), s[when].std(0, ddof=1) / np.sqrt(len(s[when]))
        ax.plot(f[keep], m[keep], color=COL[when], lw=2.2, label=f"{when} (n = {len(s[when])})")
        ax.fill_between(f[keep], (m - se)[keep], (m + se)[keep], color=COL[when], alpha=0.18, lw=0)
    ax.text(10, ax.get_ylim()[1] - 0.05, "alpha\n8–12 Hz", ha="center", va="top", fontsize=8.5, color=INK2)
    ax.set_xlabel("frequency (Hz)", fontsize=9, color=INK2); ax.set_ylabel("log10 power (µV²/Hz)", fontsize=9, color=INK2)
    ax.set_title("C · Mean wake spectrum, posterior (± SE)", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.annotate("narrow peaks: residual scanner artefact\n(identical in both runs; known limitation)", xy=(24, 0.65),
                xytext=(17.5, 1.45), fontsize=8.5, color=INK2, arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})
    ax.legend(frameon=False, fontsize=9); ax.grid(color=GRID); ax.set_axisbelow(True)


def slopes(ax, d, col, title, ylabel, fmt, note):
    w = d.pivot(index="subject", columns="run", values=col)[["before", "after"]].astype(float).dropna()
    for sub, r in w.iterrows():
        up = r.after > r.before
        ax.plot([0, 1], [r.before, r.after], color=UP if up else (DOWN if r.after < r.before else SAME),
                lw=1.4, alpha=0.8, marker="o", ms=4)
        ax.text(1.04, r.after, sub, fontsize=7, color=INK2, va="center")
    ax.plot([0, 1], [w.before.median(), w.after.median()], color=INK, lw=3.2, marker="o", ms=7)
    ax.set_xticks([0, 1], ["before\n(rest run 1)", "after\n(rest run 2)"], fontsize=9)
    ax.set_xlim(-0.15, 1.2); ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    up, down = int((w.after > w.before).sum()), int((w.after < w.before).sum())
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.text(0.5, 0.02, f"{up} higher · {down} lower · {len(w) - up - down} unchanged   {note}", transform=ax.transAxes,
            ha="center", fontsize=9, color=INK)
    for c, lab in ((UP, "higher"), (DOWN, "lower"), (SAME, "unchanged"), (INK, "median")):
        ax.plot([], [], color=c, lw=2.5 if c == INK else 1.6, label=lab)
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def wake_share(ax, d):
    w = d.pivot(index="subject", columns="run", values="wake_share")[["before", "after"]]
    x = np.arange(len(w))
    order = w.mean(axis=1).sort_values().index
    w = w.loc[order]
    ax.bar(x - 0.2, w.before, 0.4, color=COL["before"], label="before")
    ax.bar(x + 0.2, w.after, 0.4, color=COL["after"], label="after")
    ax.set_xticks(x, w.index, fontsize=7.5); ax.set_ylim(0, 1.05)
    ax.set_ylabel("share of rest run scored wake", fontsize=9, color=INK2)
    ax.set_title("F · How awake each participant stayed during rest (all 29)", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper left"); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def main():
    import json
    d = pd.read_csv(OUT / "alpha_per_participant.csv", dtype={"subject": str})
    d = d[~d.subject.isin(EXCLUDED)]
    s = json.loads((OUT / "summary.json").read_text())["all"]
    f, spec = group_spectra(d)
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                         "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig = plt.figure(figsize=(16, 19))
    gs = fig.add_gridspec(4, 3, height_ratios=[0.38, 1, 1.15, 0.8], hspace=0.36, wspace=0.45, top=0.945, bottom=0.04)
    fig.suptitle("Study 02 · Alpha rhythm before and after a visual-motor task", x=0.06, ha="left", y=0.99, fontsize=19,
                 fontweight="bold", color=INK)
    fig.text(0.06, 0.966, "Peak alpha frequency did not change (primary, inconclusive); alpha power was higher after the task "
             "(exploratory). No control condition, so the cause cannot be attributed to the task.", fontsize=10.5, color=INK2)
    design(fig.add_subplot(gs[0, :]))
    inclusion(fig.add_subplot(gs[1, 0]), d)
    spectra(fig.add_subplot(gs[1, 1:]), f, spec)
    p, pw = s["paf"], s["alpha_log_power"]
    slopes(fig.add_subplot(gs[2, 0]), d, "paf", "D · Peak alpha frequency (primary)", "Hz",
           None, f"p = {p['wilcoxon_p']:.2f}")
    slopes(fig.add_subplot(gs[2, 1]), d, "alpha_log_power", "E · Alpha power, 8–12 Hz", "log10 µV²", None,
           f"p = {pw['wilcoxon_p']:.4f}")
    slopes(fig.add_subplot(gs[2, 2]), d, "fooof_power", "E2 · Alpha peak above 1/f (FOOOF)", "aperiodic-adjusted power",
           None, f"p = {s['fooof_power']['wilcoxon_p']:.3f}")
    wake_share(fig.add_subplot(gs[3, :]), d)
    out = OUT / "alpha_overview.png"
    fig.savefig(out, dpi=115, facecolor=SURFACE, bbox_inches="tight")
    print("saved", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
