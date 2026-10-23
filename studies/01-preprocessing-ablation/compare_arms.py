"""Compare sleep-staging performance across preprocessing arms (raw / filtered / cleaned x 2 detectors).

Identical for every arm: epochs and people (after quality exclusions), features, temporal
context, models and leave-one-person-out testing. Only the EEG the features came from differs.

Pre-set analysis plan (fixed 22 Oct 2026, before results):
  tasks   3-class (wake / N1 / N2) and wake vs N2
  models  logistic regression (standardised features) and gradient-boosted trees
  test    leave-one-person-out; per-person Cohen's kappa (Cohen, 1960); paired Wilcoxon signed-rank
          tests (Wilcoxon, 1945) between arms + bootstrap 95% CI (Efron, 1979) of the mean
          difference; stratified-chance baseline. Models from scikit-learn (Pedregosa et al., 2011);
          gradient boosting (Friedman, 2001). Full citations: REFERENCES.md
  quality exclusions (judged on the standard-cleaned recording, applied identically to all arms):
          epochs the dataset's expert marked uncertain/unscorable (removed when building);
          epochs flagged by Autoreject; recordings with > 3 PREP bad channels (10%);
          people with > 25% of epochs flagged (common EEG conventions)
  signal preservation: per person, is posterior alpha higher in wake than in N2 (the dataset's
          expert labels)? Reported for every arm.
  per-person feature scaling is OFF in the main analysis (people differ greatly in their mix of
  stages, so scaling around each person's median would remove stage information); --norm runs
  it as a sensitivity analysis.

Usage: python studies/01-preprocessing-ablation/compare_arms.py [--norm] [--no-context] [--save-predictions]
                                                              [--feature-set spectral|events]
Writes results/: per_subject.csv, summary.json, exclusions.csv, kappa_by_arm.png, confusion_matrices.png
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
FEAT = ROOT / "data" / "features"
QC = ROOT / "data" / "qc"
OUT = Path(__file__).resolve().parent / "results"
META = ["subject", "session", "t", "stage", "arm", "qc_epoch_bad"]
ARMS = ["raw", "filtered", "cleaned_mne", "cleaned_refined"]
PAIRS = [("raw", "cleaned_mne"), ("raw", "cleaned_refined"), ("filtered", "cleaned_mne"),
         ("cleaned_mne", "cleaned_refined"), ("raw", "filtered")]
# exploratory "fully cleaned" arms (pre-registration amendment 1); only the one in results/reference_choice.json is evaluated
FEAT_FULL = ROOT / "data" / "features_full"
FEAT_EVENTS = ROOT / "data" / "features_events"          # amendment 6: spectral + sleep-event feature set
EXPLORATORY = ["full_mastoid", "full_average"]
EXPLORATORY_PAIRS = [("cleaned_mne", "full_mastoid"), ("cleaned_mne", "full_average"),
                     ("raw", "full_mastoid"), ("raw", "full_average")]
TASKS = {"3class": ["W", "N1", "N2"], "w_vs_n2": ["W", "N2"]}
MODELS = ["logreg", "gbm"]
MAX_BAD_CHANNELS, MAX_BAD_EPOCH_PCT = 3, 25.0
SEED = 0


def make_model(name):
    if name == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=3000))
    if name == "gbm":
        return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, class_weight="balanced",
                                              random_state=SEED)
    return DummyClassifier(strategy="stratified", random_state=SEED)


def load(events=False):
    d = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(FEAT.glob("sub-*.csv"))
                   if f.stat().st_size > 10], ignore_index=True)
    full = [pd.read_csv(f, dtype={"subject": str}) for f in sorted(FEAT_FULL.glob("sub-*.csv"))] if FEAT_FULL.exists() else []
    if full:   # exploratory arms; same epochs, labels and quality flags as the main arms
        full = pd.concat(full, ignore_index=True)
        d = pd.concat([d, full[full.subject.isin(d.subject.unique())]], ignore_index=True)
    if events:  # registered arms only, epochs that have event features
        ev = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(FEAT_EVENTS.glob("sub-*.csv"))])
        d = d[d.arm.isin(ARMS)].merge(ev.drop(columns=["stage", "qc_epoch_bad", "derivations"], errors="ignore"),
                                      on=["subject", "session", "t", "arm"], how="inner")
    q = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted(QC.glob("sub-*.csv"))], ignore_index=True)
    excl = []
    bad_rec = q[q.n_bad_channels.fillna(0) > MAX_BAD_CHANNELS][["subject", "session"]]
    for _, r in bad_rec.iterrows():
        excl.append({"subject": r.subject, "session": r.session, "reason": f"> {MAX_BAD_CHANNELS} bad channels (rule 4)"})
    key = d.subject + "|" + d.session
    d = d[~key.isin(bad_rec.subject + "|" + bad_rec.session)]
    clean = d[d.arm == "cleaned_mne"]
    pct = clean.groupby("subject").qc_epoch_bad.mean() * 100
    bad_people = pct[pct > MAX_BAD_EPOCH_PCT].index
    for s in bad_people:
        excl.append({"subject": s, "session": "all", "reason": f"{pct[s]:.0f}% epochs flagged > {MAX_BAD_EPOCH_PCT:.0f}% (rule 5)"})
    d = d[~d.subject.isin(bad_people)]
    n_flag = int(d[d.arm == "cleaned_mne"].qc_epoch_bad.sum())
    d = d[~d.qc_epoch_bad.astype(bool)]
    excl.append({"subject": "all", "session": "all", "reason": f"{n_flag} individual epochs flagged by Autoreject"})
    return d.sort_values(["arm", "subject", "session", "t"]).reset_index(drop=True), pd.DataFrame(excl)


def prepare(d, feats, norm, context):
    x = d[feats].astype(float)
    if norm:
        g = x.groupby(d.subject)
        iqr = g.transform(lambda s: s.quantile(.75) - s.quantile(.25)).replace(0, 1)
        x = (x - g.transform("median")) / iqr
    if context:  # scorers look at neighbouring epochs; give the model the +-2-epoch average too
        ctx = x.groupby([d.subject, d.session]).transform(lambda s: s.rolling(5, center=True, min_periods=1).mean())
        x = pd.concat([x, ctx.add_suffix("_ctx")], axis=1)
    return x.fillna(0).to_numpy()


def evaluate(d, feats, classes, model, norm, context, keep=None):
    d = d[d.stage.isin(classes)].reset_index(drop=True)
    X, y, subj = prepare(d, feats, norm, context), d.stage.to_numpy(), d.subject.to_numpy()
    pred = np.empty_like(y)
    for s in np.unique(subj):
        tr, te = subj != s, subj == s
        if len(set(y[tr])) < len(classes):
            pred[te] = pd.Series(y[tr]).mode()[0]; continue
        m = make_model(model); m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    if keep is not None:                                        # per-epoch predictions (--save-predictions)
        keep.append(d[["subject", "session", "t", "stage"]].assign(pred=pred))
    rows = []
    for s in np.unique(subj):
        k = subj == s
        rows.append({"subject": s, "n_epochs": int(k.sum()),
                     "kappa": cohen_kappa_score(y[k], pred[k]) if len(set(y[k])) > 1 else np.nan,
                     "bal_acc": balanced_accuracy_score(y[k], pred[k]) if len(set(y[k])) > 1 else np.nan,
                     "macro_f1": f1_score(y[k], pred[k], average="macro", labels=classes, zero_division=0)})
    pooled = {"kappa": float(cohen_kappa_score(y, pred)), "bal_acc": float(balanced_accuracy_score(y, pred)),
              "macro_f1": float(f1_score(y, pred, average="macro", labels=classes, zero_division=0))}
    return pd.DataFrame(rows), pooled, confusion_matrix(y, pred, labels=classes)


def paired(a, b, n_boot=10000):
    m = a.notna() & b.notna()
    diff = (b[m] - a[m]).to_numpy()
    if len(diff) == 0:
        return {"n_people": 0}
    boots = np.random.default_rng(SEED).choice(diff, (n_boot, len(diff))).mean(1)
    stat = wilcoxon(b[m], a[m]) if len(diff) >= 6 and np.any(diff != 0) else None
    return {"n_people": int(m.sum()), "mean_diff": float(diff.mean()), "median_diff": float(np.median(diff)),
            "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "wilcoxon_p": float(stat.pvalue) if stat else None,
            "people_improved": int((diff > 0).sum()), "people_worse": int((diff < 0).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--norm", action="store_true", help="per-person feature scaling (sensitivity analysis)")
    ap.add_argument("--no-context", action="store_true")
    ap.add_argument("--save-predictions", action="store_true",
                    help="also write results/predictions.csv (input to the amendment-5 heart-rate check)")
    ap.add_argument("--feature-set", choices=["spectral", "events"], default="spectral",
                    help="events = spectral + sleep-event features (amendment 6); writes to results/events/")
    ap.add_argument("--subjects", nargs="*", help="restrict to these participants (post-hoc subsets, amendment 8)")
    ap.add_argument("--out", help="results sub-folder for a subset run, e.g. posthoc_sleepers")
    args = ap.parse_args()
    d, excl = load(events=args.feature_set == "events")
    out = OUT / "events" if args.feature_set == "events" else OUT
    if args.subjects:                                            # same exclusions first, then the subset
        d = d[d.subject.isin([s.zfill(2) for s in args.subjects])]
        if not args.out:
            ap.error("--subjects needs --out so subset results never overwrite the main results")
    if args.out:
        out = out / args.out
    feats = [c for c in d.columns if c not in META]
    out.mkdir(parents=True, exist_ok=True)
    excl.to_csv(out / "exclusions.csv", index=False)
    per, pooled, cms, tests, preds = [], {}, {}, {}, []
    # only the reference chosen by the amendment-1 rule is evaluated, and none before the rule is applied
    choice_file = OUT / "reference_choice.json"
    chosen = json.loads(choice_file.read_text())["choice"] if choice_file.exists() else None
    exploratory = [chosen] if chosen in set(d.arm) else []
    d = d[~d.arm.isin([x for x in EXPLORATORY if x != chosen])]
    for task, classes in TASKS.items():
        for model in MODELS + ["chance"]:
            for arm in (ARMS + exploratory if model != "chance" else ["cleaned_mne"]):
                keep = [] if args.save_predictions else None
                r, p, cm = evaluate(d[d.arm == arm], feats, classes, model, args.norm, not args.no_context, keep)
                if keep:
                    preds.append(keep[0].assign(arm=arm if model != "chance" else "chance", model=model, task=task))
                r["arm"], r["model"], r["task"] = (arm if model != "chance" else "chance"), model, task
                per.append(r); pooled[f"{task}/{model}/{arm}"] = p; cms[(task, model, arm)] = cm
                print(f"{task:8s} {model:7s} {arm:9s} pooled kappa {p['kappa']:.3f}  bal.acc {p['bal_acc']:.3f}  "
                      f"| median per-person kappa {r.kappa.median():.3f}", flush=True)
            if model == "chance":
                continue
            sub = pd.concat(per)
            wide = sub[(sub.task == task) & (sub.model == model)].pivot(index="subject", columns="arm", values="kappa")
            for a, b in PAIRS:
                tests[f"{task}/{model}/{b}_vs_{a}"] = paired(wide[a], wide[b])
            for a, b in EXPLORATORY_PAIRS:
                if a in wide and b in wide:
                    tests[f"exploratory/{task}/{model}/{b}_vs_{a}"] = paired(wide[a], wide[b])
    per = pd.concat(per, ignore_index=True)
    per.to_csv(out / "per_subject.csv", index=False)
    if preds:
        pd.concat(preds, ignore_index=True).to_csv(out / "predictions.csv", index=False)
    clean = d[d.arm == "cleaned_mne"]
    preservation = {}
    for arm in ARMS + exploratory:
        a = d[(d.arm == arm) & d.stage.isin(["W", "N2"])]
        m = a.pivot_table(index="subject", columns="stage", values="posterior_rel_alpha").dropna()
        preservation[arm] = {"people_with_wake_and_n2": int(len(m)),
                             "people_alpha_wake_gt_n2": int((m.W > m.N2).sum()),
                             "median_wake_minus_n2": float((m.W - m.N2).median()) if len(m) else None}
        print(f"alpha wake > N2  {arm:16s} {preservation[arm]['people_alpha_wake_gt_n2']} of {len(m)} people", flush=True)
    summary = {"n_people": int(clean.subject.nunique()), "n_epochs_per_arm": int(len(clean)),
               "class_counts": clean.stage.value_counts().to_dict(),
               "settings": {"per_person_norm": args.norm, "context_pm2": not args.no_context,
                            "models": MODELS, "tasks": TASKS, "cv": "leave-one-person-out",
                            "exclusions": "rules 3-4 + Autoreject epoch flags, identical for all arms"},
               "signal_preservation_alpha": preservation,
               "pooled": pooled, "tests_on_per_person_kappa": tests}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, task in zip(axes, TASKS):
        w = per[(per.task == task) & (per.model == "logreg")].pivot(index="subject", columns="arm", values="kappa")
        xs = np.arange(len(ARMS))
        for _, row in w[ARMS].dropna().iterrows():
            ax.plot(xs, row.values, color="#9a9cab", lw=.8, alpha=.6)
        ax.plot(xs, w[ARMS].median().values, color="#33318a", lw=3, marker="o", label="median person")
        ch = per[(per.task == task) & (per.model == "chance")].kappa.median()
        ax.axhline(ch, color="#b53b6d", ls="--", lw=1, label="chance (median)")
        ax.set_xticks(xs, ["raw", "filtered\nonly", "cleaned\n(MNE)", "cleaned\n(refined)"]); ax.set_ylabel("Cohen's kappa vs expert")
        ax.set_title(f"{'Wake / N1 / N2' if task == '3class' else 'Wake vs N2'} (logistic regression)", loc="left")
        ax.grid(alpha=.25, axis="y"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(out / "kappa_by_arm.png", dpi=150); plt.close(fig)

    classes = TASKS["3class"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    for ax, arm in zip(axes, ARMS):
        cm = cms[("3class", "logreg", arm)]; cmn = cm / cm.sum(1, keepdims=True)
        ax.imshow(cmn, cmap="Purples", vmin=0, vmax=1)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cmn[i, j]:.0%}\n({cm[i, j]})", ha="center", va="center", fontsize=8,
                        color="white" if cmn[i, j] > .5 else "black")
        ax.set_xticks(range(3), classes); ax.set_yticks(range(3), classes)
        ax.set_xlabel("predicted"); ax.set_ylabel("expert")
        ax.set_title(f"{arm}: kappa {pooled[f'3class/logreg/{arm}']['kappa']:.2f}")
    fig.tight_layout(); fig.savefig(out / "confusion_matrices.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
