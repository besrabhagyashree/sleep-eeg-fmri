"""Validate optimal-basis-set (OBS) heartbeat removal against average artefact subtraction (AAS).

Same recording, same gradient correction and filter, same beats; only the heartbeat-removal method
differs. Scored with established measures only:
  INPS (Tong et al., 2001)  heartbeat power removed at the first five heart-rate harmonics (dB)
  physiology                posterior alpha wake / N2 and central sigma N2 / wake (power ratios),
                            using the dataset's expert labels
  power removed             share of 0.5-30 Hz scalp power each method removes

Usage: python studies/01-preprocessing-ablation/validate_obs.py <recording.vhdr> <stage.tsv>
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from scipy import signal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing import quality  # noqa: E402
from preprocessing.mr_artifacts import (TARGET_SFREQ, heart_rate_mne, r_peaks, r_peaks_mne,  # noqa: E402
                                        remove_bcg, remove_bcg_obs, remove_gradient, volume_onsets)


def bandpow(x, names, chans, lo, hi, starts):
    idx = [names.index(c) for c in chans]
    out = []
    for t in starts:
        seg = x[idx, int(t * TARGET_SFREQ): int((t + 30) * TARGET_SFREQ)]
        f, p = signal.welch(seg, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
        out.append(p.mean(0)[(f >= lo) & (f < hi)].mean())
    return float(np.mean(out))


def main(vhdr, tsv):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names = raw.ch_names
    on = volume_onsets(raw); d = raw.get_data(); seg = int(np.min(np.diff(on)))
    remove_gradient(d, on)
    r = mne.io.RawArray(d[:, int(on[0]): int(on[-1] + seg)].copy(), raw.info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error"); r.resample(TARGET_SFREQ, verbose="error")
    x = r.get_data()
    ecg = x[names.index("ECG")]
    scalp = [i for i, c in enumerate(names) if c not in ("ECG", "EOG")]
    scalp_names = [names[i] for i in scalp]
    before = x[scalp].copy()
    ref_hz = heart_rate_mne(ecg, TARGET_SFREQ) / 60

    lab = pd.read_csv(tsv, sep="\t")
    lab = pd.DataFrame({"s": lab.iloc[:, -3], "t": lab.iloc[:, -2], "st": lab.iloc[:, -1].astype(str).str.strip()})
    run = Path(vhdr).name.split("_eeg")[0].split("_", 1)[1]
    lab = lab[lab.s == run]
    W, N2 = lab[lab.st == "W"].t.tolist(), lab[lab.st.isin(["2", "3"])].t.tolist()

    rows = []
    f, pb = signal.welch(before, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
    band = (f >= 0.5) & (f < 30)
    for det_name, det in (("MNE", r_peaks_mne), ("refined", r_peaks)):
        peaks = det(ecg, TARGET_SFREQ)
        for meth, fn in (("AAS (current)", remove_bcg), ("OBS", remove_bcg_obs)):
            s = before.copy(); fn(s, peaks, TARGET_SFREQ)
            _, pa = signal.welch(s, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
            rows.append({"detector": det_name, "method": meth,
                         "INPS dB": round(quality.inps_db(before, s, ref_hz, TARGET_SFREQ), 2),
                         "0.5-30 Hz power removed %": round(100 * (1 - pa[:, band].sum() / pb[:, band].sum()), 1),
                         "alpha W/N2 (O1,O2,Pz)": round(bandpow(s, scalp_names, ["O1", "O2", "Pz"], 8, 12, W) / bandpow(s, scalp_names, ["O1", "O2", "Pz"], 8, 12, N2), 2) if W and N2 else None,
                         "sigma N2/W (C3,C4,Cz)": round(bandpow(s, scalp_names, ["C3", "C4", "Cz"], 12, 16, N2) / bandpow(s, scalp_names, ["C3", "C4", "Cz"], 12, 16, W), 2) if W and N2 else None})
    t = pd.DataFrame(rows)
    print(f"{Path(vhdr).name}: wake {len(W)} epochs, N2 {len(N2)} epochs; heart rate {60 * ref_hz:.1f} bpm")
    print(t.to_string(index=False))
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    t.to_csv(out / f"obs_validation_{Path(vhdr).name.replace('_eeg.vhdr', '')}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
