"""Exploratory: does OBS heartbeat removal (Niazy et al., 2005) change one person's sleep-staging scores?

OBS was not adopted for the main study (validate_obs.py: on sub-01 sleep run 1 it removed far more
0.5-30 Hz power than AAS). This checks the other half of the question: whether that extra removal
helps or hurts staging. Same recordings, epochs, quality flags, features, models and leave-one-recording-out
scoring as score_one_person.py; only the heartbeat-removal method differs.

    obs_mne       scanner artefact removed (AAS) -> filter + 250 Hz -> OBS with MNE's beat detector
    obs_refined   the same with the refined beat detector

Raw recordings are re-downloaded one at a time (the build deletes them) and deleted again after use.
Writes data/features_obs/sub-XX.csv and results/obs_staging_sub-XX.csv.

Usage: python studies/01-preprocessing-ablation/obs_one_person.py 01
"""
import re
import sys
import time
from pathlib import Path

import mne
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from build_dataset import DS, EPOCH_S, download, s3_list, to_250  # noqa: E402
from compare_arms import ARMS, META  # noqa: E402
from features.spectral import epoch_features  # noqa: E402
from preprocessing import quality  # noqa: E402
from preprocessing.mr_artifacts import (TARGET_SFREQ, heart_rate_mne, r_peaks, r_peaks_mne,  # noqa: E402
                                        remove_bcg_obs, remove_gradient, volume_onsets)
from score_one_person import score_arms  # noqa: E402

OBS_ARMS = {"obs_mne": r_peaks_mne, "obs_refined": r_peaks}


def process_run(vhdr, epochs, sub, session):
    """OBS features for the epochs the main build kept for this recording, plus INPS per detector."""
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names = raw.ch_names
    feat_ch = [c for c in names if c != "ECG"]
    fi = [names.index(c) for c in feat_ch]
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    data = raw.get_data()
    onsets = volume_onsets(raw)
    span = slice(int(onsets[0]), int(onsets[-1] + int(np.min(np.diff(onsets)))))
    remove_gradient(data, onsets)
    grad = to_250(data, raw.info, span)
    ecg = grad[names.index("ECG")]
    before = grad[scalp].copy()
    ref_hz = heart_rate_mne(ecg, TARGET_SFREQ) / 60.0
    rows, qc = [], {"subject": sub, "session": session}
    for arm, detector in OBS_ARMS.items():
        x = grad.copy()
        peaks = detector(ecg, TARGET_SFREQ)
        hr = quality.heartbeat_detection_stats(peaks, TARGET_SFREQ)["heart_rate_bpm"]
        if 40 <= hr <= 120:                                     # same plausibility guard as the main build
            s = x[scalp]; remove_bcg_obs(s, peaks, TARGET_SFREQ); x[scalp] = s
            qc[f"inps_db_{arm}"] = quality.inps_db(before, s, ref_hz, TARGET_SFREQ)
        else:
            qc[f"inps_db_{arm}"] = np.nan
        for _, e in epochs.iterrows():
            a = int(round(e.t * TARGET_SFREQ))
            rows.append({"subject": sub, "session": session, "t": e.t, "stage": e.stage, "arm": arm,
                         **epoch_features(x[fi, a: a + int(EPOCH_S * TARGET_SFREQ)], TARGET_SFREQ, feat_ch),
                         "qc_epoch_bad": e.qc_epoch_bad})
    return rows, qc


def build(sub):
    out = ROOT / "data" / "features_obs" / f"sub-{sub}.csv"
    if out.exists():
        print(f"sub-{sub}: OBS features already built", flush=True)
        return pd.read_csv(out, dtype={"subject": str})
    main = pd.read_csv(ROOT / "data" / "features" / f"sub-{sub}.csv", dtype={"subject": str})
    epochs = main[main.arm == "cleaned_mne"][["session", "t", "stage", "qc_epoch_bad"]]
    keys = s3_list(f"{DS}/sub-{sub}/eeg/")
    rows, qcs = [], []
    for base in sorted({re.sub(r"_eeg\.(eeg|vhdr|vmrk)$", "", k) for k in keys if "_eeg." in k}):
        session = re.search(r"(task-\w+_run-\d+)", base).group(1)
        ep = epochs[epochs.session == session]
        if ep.empty:
            continue
        t0 = time.time()
        files = [download(f"{base}_eeg.{ext}") for ext in ("vhdr", "vmrk", "eeg")]
        r, qc = process_run(files[0], ep, sub, session)
        rows += r
        qcs.append(qc)
        print(f"sub-{sub} {session}: {len(ep)} epochs; INPS dB "
              + ", ".join(f"{a} {qc[f'inps_db_{a}']:.2f}" for a in OBS_ARMS) + f"; {time.time() - t0:.0f}s", flush=True)
        files[2].unlink(missing_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(qcs).to_csv(out.with_name(f"qc_sub-{sub}.csv"), index=False)
    d = pd.DataFrame(rows)
    d.to_csv(out, index=False)
    return d


def main(sub):
    obs = build(sub)
    d = pd.concat([pd.read_csv(ROOT / "data" / "features" / f"sub-{sub}.csv", dtype={"subject": str}), obs])
    q = pd.read_csv(ROOT / "data" / "qc" / f"sub-{sub}.csv", dtype={"subject": str})
    d = d[~d.session.isin(q[q.n_bad_channels > 3].session) & ~d.qc_epoch_bad.astype(bool)]   # same exclusions
    arms = ARMS + list(OBS_ARMS)
    res = score_arms(d, arms, [c for c in d.columns if c not in META])
    print("\nkappa (leave-one-recording-out within this person; 0 = chance, 1 = perfect):")
    print(res.pivot_table(index=["task", "model"], columns="arm", values="kappa")[arms].round(3).to_string())
    print("\nbalanced accuracy:")
    print(res.pivot_table(index=["task", "model"], columns="arm", values="bal_acc")[arms].round(3).to_string())
    res.to_csv(HERE / "results" / f"obs_staging_sub-{sub}.csv", index=False)
    print(f"\nsaved results/obs_staging_sub-{sub}.csv")


if __name__ == "__main__":
    main(sys.argv[1])
