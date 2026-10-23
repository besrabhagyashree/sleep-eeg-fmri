"""Study 01b amendment 1 (post hoc): N1 decision threshold chosen by Youden's J, nested within training data.

For each held-out participant: the 28 training participants are split into 4 participant-wise groups to get
out-of-fold N1 probabilities, the Youden-optimal threshold is chosen on those, and the model refitted on all
28 is applied to the held-out participant with that threshold. Compared with argmax for the same model.

Usage: python studies/01b-n1-classification/run_threshold.py
Writes results/threshold_per_participant.csv and results/threshold_summary.json; prints one line per fold.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "studies" / "01-preprocessing-ablation")); sys.path.insert(0, str(ROOT / "src"))
import run_n1 as r  # noqa: E402
from compare_arms import make_model, paired, prepare  # noqa: E402
from methods.threshold import decide, youden_threshold  # noqa: E402

CLASSES = r.CLASSES
OUT = HERE / "results"
RUNS = [("gbm", "baseline"), ("gbm", "A"), ("logreg", "baseline"), ("logreg", "A"), ("logreg", "A+B")]


def proba(model, Xtr, ytr, Xte):
    m = make_model(model).fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, [list(m.classes_).index(c) for c in CLASSES]]


def run(d, feats, model, label):
    X, y, subj = prepare(d, feats, norm=False, context=True), d.stage.to_numpy(), d.subject.to_numpy()
    arg, tuned, thresholds = np.empty(len(d), object), np.empty(len(d), object), {}
    people = np.unique(subj)
    t0 = time.time()
    for i, s in enumerate(people, 1):
        tr, te = subj != s, subj == s
        oof = np.zeros((tr.sum(), len(CLASSES)))                       # out-of-fold probabilities, training people
        for a, b in GroupKFold(4).split(X[tr], y[tr], subj[tr]):
            oof[b] = proba(model, X[tr][a], y[tr][a], X[tr][b])
        t, j = youden_threshold(y[tr] == "N1", oof[:, CLASSES.index("N1")])
        P = proba(model, X[tr], y[tr], X[te])
        arg[te] = np.array(CLASSES, dtype=object)[P.argmax(1)]
        tuned[te] = decide(P, CLASSES, "N1", t)
        thresholds[s] = t
        print(f"{label:16s} participant {s} ({i}/{len(people)}): threshold {t:.2f} (J {j:.2f}) · "
              f"{(time.time() - t0) / i:.0f} s per participant", flush=True)
    return arg, tuned, thresholds


def main():
    d, spectral = r.data()
    sets = {"baseline": spectral, "A": spectral + r.A_FEATS, "A+B": spectral + r.A_FEATS + r.B_FEATS}
    rows, thr, pooled = [], {}, {}
    from sklearn.metrics import f1_score
    for model, fs in RUNS:
        label = f"{fs}/{model}"
        arg, tuned, t = run(d, sets[fs], model, label)
        thr[label] = t
        rows += r.per_participant(d, arg, f"{label}/argmax") + r.per_participant(d, tuned, f"{label}/youden")
        for kind, pred in (("argmax", arg), ("youden", tuned)):
            pooled[f"{label}/{kind}"] = f1_score(d.stage, pred.astype(str), labels=CLASSES, average=None).round(3).tolist()
        print(f"==> {label}: pooled F1 W/N1/N2 argmax {pooled[f'{label}/argmax']} -> Youden {pooled[f'{label}/youden']}", flush=True)
    per = pd.DataFrame(rows)
    per.to_csv(OUT / "threshold_per_participant.csv", index=False)
    el = per[per.eligible]
    wide = el.pivot(index="subject", columns="method", values="f1_N1")
    tests = {f"{m}/{fs}": paired(wide[f"{fs}/{m}/argmax"], wide[f"{fs}/{m}/youden"]) for m, fs in RUNS}
    adj = r.holm([tests["gbm/baseline"]["wilcoxon_p"], tests["gbm/A"]["wilcoxon_p"]])
    tests["gbm/baseline"]["holm_p"], tests["gbm/A"]["holm_p"] = float(adj[0]), float(adj[1])
    other = {metric: el.pivot(index="subject", columns="method", values=metric).median().round(3).to_dict()
             for metric in ("f1_W", "f1_N2", "macro_f1", "kappa")}
    summary = {"n_eligible": int(wide.shape[0]), "pooled_f1_W_N1_N2": pooled,
               "median_threshold": {k: float(np.median(list(v.values()))) for k, v in thr.items()},
               "threshold_range": {k: [min(v.values()), max(v.values())] for k, v in thr.items()},
               "median_f1_N1": wide.median().round(3).to_dict(), "tests_youden_vs_argmax_f1_N1": tests,
               "median_other_metrics": other}
    (OUT / "threshold_summary.json").write_text(json.dumps(summary, indent=2))
    print("ANALYSIS FINISHED")
    print(json.dumps({k: summary[k] for k in ("median_threshold", "tests_youden_vs_argmax_f1_N1")}, indent=1))


if __name__ == "__main__":
    main()
