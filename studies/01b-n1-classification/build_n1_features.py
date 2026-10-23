"""Study 01b inputs per epoch: alpha occupancy (A), eye-movement features (B) and YASA probabilities (D).

Reads the saved AAS-MNE recordings of study 01 (data/clean/*_clean-mne_raw.fif) and the study 01 epoch list;
writes data/features_n1/sub-XX.csv (one row per epoch). See PREREGISTRATION.md for the definitions.

Usage: python studies/01b-n1-classification/build_n1_features.py
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
from features.events import _pick  # noqa: E402
from features.n1 import alpha_occupancy, eog_components, eye_features  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "features_n1"
EXCLUDED = {"03", "13", "17", "31"}
EPOCH_S = 30
OCCIPITAL, CENTRAL = ["O2", "O1"], ["C4", "C3"]          # AASM recommended derivation first, then backup


def yasa_probs(x, sf, ch_names, bad, n_epochs):
    """YASA SleepStaging probabilities per 30-s epoch (W, N1, N2, N3, R), or None if it cannot run."""
    eeg, eeg_name = _pick(x, ch_names, CENTRAL, bad)
    if not eeg_name or "EOG" not in ch_names:
        return None
    info = mne.create_info([eeg_name[0], "EOG"], sf, ["eeg", "eog"])
    data = np.vstack([eeg[0] * 1e-6, x[ch_names.index("EOG")]])          # back to volts for MNE
    raw = mne.io.RawArray(data, info, verbose="error")
    try:
        p = yasa.SleepStaging(raw, eeg_name=eeg_name[0], eog_name="EOG").predict().proba   # YASA >= 0.7
    except Exception as e:                                                 # e.g. a recording too short
        print(f"    YASA could not run: {type(e).__name__}: {e}", flush=True)
        return None
    names = {"WAKE": "W", "W": "W", "N1": "N1", "N2": "N2", "N3": "N3", "REM": "R", "R": "R"}
    p = p.rename(columns={c: names[str(c).upper()] for c in p.columns})
    return p.reset_index(drop=True).reindex(range(n_epochs))


def participant(sub):
    main = pd.read_csv(DATA / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    epochs = main[main.arm == "cleaned_mne"][["subject", "session", "t"]]
    qc = pd.read_csv(DATA / "qc" / f"sub-{sub}.csv").set_index("session")
    rows = []
    for session, ep in epochs.groupby("session"):
        path = DATA / "clean" / f"sub-{sub}_{session}_clean-mne_raw.fif"
        if not path.exists():
            continue
        raw = mne.io.read_raw_fif(path, preload=True, verbose="error")
        sf, names, x = raw.info["sfreq"], raw.ch_names, raw.get_data()
        bad = [b for b in str(qc.loc[session, "bad_channels"]).split(";") if b and b != "nan"]
        occ, occ_name = _pick(x, names, OCCIPITAL, bad)                   # microvolts; units cancel in ratios
        slow, fast = eog_components(x[names.index("EOG")], sf)
        n_epochs = int(x.shape[1] // (EPOCH_S * sf))
        probs = yasa_probs(x, sf, names, bad, n_epochs)
        for t in ep.t:
            a, b = int(round(t * sf)), int(round((t + EPOCH_S) * sf))
            row = {"subject": sub, "session": session, "t": t, "occipital": occ_name[0] if occ_name else ""}
            row.update(alpha_occupancy(occ[0, a:b], sf) if occ_name else {"alpha_occupancy": np.nan, "alpha_theta_log": np.nan})
            row.update(eye_features(slow[a:b], fast[a:b], sf))
            k = int(round(t / EPOCH_S))
            if probs is not None and k < len(probs) and probs.iloc[k].notna().all():
                row.update({f"yasa_{c}": float(probs.iloc[k][c]) for c in ("W", "N1", "N2", "N3", "R")})
            rows.append(row)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted((DATA / "features").glob("sub-*.csv")):
        sub = f.stem.split("-")[1]
        if sub in EXCLUDED or (OUT / f"sub-{sub}.csv").exists():
            continue
        d = participant(sub)
        d.to_csv(OUT / f"sub-{sub}.csv", index=False)
        print(f"sub-{sub}: {len(d)} epochs; YASA available for {d.filter(like='yasa_W').notna().sum().sum()}", flush=True)


if __name__ == "__main__":
    main()
