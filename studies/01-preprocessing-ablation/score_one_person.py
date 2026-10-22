"""Within-person preview: score one participant's sleep staging in every arm.

The main analysis (compare_arms.py) scores each person with a model trained on everyone else.
This preview needs only one person: it trains on all but one of their recordings and tests on
the held-out recording, rotating through every recording (leave-one-recording-out). Same
features, models, tasks and quality exclusions as the main analysis; only the training data
differs. Use it to see each arm's behaviour early, not as the study result.

Usage: python studies/01-preprocessing-ablation/score_one_person.py 01
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_arms import ARMS, META, TASKS, make_model, prepare  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main(sub):
    d = pd.read_csv(ROOT / "data" / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    q = pd.read_csv(ROOT / "data" / "qc" / f"sub-{sub}.csv", dtype={"subject": str})
    bad_rec = q[q.n_bad_channels > 3].session.tolist()
    d = d[~d.session.isin(bad_rec) & ~d.qc_epoch_bad.astype(bool)]
    feats = [c for c in d.columns if c not in META]
    n_flag = int(q.n_bad_epochs.sum())
    print(f"participant {sub}: {d[d.arm == 'raw'].shape[0]} epochs kept "
          f"({n_flag} flagged by Autoreject, {int(q.expert_uncertain_or_unscorable.sum())} expert-unscorable, "
          f"{len(bad_rec)} recordings excluded for bad channels)")
    print("stages:", d[d.arm == "raw"].stage.value_counts().to_dict(), "| recordings:", d.session.nunique())

    print("\nheartbeat removal per recording (INPS, dB; higher = more removed) and detector errors:")
    print(q[["session", "heart_rate_bpm_mne", "double_counts_mne", "inps_db_mne", "heart_rate_bpm_refined",
             "double_counts_refined", "inps_db_refined", "n_bad_channels", "bad_channels", "n_bad_epochs"]]
          .round(2).to_string(index=False))

    rows = []
    for task, classes in TASKS.items():
        for model in ("logreg", "gbm"):
            for arm in ARMS:
                a = d[(d.arm == arm) & d.stage.isin(classes)].reset_index(drop=True)
                X, y, runs = prepare(a, feats, norm=False, context=True), a.stage.to_numpy(), a.session.to_numpy()
                pred = np.empty_like(y)
                for r in np.unique(runs):
                    tr, te = runs != r, runs == r
                    if len(set(y[tr])) < len(classes):
                        pred[te] = pd.Series(y[tr]).mode()[0]; continue
                    m = make_model(model); m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
                rows.append({"task": task, "model": model, "arm": arm, "n": len(y),
                             "kappa": cohen_kappa_score(y, pred), "bal_acc": balanced_accuracy_score(y, pred)})
                if task == "3class" and model == "logreg":
                    cm = confusion_matrix(y, pred, labels=classes)
                    print(f"\n{arm} (3-class, logistic regression) confusion, rows = expert {classes}, cols = predicted:")
                    print(pd.DataFrame(cm, index=classes, columns=classes).to_string())
    res = pd.DataFrame(rows)
    kappa = res.pivot_table(index=["task", "model"], columns="arm", values="kappa")[ARMS].round(3)
    bacc = res.pivot_table(index=["task", "model"], columns="arm", values="bal_acc")[ARMS].round(3)
    print("\nscores (leave-one-recording-out within this person; kappa 0 = chance, 1 = perfect):")
    print(kappa.to_string())
    print("\nbalanced accuracy:")
    print(bacc.to_string())

    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / f"preview_sub-{sub}_scores.csv", index=False)
    q.to_csv(out / f"preview_sub-{sub}_quality.csv", index=False)
    print(f"\nsaved results/preview_sub-{sub}_scores.csv and results/preview_sub-{sub}_quality.csv")


if __name__ == "__main__":
    main(sys.argv[1])
