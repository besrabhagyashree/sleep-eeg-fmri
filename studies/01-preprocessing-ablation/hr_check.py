"""Exploratory (pre-registration amendment 5): do classification errors follow heart rate?

Heartbeat artefact left after average subtraction sits at the heart rate and its harmonics, and heart
rate falls from wake into sleep. If that residual drives the classifier, then WITHIN a true stage the
model should call low-heart-rate epochs "N2" more often. Run after compare_arms.py --save-predictions.

  heart rate per epoch   60 / median R-R interval of the refined detector's beats in the epoch (ECG of
                         the saved cleaned recording); epochs with fewer than 10 beats are left out
  per person, per arm    Spearman correlation (Spearman, 1904) between heart rate and "predicted N2",
                         computed within true wake and within true N2 epochs, then averaged
  across people          Wilcoxon signed-rank test (Wilcoxon, 1945) of those correlations against 0;
                         a negative median means slower heart -> more often called N2
Task: wake vs N2 (both models). Reported whatever it shows; it does not change which arm is better.

Usage: python studies/01-preprocessing-ablation/hr_check.py
Writes results/hr_check.csv (per person and arm) and results/hr_check.json (summary).
"""
import json
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing.mr_artifacts import r_peaks  # noqa: E402

EPOCH_S, MIN_BEATS, MIN_EPOCHS = 30, 10, 5
CLEAN, OUT = ROOT / "data" / "clean", HERE / "results"


def epoch_heart_rate(peaks, sfreq, starts, epoch_s=EPOCH_S, min_beats=MIN_BEATS):
    """Heart rate (bpm) in each epoch from the median R-R interval; NaN with fewer than min_beats beats."""
    t = np.asarray(peaks) / sfreq
    out = []
    for s in starts:
        b = t[(t >= s) & (t < s + epoch_s)]
        out.append(60.0 / np.median(np.diff(b)) if len(b) >= min_beats else np.nan)
    return np.array(out)


def within_stage_corr(p):
    """Mean over true stages of Spearman(heart rate, predicted N2); NaN if no stage can be scored."""
    rs = []
    for _, g in p.dropna(subset=["hr"]).groupby("stage"):
        y = (g.pred == "N2").astype(float)
        if len(g) >= MIN_EPOCHS and y.nunique() > 1 and g.hr.nunique() > 1:
            rs.append(spearmanr(g.hr, y).statistic)
    return float(np.mean(rs)) if rs else np.nan


def heart_rates(pred):
    rows = []
    for (sub, session), g in pred[["subject", "session", "t"]].drop_duplicates().groupby(["subject", "session"]):
        f = CLEAN / f"sub-{sub}_{session}_clean-mne_raw.fif"
        if not f.exists():
            continue
        raw = mne.io.read_raw_fif(f, preload=True, verbose="error")
        sf = raw.info["sfreq"]
        hr = epoch_heart_rate(r_peaks(raw.get_data(picks="ECG")[0], sf), sf, g.t.to_numpy())
        rows.append(g.assign(hr=hr))
    return pd.concat(rows, ignore_index=True)


def main():
    pred = pd.read_csv(OUT / "predictions.csv", dtype={"subject": str})
    pred = pred[(pred.task == "w_vs_n2") & (pred.model != "chance")]
    pred["subject"] = pred.subject.str.zfill(2)
    pred = pred.merge(heart_rates(pred), on=["subject", "session", "t"], how="left")
    hr_stage = pred.drop_duplicates(["subject", "session", "t"]).pivot_table(index="subject", columns="stage", values="hr")
    rows = [{"subject": s, "arm": a, "model": m, "r_within_stage": within_stage_corr(g), "n_epochs": int(g.hr.notna().sum())}
            for (s, a, m), g in pred.groupby(["subject", "arm", "model"])]
    per = pd.DataFrame(rows)
    per.to_csv(OUT / "hr_check.csv", index=False)
    summary = {"heart_rate_wake_minus_n2_bpm_median": float((hr_stage.W - hr_stage.N2).median()),
               "people_heart_slower_in_n2": int((hr_stage.W > hr_stage.N2).sum()),
               "people_with_both_stages": int(hr_stage[["W", "N2"]].dropna().shape[0]), "tests": {}}
    for (a, m), g in per.groupby(["arm", "model"]):
        r = g.r_within_stage.dropna()
        test = wilcoxon(r) if len(r) >= 6 and np.any(r != 0) else None
        summary["tests"][f"{m}/{a}"] = {"n_people": int(len(r)), "median_r": float(r.median()) if len(r) else None,
                                        "people_negative": int((r < 0).sum()),
                                        "wilcoxon_p": float(test.pvalue) if test else None}
    (OUT / "hr_check.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
