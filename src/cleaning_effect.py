"""Measure how each cleaning step changes EEG band power (the classifier's main features).

Usage: python src/cleaning_effect.py data/raw/sub-01/eeg/sub-01_task-sleep_run-1_eeg.vhdr
Prints mean band power across scalp channels for: no artefact removal, gradient removal only,
gradient + heartbeat removal. Same filtering (0.3-40 Hz) and 250 Hz rate in all three.
"""
import sys
from pathlib import Path

import mne
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).parent))
from mr_artifacts import TARGET_SFREQ, r_peaks, remove_bcg, remove_gradient, volume_onsets  # noqa: E402

BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12), "sigma": (12, 16), "beta": (16, 30)}


def to_250(data, info, span):
    r = mne.io.RawArray(data[:, span], info.copy(), verbose="error")
    r.set_channel_types({"ECG": "ecg", "EOG": "eog"})
    r.filter(0.3, 40.0, picks="all", verbose="error")
    r.resample(TARGET_SFREQ, verbose="error")
    return r.get_data()


def band_power(x):
    f, p = signal.welch(x, fs=TARGET_SFREQ, nperseg=int(4 * TARGET_SFREQ), axis=-1)
    return {b: float(p[:, (f >= lo) & (f < hi)].mean() * 1e12) for b, (lo, hi) in BANDS.items()}


def main(vhdr):
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    names = raw.ch_names
    scalp = [i for i, c in enumerate(names) if c not in ("EOG", "ECG")]
    data = raw.get_data()
    onsets = volume_onsets(raw)
    seg_len = int(np.min(np.diff(onsets)))
    span = slice(int(onsets[0]), int(onsets[-1] + seg_len))

    none = to_250(data, raw.info, span)                       # 1) no artefact removal
    remove_gradient(data, onsets)                             # in place
    grad = to_250(data, raw.info, span)                       # 2) gradient only
    full = grad.copy()
    peaks = r_peaks(full[names.index("ECG")], TARGET_SFREQ)
    sub = full[scalp]
    remove_bcg(sub, peaks, TARGET_SFREQ)
    full[scalp] = sub                                         # 3) gradient + heartbeat

    rows = {"no artefact removal": band_power(none[scalp]),
            "scanner artefact removed": band_power(grad[scalp]),
            "scanner + heartbeat removed": band_power(full[scalp])}
    print("band power, mean of 30 scalp channels (uV^2/Hz)")
    print(f"{'':30s}" + "".join(f"{b:>10s}" for b in BANDS))
    for k, v in rows.items():
        print(f"{k:30s}" + "".join(f"{v[b]:10.2f}" for b in BANDS))
    # relative (share of 0.5-30 Hz power) - what a classifier using band ratios sees
    print("share of total 0.5-30 Hz power (%)")
    for k, v in rows.items():
        tot = sum(v.values())
        print(f"{k:30s}" + "".join(f"{100 * v[b] / tot:10.1f}" for b in BANDS))


if __name__ == "__main__":
    main(sys.argv[1])
