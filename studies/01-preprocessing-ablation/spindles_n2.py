"""Exploratory (pre-registration amendment 9): sleep spindles detected only in expert-scored N2.

YASA spindles_detect with default parameters, on the AASM derivation used for the event features
(C4-M1; C3-M2 when an electrode is PREP-bad), given the expert hypnogram so that only N2/N3 epochs that
Autoreject kept are searched, which is how the detector is intended to be used (Lacourse et al., 2019).
Uses the saved cleaned recordings (AAS-MNE and AAS-refined) of the analysed participants. Descriptive only:
the output uses the expert labels and is never a classifier feature.

Usage: python studies/01-preprocessing-ablation/spindles_n2.py
Writes results/spindles_n2.csv (one row per participant and arm) and prints a summary.
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import yasa

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from build_dataset import CLEAN_DIR, load_labels  # noqa: E402
from features.events import SPINDLE_CH, _pick  # noqa: E402

EXCLUDED = {"03", "13", "17", "31"}                 # rule 5
BAD_RECORDINGS = {("07", "task-sleep_run-1")}       # rule 4
CODE = {"W": 0, "N1": 1, "N2": 2, "N3": 3}
EPOCH_S = 30


def hypnogram(n_samples, sf, epochs):
    """Per-sample stage codes; -1 wherever the epoch is unscored, uncertain or rejected by Autoreject."""
    h = np.full(n_samples, -1, dtype=int)
    for e in epochs.itertuples():
        if e.code >= 0 and not e.bad:
            a = int(round(e.t * sf))
            h[a: min(a + int(EPOCH_S * sf), n_samples)] = e.code
    return h


def run_participant(sub):
    feats = pd.read_csv(ROOT / "data" / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    flags = feats[feats.arm == "cleaned_mne"][["session", "t", "qc_epoch_bad"]]
    lab = load_labels(sub)
    lab = lab.assign(code=lab.stage_raw.map({"W": 0, "1": 1, "2": 2, "3": 3}).fillna(-1).astype(int))
    qc = pd.read_csv(ROOT / "data" / "qc" / f"sub-{sub}.csv").set_index("session")
    rows = []
    for tag, arm in (("mne", "AAS-MNE"), ("refined", "AAS-refined")):
        n2_min, events = 0.0, []
        for session, f in flags.groupby("session"):
            path = CLEAN_DIR / f"sub-{sub}_{session}_clean-{tag}_raw.fif"
            if (sub, session) in BAD_RECORDINGS or not path.exists():
                continue
            ep = f.merge(lab[lab.session == session][["t", "code"]], on="t").rename(columns={"qc_epoch_bad": "bad"})
            raw = mne.io.read_raw_fif(path, preload=True, verbose="error")
            sf = raw.info["sfreq"]
            bad = [b for b in str(qc.loc[session, "bad_channels"]).split(";") if b and b != "nan"]
            x, names = _pick(raw.get_data(), raw.ch_names, SPINDLE_CH, bad)
            if not names:
                continue
            h = hypnogram(x.shape[1], sf, ep)
            if not np.isin(h, (2, 3)).any():                  # no usable N2 in this recording: nothing to search
                continue
            n2_min += np.isin(h, (2, 3)).sum() / sf / 60
            sp = yasa.spindles_detect(x, sf, ch_names=names, hypno=h, include=(2, 3), verbose="error")
            if sp is not None:
                events.append(sp.summary())
        ev = pd.concat(events) if events else pd.DataFrame(columns=["Frequency", "Duration", "Amplitude"])
        rows.append({"subject": sub, "arm": arm, "n2_minutes": round(n2_min, 1), "spindles": len(ev),
                     "density_per_min": len(ev) / n2_min if n2_min else np.nan,
                     "freq_hz": ev.Frequency.mean() if len(ev) else np.nan,
                     "duration_s": ev.Duration.mean() if len(ev) else np.nan,
                     "amplitude_uv": ev.Amplitude.mean() if len(ev) else np.nan})
    return rows


def main():
    subs = sorted(p.stem.split("-")[1] for p in (ROOT / "data" / "features").glob("sub-*.csv"))
    rows = []
    for sub in subs:
        if sub in EXCLUDED:
            continue
        rows += run_participant(sub)
        print(f"sub-{sub}: " + "; ".join(f"{r['arm']} {r['spindles']} spindles in {r['n2_minutes']} min" for r in rows[-2:]), flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "results" / "spindles_n2.csv", index=False)
    s = d[d.n2_minutes >= 2.5]                       # at least 5 usable N2 epochs
    print(f"\nparticipants with >= 2.5 min of usable N2: {s.subject.nunique()}")
    print(s.groupby("arm")[["n2_minutes", "spindles", "density_per_min", "freq_hz", "duration_s", "amplitude_uv"]]
          .median().round(2).to_string())
    print("participants with >= 1 spindle:", s[s.spindles > 0].groupby("arm").subject.nunique().to_dict())


if __name__ == "__main__":
    main()
