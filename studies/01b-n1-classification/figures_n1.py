"""Study 01b figure: stage boundaries, ROC curves, per-participant AUC, N1 F1 by method, per-participant change.

The pairwise (two-class) analysis is exploratory and was not pre-registered: logistic regression,
leave-one-participant-out, for W vs N1, N1 vs N2 and W vs N2, with baseline, A and A+B features.

Usage: python studies/01b-n1-classification/figures_n1.py
Writes results/n1_overview.png and results/pairwise_auc.csv
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch
from sklearn.metrics import roc_auc_score, roc_curve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "studies" / "01-preprocessing-ablation")); sys.path.insert(0, str(ROOT / "src"))
import run_n1 as r  # noqa: E402
from compare_arms import make_model, prepare  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
STAGE = {"W": "#d2622c", "N1": "#2f8cc4", "N2": "#5a4ad0"}
METHOD = {"baseline": "#8a8d99", "A": "#1baf7a", "A+B": "#6250d6"}
PAIRS = [("W", "N1"), ("N1", "N2"), ("W", "N2")]
OUT = HERE / "results"


def pairwise(d, spectral):
    feats = {"baseline": spectral, "A": spectral + r.A_FEATS, "A+B": spectral + r.A_FEATS + r.B_FEATS}
    rows, curves = [], {}
    for a, b in PAIRS:
        sub = d[d.stage.isin((a, b))].reset_index(drop=True)
        y, s = (sub.stage == b).to_numpy(int), sub.subject.to_numpy()
        for name, f in feats.items():
            X, prob = prepare(sub, f, norm=False, context=True), np.full(len(sub), np.nan)
            for p in np.unique(s):
                tr, te = s != p, s == p
                if len(set(y[tr])) == 2:
                    prob[te] = make_model("logreg").fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
            ok = ~np.isnan(prob)
            curves[(a, b, name)] = (roc_curve(y[ok], prob[ok]), roc_auc_score(y[ok], prob[ok]))
            for p in np.unique(s):
                k = (s == p) & ok
                if len(set(y[k])) == 2 and np.bincount(y[k]).min() >= 5:
                    rows.append({"pair": f"{a} vs {b}", "method": name, "subject": p, "auc": roc_auc_score(y[k], prob[k])})
    return pd.DataFrame(rows), curves


def boundary_diagram(ax, curves):
    ax.set_xlim(-0.9, 6.9); ax.set_ylim(-1.75, 2.35); ax.axis("off")
    ax.set_title("A · How well each pair of stages can be told apart (pooled AUC)", loc="left", fontsize=12, fontweight="bold", color=INK)
    pos = {"W": 0, "N1": 3, "N2": 6}
    sub = {"W": "awake", "N1": "drowsy", "N2": "asleep"}
    for st, x in pos.items():                                  # markers stay round whatever the panel's aspect
        ax.scatter([x], [0], s=5200, color=STAGE[st], edgecolors=SURFACE, linewidths=2, zorder=3)
        ax.text(x, 0.12, st, ha="center", va="center", color="white", fontsize=16, fontweight="bold", zorder=4)
        ax.text(x, -0.28, sub[st], ha="center", va="center", color="white", fontsize=9, zorder=4)
    for (a, b), rad in ((("W", "N1"), 0), (("N1", "N2"), 0), (("W", "N2"), -0.22)):
        xa, xb = pos[a], pos[b]
        arr = FancyArrowPatch((xa + 0.55, 0), (xb - 0.55, 0), arrowstyle="<->", mutation_scale=16, lw=2.2,
                              color=INK2, connectionstyle=f"arc3,rad={rad}", zorder=2)
        ax.add_patch(arr)
        base = curves[(a, b, "baseline")][1]
        bm = "A" if curves[(a, b, "A")][1] >= curves[(a, b, "A+B")][1] else "A+B"
        best = curves[(a, b, bm)][1]
        ym = -0.78 if rad == 0 else 1.95
        ax.text((xa + xb) / 2, ym, f"{base:.2f} → {best:.2f}", ha="center", fontsize=13, fontweight="bold", color=INK)
        ax.text((xa + xb) / 2, ym - 0.33, f"baseline → {bm}", ha="center", fontsize=9, color=INK2)
    ax.text(3, -1.7, "N1 sits between wake and N2 and shares features with both: its two boundaries are the hardest.",
            ha="center", fontsize=10, color=INK2)


def roc_panel(ax, curves, a, b):
    for name, col in METHOD.items():
        (fpr, tpr, _), auc = curves[(a, b, name)]
        ax.plot(fpr, tpr, color=col, lw=2, label=f"{name}  AUC {auc:.2f}")
    ax.plot([0, 1], [0, 1], ls="--", color=GRID, lw=1.2, label="chance  0.50")
    ax.set_title(f"{a} vs {b}", fontsize=11, fontweight="bold", color=INK, loc="left")
    ax.set_xlabel(f"{a} epochs wrongly called {b}", fontsize=8.5, color=INK2)
    ax.set_ylabel(f"{b} epochs correctly found", fontsize=8.5, color=INK2)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.set_aspect("equal")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)


def person_auc(ax, pw):
    xs = {p: i for i, p in enumerate(["W vs N1", "N1 vs N2", "W vs N2"])}
    off = {"baseline": -0.22, "A": 0, "A+B": 0.22}
    rng = np.random.default_rng(0)
    for (pair, m), g in pw.groupby(["pair", "method"]):
        x = xs[pair] + off[m]
        ax.scatter(x + rng.uniform(-0.06, 0.06, len(g)), g.auc, s=14, color=METHOD[m], alpha=0.55, lw=0)
        ax.plot([x - 0.08, x + 0.08], [g.auc.median()] * 2, color=METHOD[m], lw=3)
    ax.axhline(0.5, ls="--", color=INK2, lw=1); ax.text(2.45, 0.51, "chance", fontsize=8, color=INK2, ha="right")
    ax.set_xticks(range(3), list(xs), fontsize=9.5)
    ax.set_ylabel("AUC per participant", fontsize=9, color=INK2); ax.set_ylim(0.2, 1.02)
    ax.set_title("C · Every participant (dots) and the median (bar)", loc="left", fontsize=12, fontweight="bold", color=INK)
    for m, c in METHOD.items():
        ax.scatter([], [], color=c, label=m, s=30)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="lower left")
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def n1_methods(ax, summary_pooled):
    order = ["D/yasa", "C/logreg", "baseline/logreg", "A+B+C/logreg", "B/logreg", "A/logreg", "A+B/logreg",
             "baseline/gbm", "C/gbm", "B/gbm", "A+B+C/gbm", "A/gbm", "A+B/gbm"]
    label = {"D/yasa": "D · YASA pre-trained"}
    vals = [summary_pooled[m][1] for m in order]
    y = np.arange(len(order))
    cols = [METHOD["baseline"] if m.startswith("baseline") else "#d03b3b" if m in ("D/yasa", "C/logreg") else
            METHOD["A+B"] if m.startswith("A+B/") else METHOD["A"] if m.startswith("A/") else "#b9bccb" for m in order]
    ax.barh(y, vals, color=cols, height=0.65)
    for yi, v in zip(y, vals):
        ax.text(v + 0.01, yi, f"{v:.2f}", va="center", fontsize=8.5, color=INK)
    names = [label.get(m, m.replace("/gbm", " · gradient boosting").replace("/logreg", " · logistic reg.")) for m in order]
    ax.set_yticks(y, names, fontsize=8.5); ax.set_xlim(0, 0.68)
    ax.set_xlabel("N1 F1 (pooled; 1 = perfect)", fontsize=9, color=INK2)
    ax.set_title("D · N1 performance, all 13 variants", loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.axhline(6.5, color=GRID, lw=1)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)


def change_panel(ax, per):
    el = per[per.eligible].pivot(index="subject", columns="method", values="f1_N1")
    for i, (m, title) in enumerate((("A/gbm", "A"), ("B/gbm", "B"), ("C/gbm", "C"))):
        diff = (el[m] - el["baseline/gbm"]).sort_values()
        x = np.arange(len(diff)) + i * (len(diff) + 4)
        ax.bar(x, diff, color=["#1f7a35" if v > 0 else "#b13b1f" for v in diff], width=0.8)
        ax.text(x.mean(), 0.33, f"{title}: {(diff > 0).sum()} better · {(diff < 0).sum()} worse\nmean {diff.mean():+.3f}",
                ha="center", fontsize=9, color=INK)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xticks([]); ax.set_ylabel("change in N1 F1 vs baseline", fontsize=9, color=INK2); ax.set_ylim(-0.35, 0.42)
    ax.set_title("E · Per participant, gradient boosting (pre-registered tests: all inconclusive, Holm p = 1.0)",
                 loc="left", fontsize=12, fontweight="bold", color=INK)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def main():
    import json
    d, spectral = r.data()
    pw, curves = pairwise(d, spectral)
    pw.to_csv(OUT / "pairwise_auc.csv", index=False)
    summary = json.loads((OUT / "summary.json").read_text())
    per = pd.read_csv(OUT / "per_participant.csv", dtype={"subject": str})
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                         "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig = plt.figure(figsize=(16, 21))
    gs = fig.add_gridspec(4, 3, height_ratios=[0.55, 1.05, 1.15, 0.9], hspace=0.38, wspace=0.32, top=0.955, bottom=0.04)
    fig.suptitle("Study 01b · Can N1 be told apart from wake and N2?", x=0.06, ha="left", y=1.0, fontsize=19, fontweight="bold", color=INK)
    fig.text(0.06, 0.982, "29 participants, artefact-corrected EEG, leave-one-participant-out. Panels A–C: exploratory two-class "
             "analysis (logistic regression). Panels D–E: pre-registered study 01b.", fontsize=10.5, color=INK2)
    boundary_diagram(fig.add_subplot(gs[0, :]), curves)
    for i, (a, b) in enumerate(PAIRS):
        ax = fig.add_subplot(gs[1, i]); roc_panel(ax, curves, a, b)
        if i == 0:
            ax.set_title(f"B · ROC curves      {a} vs {b}", fontsize=12, fontweight="bold", color=INK, loc="left")
    person_auc(fig.add_subplot(gs[2, 0:2]), pw)
    n1_methods(fig.add_subplot(gs[2, 2]), summary["pooled_f1_W_N1_N2"])
    change_panel(fig.add_subplot(gs[3, :]), per)
    out = OUT / "n1_overview.png"
    fig.savefig(out, dpi=115, facecolor=SURFACE, bbox_inches="tight")
    print("saved", out.relative_to(ROOT))
    print(pw.groupby(["pair", "method"]).auc.agg(["median", "count", lambda v: (v > 0.5).sum()]).round(3).to_string())


if __name__ == "__main__":
    main()
