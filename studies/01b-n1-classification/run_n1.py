"""Study 01b analysis: does N1 classification improve with methods A, B, C? D is a benchmark.

Implements PREREGISTRATION.md: AAS-MNE arm of study 01 with its epochs and exclusions; baseline = study 01
spectral classifier; A = + alpha occupancy; B = + eye-movement features; C = baseline + HMM (Viterbi)
decoding; D = YASA pre-trained stager. Leave-one-participant-out. Primary outcome: per-participant N1 F1
(participants with >= 5 N1 and >= 5 non-N1 epochs); primary tests A, B, C vs baseline (gradient boosting),
Wilcoxon signed-rank with Holm correction.

Usage: python studies/01b-n1-classification/run_n1.py
Writes results/per_participant.csv and results/summary.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY01 = ROOT / "studies" / "01-preprocessing-ablation"
sys.path.insert(0, str(STUDY01))
sys.path.insert(0, str(ROOT / "src"))
from compare_arms import META, load, make_model, paired, prepare  # noqa: E402
from methods.hmm import transitions, viterbi  # noqa: E402

CLASSES = ["W", "N1", "N2"]
A_FEATS = ["alpha_occupancy", "alpha_theta_log"]
B_FEATS = ["eog_slow_log", "eog_fast_log", "eog_slow_fast_log", "eog_slow_ptp90"]
MIN_N1 = 5
OUT = HERE / "results"


def data():
    d, _ = load()
    d = d[(d.arm == "cleaned_mne") & d.stage.isin(CLASSES)]
    spectral = [c for c in d.columns if c not in META]
    n1 = pd.concat([pd.read_csv(f, dtype={"subject": str}) for f in sorted((ROOT / "data" / "features_n1").glob("sub-*.csv"))])
    n1["subject"] = n1.subject.str.zfill(2)
    d = d.merge(n1, on=["subject", "session", "t"], how="left")
    return d.sort_values(["subject", "session", "t"]).reset_index(drop=True), spectral


def lopo_proba(d, feats, model):
    """Leave-one-participant-out class probabilities (columns in CLASSES order)."""
    X, y, subj = prepare(d, feats, norm=False, context=True), d.stage.to_numpy(), d.subject.to_numpy()
    P = np.zeros((len(d), len(CLASSES)))
    for s in np.unique(subj):
        tr, te = subj != s, subj == s
        m = make_model(model).fit(X[tr], y[tr])
        P[te] = m.predict_proba(X[te])[:, [list(m.classes_).index(c) for c in CLASSES]]
    return P


def hmm_decode(d, P):
    """Per fold: transitions and priors from training participants' expert sequences; Viterbi per recording."""
    pred = np.empty(len(d), dtype=object)
    for s in d.subject.unique():
        train = d[d.subject != s]
        seqs = [g.stage.tolist() for _, g in train.groupby(["subject", "session"])]
        T, init = transitions(seqs, CLASSES)
        prior = train.stage.value_counts(normalize=True).reindex(CLASSES).to_numpy()
        for _, g in d[d.subject == s].groupby("session"):
            idx = g.index.to_numpy()
            pred[idx] = np.array(CLASSES)[viterbi(P[idx], prior, T, init)]
    return pred


def yasa_pred(d):
    p = d[["yasa_W", "yasa_N1", "yasa_N2", "yasa_N3"]].to_numpy(dtype=float)
    p = np.column_stack([p[:, 0], p[:, 1], p[:, 2] + p[:, 3]])          # drop REM, merge N3 into N2
    pred = np.array(CLASSES, dtype=object)[np.nan_to_num(p, nan=-1).argmax(1)]
    pred[np.isnan(p).any(1)] = None                                     # YASA unavailable for this epoch
    return pred


def per_participant(d, pred, name):
    rows = []
    for s, g in d.assign(pred=pred).groupby("subject"):
        g = g[g.pred.notna()]
        n_n1 = int((g.stage == "N1").sum())
        eligible = n_n1 >= MIN_N1 and (len(g) - n_n1) >= MIN_N1
        f1 = f1_score(g.stage, g.pred, labels=CLASSES, average=None, zero_division=0)
        rows.append({"subject": s, "method": name, "n_epochs": len(g), "n_n1": n_n1, "eligible": eligible,
                     "f1_W": f1[0], "f1_N1": f1[1], "f1_N2": f1[2], "macro_f1": f1.mean(),
                     "kappa": cohen_kappa_score(g.stage, g.pred) if g.stage.nunique() > 1 else np.nan})
    return rows


def holm(pvals):
    order = np.argsort(pvals)
    adj, running = np.empty(len(pvals)), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        adj[i] = min(running, 1.0)
    return adj


def main():
    d, spectral = data()
    print(f"{d.subject.nunique()} participants, {len(d)} epochs: {d.stage.value_counts().to_dict()}", flush=True)
    rows, pooled = [], {}
    for model in ("gbm", "logreg"):
        P = {}
        for name, feats in (("baseline", spectral), ("A", spectral + A_FEATS), ("B", spectral + B_FEATS),
                            ("A+B", spectral + A_FEATS + B_FEATS)):
            P[name] = lopo_proba(d, feats, model)
            pred = np.array(CLASSES, dtype=object)[P[name].argmax(1)]
            rows += per_participant(d, pred, f"{name}/{model}")
            pooled[f"{name}/{model}"] = f1_score(d.stage, pred, labels=CLASSES, average=None).round(3).tolist()
            print(f"{model:6s} {name:8s} pooled F1 W/N1/N2 = {pooled[f'{name}/{model}']}", flush=True)
        for base, name in (("baseline", "C"), ("A+B", "A+B+C")):
            pred = hmm_decode(d, P[base])
            rows += per_participant(d, pred, f"{name}/{model}")
            pooled[f"{name}/{model}"] = f1_score(d.stage, pred, labels=CLASSES, average=None).round(3).tolist()
            print(f"{model:6s} {name:8s} pooled F1 W/N1/N2 = {pooled[f'{name}/{model}']}", flush=True)
    yp = yasa_pred(d)
    rows += per_participant(d, yp, "D/yasa")
    ok = pd.notna(yp)
    pooled["D/yasa"] = f1_score(d.stage[ok], yp[ok].astype(str), labels=CLASSES, average=None).round(3).tolist()
    print(f"YASA pre-trained       pooled F1 W/N1/N2 = {pooled['D/yasa']} ({ok.sum()} epochs)", flush=True)

    per = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    per.to_csv(OUT / "per_participant.csv", index=False)
    el = per[per.eligible]
    wide = el.pivot(index="subject", columns="method", values="f1_N1")
    tests = {}
    for m in ("A", "B", "C"):
        tests[f"primary/{m}_vs_baseline/gbm"] = paired(wide["baseline/gbm"], wide[f"{m}/gbm"])
    adj = holm([tests[k]["wilcoxon_p"] for k in tests])
    for k, a in zip(list(tests), adj):
        tests[k]["holm_p"] = float(a)
    for m, base in (("D/yasa", "baseline/gbm"), ("A/logreg", "baseline/logreg"), ("B/logreg", "baseline/logreg"),
                    ("C/logreg", "baseline/logreg"), ("A+B+C/gbm", "baseline/gbm"), ("A+B+C/logreg", "baseline/logreg")):
        tests[f"secondary/{m}_vs_{base}"] = paired(wide[base], wide[m])
    other = {}
    for metric in ("kappa", "macro_f1", "f1_W", "f1_N2"):
        w = el.pivot(index="subject", columns="method", values=metric)
        other[metric] = {m: float(w[m].median()) for m in w.columns}
    summary = {"n_participants": int(d.subject.nunique()), "n_eligible": int(wide.shape[0]),
               "class_counts": d.stage.value_counts().to_dict(), "pooled_f1_W_N1_N2": pooled,
               "median_f1_N1": {m: float(wide[m].median()) for m in wide.columns},
               "tests_on_f1_N1": tests, "median_other_metrics_eligible": other}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k in ("n_eligible", "median_f1_N1", "tests_on_f1_N1")}, indent=1))


if __name__ == "__main__":
    main()
