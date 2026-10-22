"""Compare sleep-staging performance across preprocessing arms (raw / filtered / cleaned).

Identical for every arm: features, per-person feature normalisation, temporal context,
model, and leave-one-person-out testing. Only the EEG the features came from differs.

Per person (test fold) we compute Cohen's kappa against the expert, balanced accuracy and
macro F1. Arms are compared with paired Wilcoxon signed-rank tests on per-person kappa,
plus a bootstrap 95% CI of the mean difference.

Usage: python src/train_eval.py [--no-context] [--no-norm]
Writes results/ per_subject.csv, summary.json, kappa_by_arm.png, confusion_matrices.png
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data" / "features"
OUT = ROOT / "results"
META = ["subject", "session", "t", "stage", "arm"]
CLASSES = ["W", "N1", "N2"]
ARMS = ["raw", "filtered", "cleaned"]
SEED = 0


def load():
    d = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(FEAT.glob("sub-*.csv"))
                   if f.stat().st_size > 10], ignore_index=True)
    return d.sort_values(["arm", "subject", "session", "t"]).reset_index(drop=True)


def prepare(d, feats, norm, context):
    x = d[feats].astype(float)
    if norm:   # robust z-score within each person (uses no labels, so the test person can be normalised too)
        g = x.groupby(d.subject)
        med = g.transform("median")
        iqr = g.transform(lambda s: s.quantile(.75) - s.quantile(.25)).replace(0, 1)
        x = (x - med) / iqr
    if context:  # scorers look at neighbouring epochs; give the model the +-2-epoch average too
        ctx = x.groupby([d.subject, d.session]).transform(lambda s: s.rolling(5, center=True, min_periods=1).mean())
        x = pd.concat([x, ctx.add_suffix("_ctx")], axis=1)
    return x.fillna(0).to_numpy()


def evaluate_arm(d, feats, norm, context, model_name):
    X, y, subj = prepare(d, feats, norm, context), d.stage.to_numpy(), d.subject.to_numpy()
    pred = np.empty_like(y)
    for s in np.unique(subj):
        tr, te = subj != s, subj == s
        if model_name == "chance":
            m = DummyClassifier(strategy="stratified", random_state=SEED)
        else:
            m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, class_weight="balanced",
                                               random_state=SEED)
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    rows = []
    for s in np.unique(subj):
        k = subj == s
        rows.append({"subject": s, "n_epochs": int(k.sum()), "n_classes": len(set(y[k])),
                     "kappa": cohen_kappa_score(y[k], pred[k]) if len(set(y[k])) > 1 else np.nan,
                     "bal_acc": balanced_accuracy_score(y[k], pred[k]),
                     "macro_f1": f1_score(y[k], pred[k], average="macro", labels=CLASSES, zero_division=0)})
    pooled = {"kappa": cohen_kappa_score(y, pred), "bal_acc": balanced_accuracy_score(y, pred),
              "macro_f1": f1_score(y, pred, average="macro", labels=CLASSES, zero_division=0)}
    return pd.DataFrame(rows), pooled, confusion_matrix(y, pred, labels=CLASSES)


def paired(a, b, n_boot=10000):
    m = a.notna() & b.notna()
    diff = (b[m] - a[m]).to_numpy()
    rng = np.random.default_rng(SEED)
    boots = rng.choice(diff, (n_boot, len(diff))).mean(1)
    stat = wilcoxon(b[m], a[m]) if len(diff) >= 6 and np.any(diff != 0) else None
    return {"n_people": int(m.sum()), "mean_diff": float(diff.mean()), "median_diff": float(np.median(diff)),
            "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "wilcoxon_p": float(stat.pvalue) if stat else None,
            "people_improved": int((diff > 0).sum()), "people_worse": int((diff < 0).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-context", action="store_true")
    ap.add_argument("--no-norm", action="store_true")
    args = ap.parse_args()
    d = load()
    feats = [c for c in d.columns if c not in META]
    OUT.mkdir(exist_ok=True)
    per, pooled, cms = [], {}, {}
    for arm in ARMS + ["chance"]:
        src = d[d.arm == ("cleaned" if arm == "chance" else arm)].reset_index(drop=True)
        r, p, cm = evaluate_arm(src, feats, not args.no_norm, not args.no_context,
                                "chance" if arm == "chance" else "gbm")
        r["arm"] = arm
        per.append(r); pooled[arm] = p; cms[arm] = cm
        print(f"{arm:9s} pooled kappa {p['kappa']:.3f}  bal.acc {p['bal_acc']:.3f}  macroF1 {p['macro_f1']:.3f}  "
              f"| median per-person kappa {r.kappa.median():.3f}", flush=True)
    per = pd.concat(per, ignore_index=True)
    per.to_csv(OUT / "per_subject.csv", index=False)
    wide = per.pivot(index="subject", columns="arm", values="kappa")
    tests = {f"{b}_vs_{a}": paired(wide[a], wide[b])
             for a, b in [("raw", "cleaned"), ("filtered", "cleaned"), ("raw", "filtered")]}
    summary = {"n_people": int(d.subject.nunique()), "n_epochs_per_arm": int((d.arm == "cleaned").sum()),
               "class_counts": d[d.arm == "cleaned"].stage.value_counts().to_dict(),
               "settings": {"per_person_norm": not args.no_norm, "context_pm2": not args.no_context,
                            "model": "HistGradientBoosting(300, lr .05, balanced)", "cv": "leave-one-person-out"},
               "pooled": pooled, "tests_on_per_person_kappa": tests}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(tests, indent=2))

    # per-person kappa, paired lines across arms
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = np.arange(len(ARMS))
    for _, row in wide[ARMS].dropna().iterrows():
        ax.plot(xs, row.values, color="#9a9cab", lw=.8, alpha=.6)
    ax.plot(xs, wide[ARMS].median().values, color="#33318a", lw=3, marker="o", label="median person")
    ax.axhline(wide["chance"].median(), color="#b53b6d", ls="--", lw=1, label="chance (median)")
    ax.set_xticks(xs, ["raw", "filtered only", "cleaned"]); ax.set_ylabel("Cohen's kappa vs expert")
    ax.set_title("Sleep-staging agreement per person, by preprocessing", loc="left"); ax.legend(frameon=False)
    ax.grid(alpha=.25, axis="y"); fig.tight_layout(); fig.savefig(OUT / "kappa_by_arm.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, arm in zip(axes, ARMS):
        cm = cms[arm]; cmn = cm / cm.sum(1, keepdims=True)
        ax.imshow(cmn, cmap="Purples", vmin=0, vmax=1)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cmn[i, j]:.0%}\n({cm[i, j]})", ha="center", va="center", fontsize=8,
                        color="white" if cmn[i, j] > .5 else "black")
        ax.set_xticks(range(3), CLASSES); ax.set_yticks(range(3), CLASSES)
        ax.set_xlabel("predicted"); ax.set_ylabel("expert"); ax.set_title(f"{arm}: kappa {pooled[arm]['kappa']:.2f}")
    fig.tight_layout(); fig.savefig(OUT / "confusion_matrices.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
