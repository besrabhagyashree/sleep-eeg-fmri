"""Study 02: individual alpha before (rest run 1) vs after (rest run 2) a visual-motor adaptation task.

Implements PREREGISTRATION.md: the 29 participants analysed in study 01; AAS-MNE rest recordings; expert-scored
wake epochs not rejected by Autoreject; posterior channels; Corcoran et al. (2018) PAF (primary) and CoG, FOOOF
peak and exponent, alpha power (secondary); equal-epoch sensitivity analysis.

Usage: python studies/02-alpha-before-after/run_alpha.py
Writes results/alpha_per_participant.csv and results/summary.json
"""
import json
import sys
from pathlib import Path

import mne
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "studies" / "01-preprocessing-ablation"))
from build_dataset import load_labels  # noqa: E402
from compare_arms import paired  # noqa: E402
from methods.alpha import alpha_power, concat_segments, corcoran_iaf, fooof_alpha, spectrum  # noqa: E402

DATA = ROOT / "data"
POSTERIOR = ["O1", "O2", "Oz", "P3", "P4", "Pz", "P7", "P8"]
EXCLUDED = {"03", "13", "17", "31"}
RUNS = {"task-rest_run-1": "before", "task-rest_run-2": "after"}
MIN_EPOCHS = 6
OUT = HERE / "results"


def measures(x, sf, names):
    paf, cog = corcoran_iaf(x, sf, names)
    f, p = spectrum(x, sf)
    return {"paf": paf, "cog": cog, "alpha_log_power": alpha_power(f, p), **fooof_alpha(f, p)}


def participant(sub):
    feats = pd.read_csv(DATA / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    kept = feats[feats.arm == "cleaned_mne"][["session", "t", "stage", "qc_epoch_bad"]]
    labels = load_labels(sub)
    rows, data = [], {}
    for session, when in RUNS.items():
        lab = labels[labels.session == session]
        ep = kept[(kept.session == session) & (kept.stage == "W") & ~kept.qc_epoch_bad.astype(bool)]
        path = DATA / "clean" / f"sub-{sub}_{session}_clean-mne_raw.fif"
        row = {"subject": sub, "run": when, "n_wake_epochs": len(ep),
               "wake_share": float((lab.stage == "W").sum() / max(lab.stage.notna().sum(), 1))}
        if len(ep) >= MIN_EPOCHS and path.exists():
            raw = mne.io.read_raw_fif(path, preload=True, verbose="error")
            names = [c for c in POSTERIOR if c in raw.ch_names]
            x_all = raw.get_data(picks=names)
            data[when] = (x_all, raw.info["sfreq"], names, sorted(ep.t))
            row.update(measures(concat_segments(x_all, raw.info["sfreq"], ep.t), raw.info["sfreq"], names))
        rows.append(row)
    if len(data) == 2:                                              # sensitivity: equal epochs per run, earliest first
        n = min(len(v[3]) for v in data.values())
        for row in rows:
            x_all, sf, names, starts = data[row["run"]]
            paf, _ = corcoran_iaf(concat_segments(x_all, sf, starts[:n]), sf, names)
            row.update({"paf_equal_n": paf, "equal_n": n})
    return rows


def main():
    subs = sorted(p.stem.split("-")[1] for p in (DATA / "features").glob("sub-*.csv"))
    rows = []
    for sub in subs:
        if sub in EXCLUDED:
            continue
        rows += participant(sub)
        r1, r2 = rows[-2], rows[-1]
        print(f"sub-{sub}: wake epochs {r1['n_wake_epochs']} / {r2['n_wake_epochs']} · PAF {r1.get('paf')} -> {r2.get('paf')}", flush=True)
    d = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    d.to_csv(OUT / "alpha_per_participant.csv", index=False)
    wide = d.pivot(index="subject", columns="run")
    tests = {}
    for m in ("paf", "cog", "fooof_cf", "fooof_power", "fooof_exponent", "alpha_log_power", "wake_share", "paf_equal_n"):
        if m in d:
            a, b = wide[m]["before"].astype(float), wide[m]["after"].astype(float)
            tests[m] = {**paired(a, b), "median_before": float(a.median()), "median_after": float(b.median())}
    included = int(wide["paf"].dropna().shape[0]) if "paf" in d else 0
    summary = {"n_participants": int(d.subject.nunique()),
               "n_with_enough_wake_both_runs": int((wide["n_wake_epochs"].min(axis=1) >= MIN_EPOCHS).sum()),
               "n_with_paf_both_runs": included, "primary": tests.get("paf"), "all": tests}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: summary[k] for k in ("n_participants", "n_with_enough_wake_both_runs", "n_with_paf_both_runs", "primary")}, indent=1, default=float))


if __name__ == "__main__":
    main()
